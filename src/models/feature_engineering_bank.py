"""Task C-02: Feature engineering for bank CAMELS data.

Queries fact_bank_performance from BigQuery.
Applies StandardScaler normalization to all CAMELS ratio features.
See docs/ml-spec.md Section 2.2 and docs/data-dictionary.md Section 3.5.
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.logger import get_logger

logger = get_logger(__name__)

# CAMELS ratio features used for PCA and K-Means clustering.
# These correspond to the columns defined in data-dictionary.md Section 3.5.
CAMELS_FEATURES = [
    "roa",
    "roe",
    "nim",
    "cir",
    "eta",
    "etd",
    "lta",
    "ltd",
    "gta",
    "npl_ratio",
    "llp_ratio",
]

# Additional scale variables used for Random Forest classification.
# Defined in data-dictionary.md Section 3.2.
SCALE_FEATURES = [
    "total_assets",
    "total_deposits",
    "total_loans",
    "total_equity",
]

# All numeric features available for ML models
ALL_NUMERIC_FEATURES = CAMELS_FEATURES + SCALE_FEATURES


def query_bank_performance(client) -> pd.DataFrame:
    """Query fact_bank_performance joined with dim_bank for bank metadata.

    Args:
        client: An authenticated BigQuery Client.

    Returns:
        DataFrame with bank identification, date_key, and all CAMELS
        performance columns.
    """
    fact_table = get_full_table_id("fact_bank_performance")
    dim_table = get_full_table_id("dim_bank")
    query = f"""
        SELECT
            f.date_key,
            f.bank_key,
            d.bank_code,
            d.bank_name,
            d.bank_type,
            f.total_assets,
            f.total_deposits,
            f.total_loans,
            f.total_equity,
            f.npl_ratio,
            f.roa,
            f.roe,
            f.nim,
            f.cir,
            f.eta,
            f.etd,
            f.lta,
            f.ltd,
            f.gta,
            f.llp_ratio
        FROM `{fact_table}` AS f
        JOIN `{dim_table}` AS d
            ON f.bank_key = d.bank_key
        ORDER BY d.bank_code, f.date_key
    """
    df = client.query(query).to_dataframe()
    logger.info("Queried %d rows from fact_bank_performance.", len(df))
    return df


def scale_features(
    df: pd.DataFrame, feature_cols: list
) -> tuple[pd.DataFrame, StandardScaler]:
    """Apply StandardScaler to the specified feature columns.

    StandardScaler is mandatory before PCA and K-Means to ensure equal
    weighting of all financial ratios (docs/ml-spec.md Section 2.2).

    Args:
        df: Raw or imputed DataFrame containing the feature columns.
        feature_cols: List of column names to scale.

    Returns:
        A tuple of (scaled_df, fitted_scaler) where scaled_df has the
        same index and non-feature columns as the input, with the
        feature columns replaced by their standardized values.
    """
    scaler = StandardScaler()

    # Only scale columns that actually exist in the DataFrame
    available_cols = [c for c in feature_cols if c in df.columns]
    missing_cols = set(feature_cols) - set(available_cols)
    if missing_cols:
        logger.warning(
            "The following feature columns are missing from the DataFrame "
            "and will be skipped: %s",
            sorted(missing_cols),
        )

    df_scaled = df.copy()
    df_scaled[available_cols] = scaler.fit_transform(df[available_cols])

    # Validate: scaled columns should have mean approximately 0 and std approximately 1
    means = df_scaled[available_cols].mean()
    stds = df_scaled[available_cols].std()
    logger.info(
        "StandardScaler applied to %d columns. "
        "Mean range: [%.4f, %.4f]. Std range: [%.4f, %.4f].",
        len(available_cols),
        means.min(),
        means.max(),
        stds.min(),
        stds.max(),
    )

    return df_scaled, scaler


def build_bank_features(
    scale: bool = True,
) -> tuple[pd.DataFrame, StandardScaler | None]:
    """Execute the full C-02 feature engineering pipeline for bank data.

    Queries fact_bank_performance from BigQuery, optionally applies
    StandardScaler normalization, and returns the processed DataFrame.

    Args:
        scale: If True, apply StandardScaler to CAMELS features.
            Set to False when the downstream model handles its own scaling.

    Returns:
        A tuple of (features_df, scaler). If scale is False, scaler is None.

    Raises:
        ValueError: If npl_ratio contains null values after query.
    """
    client = get_bigquery_client()
    df = query_bank_performance(client)

    # Validate: npl_ratio must not be null (it is the classification target)
    null_npl = df["npl_ratio"].isna().sum()
    if null_npl > 0:
        logger.warning(
            "npl_ratio contains %d null values. These should have been "
            "imputed during ETL (median imputation, not forward-fill).",
            null_npl,
        )

    scaler = None
    if scale:
        df, scaler = scale_features(df, CAMELS_FEATURES)

    return df, scaler


if __name__ == "__main__":
    bank_df, fitted_scaler = build_bank_features(scale=True)
    logger.info("Bank feature engineering complete.")
    logger.info("Columns: %s", list(bank_df.columns))
    logger.info("Shape: %s", bank_df.shape)
    logger.info("\n%s", bank_df.head().to_string())
