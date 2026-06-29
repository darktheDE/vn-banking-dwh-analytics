"""Task B-10: Load fact_proprietary_trading.

Reads the raw BID proprietary trading data, cleans it, handles missing values
using forward-fill (max 1 day), and saves it locally as a CSV.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

BID_STOCK_KEY = 1


def transform_proprietary_trading(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw BID proprietary trading data.

    Args:
        df_raw: Raw proprietary trading DataFrame.

    Returns:
        Transformed DataFrame.
    """
    df = df_raw.copy()

    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    column_mapping = {
        "Date": "date",
        "Ngày": "date",
        "time": "date",
        "Prop Buy Volume": "prop_buy_volume",
        "prop_buy_volume": "prop_buy_volume",
        "Prop Sell Volume": "prop_sell_volume",
        "prop_sell_volume": "prop_sell_volume",
        "Prop Net Volume": "prop_net_volume",
        "prop_net_volume": "prop_net_volume",
        "Prop Net Value": "prop_net_value",
        "prop_net_value": "prop_net_value",
    }

    df = df.rename(columns=column_mapping)

    required = {"date", "prop_buy_volume", "prop_sell_volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if "prop_net_volume" not in df.columns:
        df["prop_net_volume"] = df["prop_buy_volume"] - df["prop_sell_volume"]
    if "prop_net_value" not in df.columns:
        df["prop_net_value"] = pd.NA

    # Standardize types
    df["stock_key"] = BID_STOCK_KEY
    df["prop_buy_volume"] = pd.to_numeric(df["prop_buy_volume"], errors="coerce").astype("Int64")
    df["prop_sell_volume"] = pd.to_numeric(df["prop_sell_volume"], errors="coerce").astype("Int64")
    df["prop_net_volume"] = pd.to_numeric(df["prop_net_volume"], errors="coerce").astype("Int64")
    df["prop_net_value"] = pd.to_numeric(df["prop_net_value"], errors="coerce").astype("float64")

    # Apply forward-fill (limit=1)
    metric_cols = ["prop_buy_volume", "prop_sell_volume", "prop_net_volume", "prop_net_value"]
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
        "prop_buy_volume",
        "prop_sell_volume",
        "prop_net_volume",
        "prop_net_value",
    ]
    df = df.loc[:, canonical_cols]

    # Remove duplicates
    df = df.drop_duplicates(subset=["date_key", "stock_key"], keep="first").sort_values("date_key").reset_index(drop=True)

    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and load proprietary trading locally.")
    parser.add_argument(
        "--input-file",
        default=None,
        help="Path to raw proprietary trading file.",
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

    input_file = Path(args.input_file) if args.input_file else Path(raw_data_path) / "BID_proprietary_trading.xlsx"
    if not input_file.exists():
        logger.error("Input file %s not found.", input_file)
        return 1

    logger.info("Reading proprietary trading from %s.", input_file)
    df_raw = pd.read_excel(input_file)
    df_clean = transform_proprietary_trading(df_raw)

    if len(df_clean) != 22:
        logger.warning("Row count is %d, expected 22 for sample dataset.", len(df_clean))

    output_path = output_dir / "fact_proprietary_trading_clean.csv"
    df_clean.to_csv(output_path, index=False)
    logger.info("Saved fact_proprietary_trading to %s. Rows: %d", output_path, len(df_clean))
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
