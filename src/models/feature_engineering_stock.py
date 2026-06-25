"""Task C-01: Feature engineering for BID stock data.

Queries fact_price_history, fact_foreign_trading, fact_proprietary_trading
from BigQuery. Merges into a single feature DataFrame for the BID ticker.
Adds derived features: price_change_pct, foreign_net_lag_1, prop_net_lag_1.

See docs/data-dictionary.md Section 4 and docs/ml-spec.md Section 1.2.
"""

import pandas as pd

from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.logger import get_logger

logger = get_logger(__name__)

# BID stock_key is 1 as defined in dim_stock (see docs/star-schema.md 2.2)
BID_STOCK_KEY = 1


def query_price_history(client) -> pd.DataFrame:
    """Query fact_price_history for BID and return as DataFrame.

    Args:
        client: An authenticated BigQuery Client.

    Returns:
        DataFrame with columns: date_key, open_price, high_price,
        low_price, close_price, trading_volume.
    """
    table_id = get_full_table_id("fact_price_history")
    query = f"""
        SELECT
            date_key,
            open_price,
            high_price,
            low_price,
            close_price,
            trading_volume
        FROM `{table_id}`
        WHERE stock_key = {BID_STOCK_KEY}
        ORDER BY date_key
    """
    df = client.query(query).to_dataframe()
    logger.info("Queried %d rows from fact_price_history.", len(df))
    return df


def query_foreign_trading(client) -> pd.DataFrame:
    """Query fact_foreign_trading for BID and return as DataFrame.

    Args:
        client: An authenticated BigQuery Client.

    Returns:
        DataFrame with columns: date_key, foreign_buy_volume,
        foreign_sell_volume, foreign_net_volume, foreign_net_value.
    """
    table_id = get_full_table_id("fact_foreign_trading")
    query = f"""
        SELECT
            date_key,
            foreign_buy_volume,
            foreign_sell_volume,
            foreign_net_volume,
            foreign_net_value
        FROM `{table_id}`
        WHERE stock_key = {BID_STOCK_KEY}
        ORDER BY date_key
    """
    df = client.query(query).to_dataframe()
    logger.info("Queried %d rows from fact_foreign_trading.", len(df))
    return df


def query_proprietary_trading(client) -> pd.DataFrame:
    """Query fact_proprietary_trading for BID and return as DataFrame.

    Args:
        client: An authenticated BigQuery Client.

    Returns:
        DataFrame with columns: date_key, prop_buy_volume,
        prop_sell_volume, prop_net_volume, prop_net_value.
    """
    table_id = get_full_table_id("fact_proprietary_trading")
    query = f"""
        SELECT
            date_key,
            prop_buy_volume,
            prop_sell_volume,
            prop_net_volume,
            prop_net_value
        FROM `{table_id}`
        WHERE stock_key = {BID_STOCK_KEY}
        ORDER BY date_key
    """
    df = client.query(query).to_dataframe()
    logger.info("Queried %d rows from fact_proprietary_trading.", len(df))
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived feature columns for LSTM training.

    Implements the derived features specified in docs/data-dictionary.md
    Section 4:
      - price_change_pct: daily percentage change of close_price.
      - foreign_net_lag_1: foreign_net_volume shifted by 1 day.
      - prop_net_lag_1: prop_net_volume shifted by 1 day.

    Args:
        df: Merged feature DataFrame sorted by date_key.

    Returns:
        DataFrame with additional derived columns.
    """
    df = df.copy()

    # Daily percentage change of close_price
    df["price_change_pct"] = df["close_price"].pct_change()

    # Lagged foreign flow signal (1 trading day lag)
    df["foreign_net_lag_1"] = df["foreign_net_volume"].shift(1)

    # Lagged proprietary flow signal (1 trading day lag)
    df["prop_net_lag_1"] = df["prop_net_volume"].shift(1)

    # Drop the first row which will have NaN from shift/pct_change
    df = df.dropna().reset_index(drop=True)

    logger.info(
        "Added derived features. Final feature DataFrame has %d rows and %d columns.",
        len(df),
        len(df.columns),
    )
    return df


def build_stock_features() -> pd.DataFrame:
    """Execute the full C-01 feature engineering pipeline for BID stock.

    Queries three fact tables from BigQuery, merges them on date_key,
    adds derived features, and returns a clean DataFrame ready for
    LSTM training.

    Returns:
        A merged and enriched DataFrame with all stock features.

    Raises:
        ValueError: If the merged DataFrame contains null close_price values.
    """
    client = get_bigquery_client()

    # Query the three source tables
    df_price = query_price_history(client)
    df_foreign = query_foreign_trading(client)
    df_prop = query_proprietary_trading(client)

    # Merge on date_key using inner join to keep only valid trading days
    df = df_price.merge(df_foreign, on="date_key", how="inner")
    df = df.merge(df_prop, on="date_key", how="inner")

    logger.info("Merged DataFrame has %d rows after inner join.", len(df))

    # Validate: close_price must not be null (DQ-03 from data-dictionary.md)
    null_close = df["close_price"].isna().sum()
    if null_close > 0:
        raise ValueError(
            "close_price contains %d null values after merge. "
            "Rows with null close_price must be rejected per ETL spec." % null_close
        )

    # Sort by date for time-series consistency
    df = df.sort_values("date_key").reset_index(drop=True)

    # Add derived features
    df = add_derived_features(df)

    return df


if __name__ == "__main__":
    features_df = build_stock_features()
    logger.info("Stock feature engineering complete.")
    logger.info("Columns: %s", list(features_df.columns))
    logger.info("Shape: %s", features_df.shape)
    logger.info("\n%s", features_df.head().to_string())
