"""Task C-09: Logistic Regression baseline for NPL >= 3% risk classification.

Used as a performance comparison baseline against Random Forest.
NOT a production deployment.
See docs/ml-spec.md Section 4.1.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
)

from src.models.feature_engineering_bank import (
    ALL_NUMERIC_FEATURES,
    CAMELS_FEATURES,
    build_bank_features,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# NPL threshold for binary classification (3%)
NPL_THRESHOLD = 0.03


def create_risk_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Create binary risk labels based on npl_ratio threshold.

    Implements the derived feature from docs/data-dictionary.md Section 4:
      risk_label = 1 if npl_ratio >= 0.03, else 0.

    Args:
        df: DataFrame containing the npl_ratio column.

    Returns:
        DataFrame with an added risk_label column.
    """
    df = df.copy()
    df["risk_label"] = (df["npl_ratio"] >= NPL_THRESHOLD).astype(int)

    label_counts = df["risk_label"].value_counts()
    logger.info(
        "Risk label distribution — Healthy (0): %d, High Risk (1): %d",
        label_counts.get(0, 0),
        label_counts.get(1, 0),
    )
    return df


def time_based_split(
    df: pd.DataFrame, target_col: str, feature_cols: list
) -> tuple:
    """Split data using time-based ordering to prevent data leakage.

    Per AGENTS.md Section 4.3, time-based split is mandatory for the
    credit risk classification task.

    Args:
        df: DataFrame sorted by date_key.
        target_col: Name of the target column.
        feature_cols: List of feature column names.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test).
    """
    df = df.sort_values("date_key").reset_index(drop=True)

    # Use approximately the last 20% by time for testing
    split_idx = int(len(df) * 0.8)

    X_train = df.iloc[:split_idx][feature_cols].values
    X_test = df.iloc[split_idx:][feature_cols].values
    y_train = df.iloc[:split_idx][target_col].values
    y_test = df.iloc[split_idx:][target_col].values

    logger.info(
        "Time-based split: %d train, %d test samples.",
        len(X_train),
        len(X_test),
    )
    return X_train, X_test, y_train, y_test


def run_logistic_baseline() -> dict:
    """Train a Logistic Regression baseline and return evaluation metrics.

    Returns:
        Dictionary with 'auc_roc' and classification report details.
    """
    # Load unscaled features — Logistic Regression handles its own scaling
    df, _ = build_bank_features(scale=False)
    df = create_risk_labels(df)

    # Drop rows with any null in feature columns
    feature_cols = [c for c in CAMELS_FEATURES if c in df.columns and c != "npl_ratio"]
    scale_cols = [c for c in ALL_NUMERIC_FEATURES if c in df.columns and c != "npl_ratio"]
    # Use CAMELS features excluding npl_ratio (the target source)
    used_features = [c for c in feature_cols + scale_cols if c != "npl_ratio"]
    # Deduplicate while preserving order
    used_features = list(dict.fromkeys(used_features))

    df_clean = df.dropna(subset=used_features + ["risk_label"])
    logger.info("Clean dataset: %d rows with %d features.", len(df_clean), len(used_features))

    # Time-based split
    X_train, X_test, y_train, y_test = time_based_split(
        df_clean, "risk_label", used_features
    )

    # Train Logistic Regression
    lr = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )
    lr.fit(X_train, y_train)

    # Predict probabilities for AUC-ROC
    y_prob = lr.predict_proba(X_test)[:, 1]
    y_pred = lr.predict(X_test)

    # Evaluate
    auc_roc = roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 0.0
    report = classification_report(y_test, y_pred, output_dict=True)

    logger.info("Logistic Regression Baseline — AUC-ROC: %.4f", auc_roc)
    logger.info(
        "Classification Report:\n%s",
        classification_report(y_test, y_pred),
    )

    results = {
        "auc_roc": auc_roc,
        "classification_report": report,
    }

    return results


if __name__ == "__main__":
    metrics = run_logistic_baseline()
    logger.info(
        "Logistic Regression baseline complete. AUC-ROC: %.4f",
        metrics["auc_roc"],
    )
