"""Task B-11: Load fact_order_stats.

Reads the raw BID order statistics data, cleans it, rejects null rows
(no forward-fill), and saves it locally as a CSV.
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

BID_STOCK_KEY = 1


def transform_order_stats(df_raw: pd.DataFrame, audit_key: int, now_ts: datetime.datetime, source_filename: str) -> pd.DataFrame:
    """Transform raw BID order stats data.

    Args:
        df_raw: Raw order stats DataFrame.
        audit_key: Audit run key.
        now_ts: Execution timestamp.
        source_filename: Name of the source file.

    Returns:
        Transformed DataFrame.
    """
    df = df_raw.copy()

    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    column_mapping = {
        "Date": "date",
        "Ngày": "date",
        "time": "date",
        "Total Buy Orders": "total_buy_orders",
        "total_buy_orders": "total_buy_orders",
        "Total Buy Volume": "total_buy_volume",
        "total_buy_volume": "total_buy_volume",
        "Total Sell Orders": "total_sell_orders",
        "total_sell_orders": "total_sell_orders",
        "Total Sell Volume": "total_sell_volume",
        "total_sell_volume": "total_sell_volume",
        "Matched Volume": "matched_volume",
        "matched_volume": "matched_volume",
    }

    df = df.rename(columns=column_mapping)

    required = {
        "date",
        "total_buy_orders",
        "total_buy_volume",
        "total_sell_orders",
        "total_sell_volume",
        "matched_volume",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Reject null rows (no forward-fill for order stats)
    initial_len = len(df)
    df = df.dropna(subset=list(required))
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.warning("Dropped %d rows with null values in order statistics.", dropped)

    # Standardize types
    df["stock_key"] = BID_STOCK_KEY
    df["total_buy_orders"] = pd.to_numeric(df["total_buy_orders"], errors="coerce").astype("Int64")
    df["total_buy_volume"] = pd.to_numeric(df["total_buy_volume"], errors="coerce").astype("Int64")
    df["total_sell_orders"] = pd.to_numeric(df["total_sell_orders"], errors="coerce").astype("Int64")
    df["total_sell_volume"] = pd.to_numeric(df["total_sell_volume"], errors="coerce").astype("Int64")
    df["matched_volume"] = pd.to_numeric(df["matched_volume"], errors="coerce").astype("Int64")

    # Standardize dates
    df["date"] = pd.to_datetime(df["date"])
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype("int64")

    canonical_cols = [
        "date_key",
        "stock_key",
        "total_buy_orders",
        "total_buy_volume",
        "total_sell_orders",
        "total_sell_volume",
        "matched_volume",
    ]
    df = df.loc[:, canonical_cols]

    # Remove duplicates
    df = df.drop_duplicates(subset=["date_key", "stock_key"], keep="first").sort_values("date_key").reset_index(drop=True)

    # Append dynamic auditing columns
    df["audit_key"] = audit_key
    df["_created_at"] = now_ts
    df["_updated_at"] = now_ts
    df["_source_file"] = source_filename

    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and load order stats locally.")
    parser.add_argument(
        "--input-file",
        default=None,
        help="Path to raw order stats file.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the output CSV. Defaults to PROCESSED_DATA_PATH.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    raw_data_path = os.getenv("RAW_DATA_PATH", "./data/raw/")
    output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = Path(args.input_file) if args.input_file else Path(raw_data_path) / "BID_order_stats.xlsx"
    if not input_file.exists():
        logger.error("Input file %s not found.", input_file)
        return 1

    # Auditing parameters
    now = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    logger.info("Reading order stats from %s.", input_file)
    df_raw = pd.read_excel(input_file)
    df_clean = transform_order_stats(df_raw, audit_key, now, input_file.name)

    if len(df_clean) != 22:
        logger.warning("Row count is %d, expected 22 for sample dataset.", len(df_clean))

    output_path = output_dir / "fact_order_stats_clean.csv"
    df_clean.to_csv(output_path, index=False)
    logger.info("Saved fact_order_stats to %s. Rows: %d", output_path, len(df_clean))
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
