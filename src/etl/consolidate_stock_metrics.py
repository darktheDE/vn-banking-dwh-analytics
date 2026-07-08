"""Task 1.2: Consolidate stock daily metrics fact table.

Reads clean daily stock price history, casts types, and saves the consolidated
DataFrame as fact_stock_daily_metrics_clean.csv.
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def consolidate_stock_metrics(processed_dir: Path) -> bool:
    """Read the clean daily price history CSV and consolidate it.

    Args:
        processed_dir: Path to the processed data directory.

    Returns:
        True if consolidation succeeded, False otherwise.
    """
    price_history_path = processed_dir / "fact_price_history_clean.csv"

    if not price_history_path.exists():
        logger.error("Price history clean CSV not found at: %s", price_history_path)
        return False

    logger.info("Reading price history base from %s...", price_history_path)
    df_price = pd.read_csv(price_history_path)

    # Define standard column list and ensure all exist
    required_cols = [
        "date_key", "stock_key", "open_price", "high_price", "low_price", "close_price", "trading_volume"
    ]

    for col in required_cols:
        if col not in df_price.columns:
            logger.error("Required column %s not found in price history data.", col)
            return False

    df_merged = df_price[required_cols].copy()

    # Cast to appropriate types
    float_cols = ["open_price", "high_price", "low_price", "close_price"]
    int_cols = ["date_key", "stock_key", "trading_volume"]

    for col in float_cols:
        df_merged[col] = pd.to_numeric(df_merged[col], errors="coerce").astype("float64")
    for col in int_cols:
        df_merged[col] = pd.to_numeric(df_merged[col], errors="coerce").astype("Int64")

    # Sort and remove duplicates
    df_merged = df_merged.drop_duplicates(subset=["date_key", "stock_key"], keep="first")
    df_merged = df_merged.sort_values(["stock_key", "date_key"]).reset_index(drop=True)

    # Calculate 5 new metrics
    df_merged["price_change"] = df_merged["close_price"] - df_merged["open_price"]
    df_merged["price_change_pct"] = df_merged.groupby("stock_key")["close_price"].pct_change().fillna(0.0)
    df_merged["price_amplitude"] = (df_merged["high_price"] - df_merged["low_price"]) / df_merged["open_price"]
    df_merged["volume_change_pct"] = df_merged.groupby("stock_key")["trading_volume"].pct_change().fillna(0.0)
    df_merged["trading_value"] = df_merged["close_price"] * df_merged["trading_volume"]

    # Retain or populate system columns
    now_ts = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    df_merged["audit_key"] = audit_key
    df_merged["_created_at"] = now_ts
    df_merged["_updated_at"] = now_ts
    df_merged["_source_file"] = "consolidated_price_history"

    # Select final columns in order
    calculated_cols = ["price_change", "price_change_pct", "price_amplitude", "volume_change_pct", "trading_value"]
    final_cols = required_cols + calculated_cols + ["audit_key", "_created_at", "_updated_at", "_source_file"]
    df_final = df_merged[final_cols]

    output_path = processed_dir / "fact_stock_daily_metrics_clean.csv"
    df_final.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Saved consolidated metrics to %s. Total rows: %d.", output_path, len(df_final))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate clean daily stock CSVs.")
    parser.add_argument(
        "--processed-dir",
        default=None,
        help="Directory containing clean CSV files.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    processed_dir = Path(args.processed_dir) if args.processed_dir else Path(processed_data_path)

    success = consolidate_stock_metrics(processed_dir)
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
