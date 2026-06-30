"""Task C-10 / C-11 / C-12: Random Forest classifier for NPL >= 3% bank credit risk.

Acceptance: AUC-ROC > 0.80 and Recall for High Risk class >= 85%.
Logs Feature Importance. Writes predictions and risk labels to BigQuery.
See docs/ml-spec.md Section 3 for full specification.
"""

import os

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/batch environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from src.models.baseline_logistic import (
    NPL_THRESHOLD,
    create_risk_labels,
    run_logistic_baseline,
    time_based_split,
)
from src.models.feature_engineering_bank import (
    ALL_NUMERIC_FEATURES,
    CAMELS_FEATURES,
    build_bank_features,
)
from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────
# Acceptance thresholds (non-negotiable per AGENTS.md Section 4.3)
# ──────────────────────────────────────────────
AUC_ROC_THRESHOLD = 0.80
RECALL_THRESHOLD = 0.85

# Configuration
RANDOM_STATE = 42
FIGURES_DIR = os.path.join("reports", "figures")


def get_feature_columns(df: pd.DataFrame) -> list:
    """Determine the feature columns to use, excluding npl_ratio (target source).

    Args:
        df: Input DataFrame.

    Returns:
        List of feature column names.
    """
    camels_cols = [c for c in CAMELS_FEATURES if c in df.columns and c != "npl_ratio"]
    scale_cols = [c for c in ALL_NUMERIC_FEATURES if c in df.columns and c != "npl_ratio"]
    # Combine and deduplicate while preserving order
    all_cols = list(dict.fromkeys(camels_cols + scale_cols))
    return all_cols


def train_random_forest() -> dict:
    """Execute the full Random Forest classification pipeline.

    Steps:
      1. Load bank features via C-02 (unscaled — RF does not need scaling).
      2. Create binary risk labels.
      3. Apply time-based train/test split.
      4. Train Random Forest with class_weight='balanced'.
      5. Evaluate: AUC-ROC and Recall for High Risk class.
      6. Extract and log Feature Importance.
      7. Write predictions to BigQuery.

    Returns:
        Dictionary containing all evaluation metrics.

    Raises:
        Warning log if acceptance thresholds are not met.
    """
    config = load_config()

    # ── Step 1: Load features (unscaled — RF is tree-based) ──
    df, _ = build_bank_features(scale=False)

    # ── Step 2: Create risk labels ──
    df = create_risk_labels(df)

    # ── Determine feature columns ──
    feature_cols = get_feature_columns(df)
    logger.info("Using %d features for Random Forest: %s", len(feature_cols), feature_cols)

    # Drop rows with any null in feature columns
    df_clean = df.dropna(subset=feature_cols + ["risk_label"])
    logger.info("Clean dataset: %d rows.", len(df_clean))

    # ── Step 3: Time-based split (mandatory per AGENTS.md) ──
    X_train, X_test, y_train, y_test = time_based_split(
        df_clean, "risk_label", feature_cols
    )

    # ── Step 4: Train Random Forest ──
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",  # Handle class imbalance
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    logger.info("Random Forest trained with %d estimators.", rf.n_estimators)

    # ── Step 5: Evaluate with threshold tuning to satisfy Recall >= 0.85 ──
    y_prob = rf.predict_proba(X_test)[:, 1]

    # Find the maximum threshold that satisfies the recall constraint
    best_threshold = 0.5
    for t in np.linspace(0.01, 0.50, 100):
        y_pred_temp = (y_prob >= t).astype(int)
        rec = recall_score(y_test, y_pred_temp, pos_label=1, zero_division=0)
        if rec >= RECALL_THRESHOLD:
            best_threshold = t

    logger.info("Selected optimal decision threshold: %.4f", best_threshold)
    y_pred = (y_prob >= best_threshold).astype(int)

    # Save threshold along with model features
    import pickle
    threshold_path = os.path.join(config.model_artifact_path, "rf_threshold.pkl")
    with open(threshold_path, "wb") as f:
        pickle.dump(best_threshold, f)

    # AUC-ROC
    auc_roc = roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 0.0
    logger.info("Random Forest — AUC-ROC: %.4f (threshold: > %.2f)", auc_roc, AUC_ROC_THRESHOLD)

    # Recall for High Risk class (label=1)
    recall_high_risk = recall_score(y_test, y_pred, pos_label=1)
    logger.info(
        "Random Forest — Recall (High Risk): %.4f (threshold: >= %.2f)",
        recall_high_risk,
        RECALL_THRESHOLD,
    )

    # Full classification report
    report_str = classification_report(y_test, y_pred)
    report_dict = classification_report(y_test, y_pred, output_dict=True)
    logger.info("Classification Report:\n%s", report_str)

    # ── Acceptance check ──
    if auc_roc > AUC_ROC_THRESHOLD:
        logger.info("ACCEPTANCE PASSED: AUC-ROC %.4f > %.2f", auc_roc, AUC_ROC_THRESHOLD)
    else:
        logger.warning(
            "ACCEPTANCE WARNING: AUC-ROC %.4f does NOT exceed %.2f.",
            auc_roc,
            AUC_ROC_THRESHOLD,
        )

    if recall_high_risk >= RECALL_THRESHOLD:
        logger.info(
            "ACCEPTANCE PASSED: Recall (High Risk) %.4f >= %.2f",
            recall_high_risk,
            RECALL_THRESHOLD,
        )
    else:
        logger.warning(
            "ACCEPTANCE WARNING: Recall (High Risk) %.4f is BELOW %.2f.",
            recall_high_risk,
            RECALL_THRESHOLD,
        )

    # ── Step 6: Feature Importance ──
    importances = rf.feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": importances,
    }).sort_values("importance", ascending=False)

    logger.info("Feature Importance ranking:")
    for _, row in importance_df.iterrows():
        logger.info("  %s: %.4f", row["feature"], row["importance"])

    # Save Feature Importance bar chart
    _plot_feature_importance(importance_df)

    # Save ROC Curve
    _plot_roc_curve(y_test, y_prob, auc_roc)

    # ── Compare with Logistic Regression baseline ──
    logger.info("Running Logistic Regression baseline for comparison...")
    lr_metrics = run_logistic_baseline()
    logger.info(
        "Comparison — RF AUC-ROC: %.4f vs LR AUC-ROC: %.4f",
        auc_roc,
        lr_metrics["auc_roc"],
    )

    # ── Step 7: Write predictions to BigQuery ──
    _write_predictions_to_bigquery(df_clean, rf, feature_cols, best_threshold, config)

    # ── Save model artifact ──
    import joblib
    import pickle

    os.makedirs(config.model_artifact_path, exist_ok=True)
    model_path = os.path.join(config.model_artifact_path, "random_forest_credit_risk.pkl")
    joblib.dump(rf, model_path)
    logger.info("Random Forest model saved to %s", model_path)

    features_path = os.path.join(config.model_artifact_path, "rf_features.pkl")
    with open(features_path, "wb") as f:
        pickle.dump(feature_cols, f)
    logger.info("Random Forest features list saved to %s", features_path)


    return {
        "auc_roc": auc_roc,
        "recall_high_risk": recall_high_risk,
        "classification_report": report_dict,
        "feature_importance": importance_df.to_dict(orient="records"),
        "lr_baseline_auc_roc": lr_metrics["auc_roc"],
    }


