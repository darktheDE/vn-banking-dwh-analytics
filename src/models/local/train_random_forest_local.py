"""
Random Forest Local — Phân loại rủi ro tín dụng ngân hàng (NPL >= 3%).

Đọc dữ liệu từ data/ML_data/banks_camels_46.csv (667 quan sát, 45 ngân hàng).
Tạo nhãn rủi ro (1 nếu npl_ratio >= 0.03, ngược lại 0).
Train/Test split theo thời gian (time-based) để tránh data leakage.
Acceptance: AUC-ROC > 0.80, Recall (High Risk) >= 85%.
Xuất kết quả ra data/ML_data/rf_predictions_local.csv và rf_feature_importance_local.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, recall_score, roc_auc_score, roc_curve, f1_score,
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
ML_DATA_DIR = os.path.join(BASE_DIR, "data", "data_ml")
FIGURES_DIR = os.path.join(ML_DATA_DIR, "figures")

# Acceptance thresholds (theo AGENTS.md Section 4.3)
AUC_ROC_THRESHOLD = 0.80
RECALL_THRESHOLD = 0.85
NPL_THRESHOLD = 0.03
RANDOM_STATE = 42

# Feature columns (loại bỏ npl_ratio vì đó là target)
FEATURE_COLUMNS = [
    "llp_ratio", "roa", "roe", "nim", "cir",
    "eta", "etd", "lta", "ltd", "gta",
    "total_assets", "total_deposits", "total_loans", "total_equity",
]


def train_random_forest():
    """Pipeline chính: Load data -> Label -> Split -> Train RF -> Evaluate -> Export."""
    data_path = os.path.join(ML_DATA_DIR, "banks_camels_46.csv")
    if not os.path.exists(data_path):
        logger.error("Data not found at %s. Run data_loader.py first.", data_path)
        return None

    df = pd.read_csv(data_path)
    logger.info("Loaded %d rows, %d banks.", len(df), df["bank_key"].nunique())

    # --- Tạo nhãn rủi ro ---
    df["risk_label"] = (df["npl_ratio"] >= NPL_THRESHOLD).astype(int)
    label_dist = df["risk_label"].value_counts()
    logger.info("Risk label distribution: 0 (Healthy)=%d, 1 (High Risk)=%d",
                label_dist.get(0, 0), label_dist.get(1, 0))

    # --- Lọc feature columns có sẵn ---
    available_features = [c for c in FEATURE_COLUMNS if c in df.columns]
    logger.info("Using %d features: %s", len(available_features), available_features)

    # Drop rows with null in features or target
    df_clean = df.dropna(subset=available_features + ["risk_label"]).copy()
    logger.info("Clean dataset: %d rows after dropping nulls.", len(df_clean))

    # --- Time-based split (bắt buộc theo AGENTS.md) ---
    df_clean = df_clean.sort_values("date_key").reset_index(drop=True)
    split_idx = int(len(df_clean) * 0.8)

    X_train = df_clean.iloc[:split_idx][available_features]
    X_test = df_clean.iloc[split_idx:][available_features]
    y_train = df_clean.iloc[:split_idx]["risk_label"]
    y_test = df_clean.iloc[split_idx:]["risk_label"]

    logger.info("Train: %d rows (High Risk: %d), Test: %d rows (High Risk: %d)",
                len(X_train), y_train.sum(), len(X_test), y_test.sum())

    # --- Train Random Forest ---
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    logger.info("Random Forest trained with %d estimators.", rf.n_estimators)

    # --- Evaluate ---
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1]

    # AUC-ROC
    if len(np.unique(y_test)) > 1:
        auc_roc = roc_auc_score(y_test, y_prob)
    else:
        auc_roc = 0.0
        logger.warning("Only one class in test set. AUC-ROC set to 0.")

    # Recall for High Risk class
    recall_hr = recall_score(y_test, y_pred, pos_label=1, zero_division=0)
    f1 = f1_score(y_test, y_pred, pos_label=1, zero_division=0)

    logger.info("Random Forest — AUC-ROC: %.4f (threshold: > %.2f)", auc_roc, AUC_ROC_THRESHOLD)
    logger.info("Random Forest — Recall (High Risk): %.4f (threshold: >= %.2f)", recall_hr, RECALL_THRESHOLD)
    logger.info("Random Forest — F1-Score (High Risk): %.4f", f1)

    # Classification Report
    report_str = classification_report(y_test, y_pred, zero_division=0)
    logger.info("Classification Report:\n%s", report_str)

    # Acceptance check
    if auc_roc > AUC_ROC_THRESHOLD:
        logger.info("ACCEPTANCE PASSED: AUC-ROC %.4f > %.2f", auc_roc, AUC_ROC_THRESHOLD)
    else:
        logger.warning("ACCEPTANCE WARNING: AUC-ROC %.4f does NOT exceed %.2f.", auc_roc, AUC_ROC_THRESHOLD)

    if recall_hr >= RECALL_THRESHOLD:
        logger.info("ACCEPTANCE PASSED: Recall (High Risk) %.4f >= %.2f", recall_hr, RECALL_THRESHOLD)
    else:
        logger.warning("ACCEPTANCE WARNING: Recall (High Risk) %.4f is BELOW %.2f.", recall_hr, RECALL_THRESHOLD)

    # --- Feature Importance ---
    importance_df = pd.DataFrame({
        "feature": available_features,
        "importance": rf.feature_importances_,
    }).sort_values("importance", ascending=False)

    logger.info("Feature Importance ranking:")
    for _, row in importance_df.iterrows():
        logger.info("  %s: %.4f", row["feature"], row["importance"])

    # Plot Feature Importance
    os.makedirs(FIGURES_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, max(6, len(importance_df) * 0.4)))
    ax.barh(importance_df["feature"], importance_df["importance"],
            color="steelblue", edgecolor="navy")
    ax.set_xlabel("Feature Importance")
    ax.set_title("Random Forest — Feature Importance (Credit Risk)")
    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "rf_feature_importance.png"), dpi=150)
    plt.close(fig)

    # Plot ROC Curve
    if auc_roc > 0:
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(fpr, tpr, color="darkorange", linewidth=2,
                label=f"ROC Curve (AUC = {auc_roc:.4f})")
        ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1)
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("Random Forest — ROC Curve")
        ax.legend(loc="lower right")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGURES_DIR, "rf_roc_curve.png"), dpi=150)
        plt.close(fig)

    # --- Export predictions ---
    df_test_output = df_clean.iloc[split_idx:].copy()
    df_test_output["predicted_risk_label"] = y_pred
    df_test_output["risk_probability"] = y_prob

    out_cols = ["bank_key", "date_key", "year", "npl_ratio", "risk_label",
                "predicted_risk_label", "risk_probability"]
    if "bank_code" in df_test_output.columns:
        out_cols.insert(1, "bank_code")

    out_path = os.path.join(ML_DATA_DIR, "rf_predictions_local.csv")
    df_test_output[out_cols].to_csv(out_path, index=False)
    logger.info("Saved RF predictions to %s", out_path)

    imp_path = os.path.join(ML_DATA_DIR, "rf_feature_importance_local.csv")
    importance_df.to_csv(imp_path, index=False)
    logger.info("Saved feature importance to %s", imp_path)

    return {
        "auc_roc": auc_roc,
        "recall_high_risk": recall_hr,
        "f1_score": f1,
        "n_test": len(y_test),
        "n_high_risk_test": int(y_test.sum()),
    }


if __name__ == "__main__":
    results = train_random_forest()
    if results:
        logger.info("Random Forest pipeline complete.")
        logger.info("AUC-ROC: %.4f, Recall: %.4f, F1: %.4f",
                     results["auc_roc"], results["recall_high_risk"], results["f1_score"])
