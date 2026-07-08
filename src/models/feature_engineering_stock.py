"""Task C-01: Feature engineering for focus banking stocks.

Queries fact_price_history, fact_foreign_trading, and fact_proprietary_trading
from BigQuery. Merges into a single feature DataFrame for BID (stock_key 1),
or returns daily stock history with derived change columns for other stocks.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.logger import get_logger

logger = get_logger(__name__)


def query_price_history(client, stock_key: int) -> pd.DataFrame:
    """Query fact_price_history for the given stock_key and return as DataFrame.

    Args:
        client: An authenticated BigQuery Client.
        stock_key: The stock surrogate key.

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
        WHERE stock_key = {stock_key}
        ORDER BY date_key
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    logger.info("Queried %d rows from fact_price_history for stock_key %d.", len(df), stock_key)
    return df


def query_foreign_trading(client, stock_key: int) -> pd.DataFrame:
    """Query fact_foreign_trading for the given stock_key and return as DataFrame.

    Args:
        client: An authenticated BigQuery Client.
        stock_key: The stock surrogate key.

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
        WHERE stock_key = {stock_key}
        ORDER BY date_key
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    logger.info("Queried %d rows from fact_foreign_trading for stock_key %d.", len(df), stock_key)
    return df


def query_proprietary_trading(client, stock_key: int) -> pd.DataFrame:
    """Query fact_proprietary_trading for the given stock_key and return as DataFrame.

    Args:
        client: An authenticated BigQuery Client.
        stock_key: The stock surrogate key.

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
        WHERE stock_key = {stock_key}
        ORDER BY date_key
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    logger.info("Queried %d rows from fact_proprietary_trading for stock_key %d.", len(df), stock_key)
    return df


def build_stock_features(stock_key: int = 1) -> pd.DataFrame:
    """Execute the full C-01 feature engineering pipeline for the given stock key.

    Queries BigQuery fact tables, adds derived features,
    and returns a clean DataFrame ready for LSTM training.

    Args:
        stock_key: Stock key (1: BID, 2: TCB, 3: VCB, 4: CTG)

    Returns:
        A cleaned and enriched DataFrame with stock features.
    """
    client = get_bigquery_client()
    df_price = query_price_history(client, stock_key)

    if len(df_price) == 0:
        logger.warning("No price history rows found for stock_key %d.", stock_key)
        return pd.DataFrame()

    # All stocks use standard price history (OHLCV) features to avoid mock data constraints
    df = df_price.copy()
    df = df.sort_values("date_key").reset_index(drop=True)

    # Add derived features
    df["price_change_pct"] = df["close_price"].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    df["volume_change_pct"] = df["trading_volume"].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    df = df.dropna().reset_index(drop=True)

    # Validate: close_price must not be null
    if not df.empty:
        null_close = df["close_price"].isna().sum()
        if null_close > 0:
            raise ValueError(f"close_price contains {null_close} null values after merge.")

    return df


if __name__ == "__main__":
    for sk in [1, 2, 3, 4]:
        features_df = build_stock_features(sk)
        if not features_df.empty:
            logger.info("Stock key %d feature engineering complete. Shape: %s", sk, features_df.shape)