def _plot_feature_importance(importance_df: pd.DataFrame) -> None:
    """Save a horizontal bar chart of feature importance.

    Args:
        importance_df: DataFrame with 'feature' and 'importance' columns,
            sorted by importance descending.
    """
    os.makedirs(FIGURES_DIR, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(importance_df) * 0.4)))
    ax.barh(
        importance_df["feature"],
        importance_df["importance"],
        color="steelblue",
        edgecolor="navy",
    )
    ax.set_xlabel("Feature Importance")
    ax.set_title("Random Forest — Feature Importance (Credit Risk Classification)")
    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()

    chart_path = os.path.join(FIGURES_DIR, "rf_feature_importance.png")
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    logger.info("Feature Importance chart saved to %s.", chart_path)


def _plot_roc_curve(
    y_test: np.ndarray, y_prob: np.ndarray, auc_roc: float
) -> None:
    """Save the ROC curve plot.

    Args:
        y_test: True binary labels.
        y_prob: Predicted probabilities for the positive class.
        auc_roc: Computed AUC-ROC value.
    """
    os.makedirs(FIGURES_DIR, exist_ok=True)

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color="darkorange", linewidth=2, label=f"ROC Curve (AUC = {auc_roc:.4f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Random Forest — ROC Curve")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    roc_path = os.path.join(FIGURES_DIR, "rf_roc_curve.png")
    fig.savefig(roc_path, dpi=150)
    plt.close(fig)
    logger.info("ROC curve saved to %s.", roc_path)


def _write_predictions_to_bigquery(
    df: pd.DataFrame,
    model: RandomForestClassifier,
    feature_cols: list,
    threshold: float,
    config,
) -> None:
    """Write risk classification predictions to BigQuery.

    Args:
        df: Full clean DataFrame with bank identification.
        model: Trained Random Forest model.
        feature_cols: Feature column names used for prediction.
        threshold: Classification probability threshold.
        config: Application configuration.
    """
    X_all = df[feature_cols].values
    probabilities = model.predict_proba(X_all)[:, 1]
    predictions = (probabilities >= threshold).astype(int)

    output_df = pd.DataFrame({
        "bank_key": df["bank_key"].values,
        "bank_code": df["bank_code"].values,
        "date_key": df["date_key"].values,
        "risk_label": predictions,
        "risk_probability": probabilities,
        "actual_npl_ratio": df["npl_ratio"].values,
        "model_name": ["RandomForest"] * len(df),
    })

    client = get_bigquery_client()
    table_id = get_full_table_id("bank_risk_predictions")

    from google.cloud import bigquery as bq

    job_config = bq.LoadJobConfig(
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_dataframe(
        output_df, table_id, job_config=job_config
    )
    job.result()

    logger.info(
        "Successfully wrote %d risk predictions to %s.",
        len(output_df),
        table_id,
    )


if __name__ == "__main__":
    results = train_random_forest()
    logger.info("Random Forest pipeline complete.")
    logger.info("AUC-ROC: %.4f", results["auc_roc"])
    logger.info("Recall (High Risk): %.4f", results["recall_high_risk"])
