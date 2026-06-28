"""Task B-08: Load fact_price_history.

Reads the raw BID price history data, cleans and standardizes the prices,
and saves the cleaned DataFrame locally as a CSV file.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

BID_STOCK_KEY = 1


def transform_price_history(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw BID price history data.

    Args:
        df_raw: Raw price history DataFrame.

    Returns:
        Transformed DataFrame.
    """
    df = df_raw.copy()
    
    # Strip column names
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    
    # Map raw columns to canonical
    column_mapping = {
        "Date": "date",
        "Ngày": "date",
        "time": "date",
        "Open": "open_price",
        "Mở cửa": "open_price",
        "open": "open_price",
        "High": "high_price",
        "Cao nhất": "high_price",
        "high": "high_price",
        "Low": "low_price",
        "Thấp nhất": "low_price",
        "low": "low_price",
        "Close": "close_price",
        "Đóng cửa": "close_price",
        "close": "close_price",
        "Volume": "trading_volume",
        "Khối lượng": "trading_volume",
        "volume": "trading_volume",
    }
    
    df = df.rename(columns=column_mapping)
    
    # Ensure required columns are present
    required = {"date", "open_price", "high_price", "low_price", "close_price", "trading_volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
        
    # Drop rows with null close_price
    initial_len = len(df)
    df = df.dropna(subset=["close_price"])
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.warning("Dropped %d rows with null close_price.", dropped)
        
    # Standardize types
    df["stock_key"] = BID_STOCK_KEY
    df["open_price"] = pd.to_numeric(df["open_price"], errors="coerce").astype("float64")
    df["high_price"] = pd.to_numeric(df["high_price"], errors="coerce").astype("float64")
    df["low_price"] = pd.to_numeric(df["low_price"], errors="coerce").astype("float64")
    df["close_price"] = pd.to_numeric(df["close_price"], errors="coerce").astype("float64")
    df["trading_volume"] = pd.to_numeric(df["trading_volume"], errors="coerce").astype("Int64")
    
    # Standardize dates
    df["date"] = pd.to_datetime(df["date"])
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype("int64")
    
    # Select canonical columns
    canonical_cols = [
        "date_key",
        "stock_key",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "trading_volume",
    ]
    df = df.loc[:, canonical_cols]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["date_key", "stock_key"], keep="first").sort_values("date_key").reset_index(drop=True)
    
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and load price history locally.")
    parser.add_argument(
        "--input-file",
        default=None,
        help="Path to raw price history file. Defaults to data/bid_stock_history.csv or data/raw/BID_price_history.xlsx.",
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
    
    # Resolve input file
    input_file = None
    if args.input_file:
        input_file = Path(args.input_file)
    else:
        # Try raw excel first, then fallback to bid_stock_history.csv
        raw_excel = Path(raw_data_path) / "BID_price_history.xlsx"
        if raw_excel.exists():
            input_file = raw_excel
        else:
            local_csv = Path("./data/bid_stock_history.csv")
            if local_csv.exists():
                input_file = local_csv

    if not input_file or not input_file.exists():
        logger.error("Input file not found.")
        return 1

    logger.info("Reading price history from %s.", input_file)
    if input_file.suffix == ".xlsx":
        df_raw = pd.read_excel(input_file)
    else:
        df_raw = pd.read_csv(input_file)
        
    df_clean = transform_price_history(df_raw)
    
    # If using the specific raw test file (with 22 rows), validate the count
    if input_file.name == "BID_price_history.xlsx":
        if len(df_clean) != 22:
            logger.error("Row count mismatch. Expected 22, got %d.", len(df_clean))
            return 1
            
    output_path = output_dir / "fact_price_history_clean.csv"
    df_clean.to_csv(output_path, index=False)
    logger.info("Saved fact_price_history to %s. Rows: %d", output_path, len(df_clean))
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
