"""Task B-08: Load fact_price_history.

Reads raw/processed price history data for focus banks (BID, TCB, VCB, CTG),
cleans and standardizes the prices, and saves a consolidated fact DataFrame
locally as a CSV file.
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def transform_price_history(df_raw: pd.DataFrame, stock_key: int, audit_key: int, now_ts: datetime.datetime, source_filename: str) -> pd.DataFrame:
    """Transform raw/processed price history data.

    Args:
        df_raw: Raw price history DataFrame.
        stock_key: Stock surrogate key to assign.
        audit_key: Audit run key.
        now_ts: Execution timestamp.
        source_filename: Name of the source file.

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
    df["stock_key"] = stock_key
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
    
    # Add audit metadata columns
    df["audit_key"] = audit_key
    df["_created_at"] = now_ts
    df["_updated_at"] = now_ts
    df["_source_file"] = source_filename
    
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and load price history locally for all focus stocks.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the output CSV. Defaults to PROCESSED_DATA_PATH.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Auditing parameters
    now = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    
    stock_configs = [
        {"symbol": "BID", "key": 1, "path": "bid/bid_stock_history.csv"},
        {"symbol": "TCB", "key": 2, "path": "tcb/tcb_stock_history.csv"},
        {"symbol": "VCB", "key": 3, "path": "vcb/vcb_stock_history.csv"},
        {"symbol": "CTG", "key": 4, "path": "ctg/ctg_stock_history.csv"},
    ]
    
    all_dfs = []
    
    for config in stock_configs:
        file_path = Path(processed_data_path) / config["path"]
        if file_path.exists():
            logger.info("Processing price history for %s (key %d) from %s...", config["symbol"], config["key"], file_path)
            try:
                df_raw = pd.read_csv(file_path)
                df_clean = transform_price_history(df_raw, config["key"], audit_key, now, file_path.name)
                all_dfs.append(df_clean)
            except Exception as e:
                logger.error("Error transforming %s: %s", config["symbol"], str(e))
        else:
            logger.warning("Stock history file not found for %s at %s.", config["symbol"], file_path)
            
    # Fallback if no files found
    if not all_dfs:
        raw_excel = Path("./data/raw/BID_price_history.xlsx")
        if raw_excel.exists():
            logger.info("Falling back to raw Excel: %s", raw_excel)
            df_raw = pd.read_excel(raw_excel)
            df_clean = transform_price_history(df_raw, 1, audit_key, now, raw_excel.name)
            all_dfs.append(df_clean)

    if not all_dfs:
        logger.error("No stock price history files found to process.")
        return 1
        
    df_final = pd.concat(all_dfs, ignore_index=True)
    
    output_path = output_dir / "fact_price_history_clean.csv"
    df_final.to_csv(output_path, index=False)
    logger.info("Saved consolidated fact_price_history to %s. Total rows: %d", output_path, len(df_final))
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
