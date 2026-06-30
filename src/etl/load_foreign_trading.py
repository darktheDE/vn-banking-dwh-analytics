"""Task B-09: Load fact_foreign_trading.

Reads the raw BID foreign trading data, cleans it, handles missing values
using forward-fill (max 1 day), and saves it locally as a CSV.
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


def transform_foreign_trading(df_raw: pd.DataFrame, audit_key: int, now_ts: datetime.datetime, source_filename: str) -> pd.DataFrame:
    """Transform raw BID foreign trading data.

    Args:
        df_raw: Raw foreign trading DataFrame.
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
        "Foreign Buy Volume": "foreign_buy_volume",
        "foreign_buy_volume": "foreign_buy_volume",
        "Foreign Sell Volume": "foreign_sell_volume",
        "foreign_sell_volume": "foreign_sell_volume",
        "Foreign Net Volume": "foreign_net_volume",
        "foreign_net_volume": "foreign_net_volume",
        "Foreign Net Value": "foreign_net_value",
        "foreign_net_value": "foreign_net_value",
        "Foreign Ownership": "foreign_ownership_ratio",
        "Foreign Ownership Ratio": "foreign_ownership_ratio",
        "foreign_ownership_ratio": "foreign_ownership_ratio",
    }

    df = df.rename(columns=column_mapping)

    required = {"date", "foreign_buy_volume", "foreign_sell_volume", "foreign_ownership_ratio"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Ensure other columns are computed if missing
    if "foreign_net_volume" not in df.columns:
        df["foreign_net_volume"] = df["foreign_buy_volume"] - df["foreign_sell_volume"]
    if "foreign_net_value" not in df.columns:
        df["foreign_net_value"] = pd.NA

    # Standardize types
    df["stock_key"] = BID_STOCK_KEY
    df["foreign_buy_volume"] = pd.to_numeric(df["foreign_buy_volume"], errors="coerce").astype("Int64")
    df["foreign_sell_volume"] = pd.to_numeric(df["foreign_sell_volume"], errors="coerce").astype("Int64")
    df["foreign_net_volume"] = pd.to_numeric(df["foreign_net_volume"], errors="coerce").astype("Int64")
    df["foreign_net_value"] = pd.to_numeric(df["foreign_net_value"], errors="coerce").astype("float64")
    df["foreign_ownership_ratio"] = pd.to_numeric(df["foreign_ownership_ratio"], errors="coerce").astype("float64")

    # Apply forward-fill for metrics (limit=1)
    metric_cols = ["foreign_buy_volume", "foreign_sell_volume", "foreign_net_volume", "foreign_net_value", "foreign_ownership_ratio"]
    for col in metric_cols:
        null_count = df[col].isna().sum()
        if null_count > 0:
            df[col] = df[col].ffill(limit=1)
            logger.warning("Applied forward-fill to %d null values in %s.", null_count, col)

    # Standardize dates
    df["date"] = pd.to_datetime(df["date"])
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype("int64")

    canonical_cols = [
        "date_key",
        "stock_key",
        "foreign_buy_volume",
        "foreign_sell_volume",
        "foreign_net_volume",
        "foreign_net_value",
        "foreign_ownership_ratio",
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
    parser = argparse.ArgumentParser(description="Clean and load foreign trading locally.")
    parser.add_argument(
        "--input-file",
        default=None,
        help="Path to raw foreign trading file.",
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

    input_file = Path(args.input_file) if args.input_file else Path(raw_data_path) / "BID_foreign_trading.xlsx"
    if not input_file.exists():
        logger.error("Input file %s not found.", input_file)
        return 1

    # Auditing parameters
    now = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    logger.info("Reading foreign trading from %s.", input_file)
    df_raw = pd.read_excel(input_file)
    df_clean = transform_foreign_trading(df_raw, audit_key, now, input_file.name)

    if len(df_clean) != 22:
        logger.warning("Row count is %d, expected 22 for sample dataset.", len(df_clean))

    output_path = output_dir / "fact_foreign_trading_clean.csv"
    df_clean.to_csv(output_path, index=False)
    logger.info("Saved fact_foreign_trading to %s. Rows: %d", output_path, len(df_clean))
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
