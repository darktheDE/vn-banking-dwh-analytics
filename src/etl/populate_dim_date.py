"""Task B-04: Populate dim_date.

Generates the calendar dimension table covering 2002-01-01 to 2026-12-31
and saves it locally as a CSV file in the processed data directory.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_dim_date(start_date: str = "2002-01-01", end_date: str = "2026-12-31") -> pd.DataFrame:
    """Generate calendar dimension DataFrame.

    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).

    Returns:
        DataFrame with columns: date_key, full_date, day, month, year, quarter, is_trading_day.
    """
    logger.info("Generating date range from %s to %s.", start_date, end_date)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    
    df = pd.DataFrame()
    df["full_date"] = dates.date.astype(str)
    df["date_key"] = dates.strftime("%Y%m%d").astype("int64")
    df["day"] = dates.day.astype("int64")
    df["month"] = dates.month.astype("int64")
    df["year"] = dates.year.astype("int64")
    df["quarter"] = dates.quarter.astype("int64")
    
    # Simple trading day logic: weekdays (Monday=0 to Friday=4) are trading days
    df["is_trading_day"] = dates.dayofweek < 5
    
    logger.info("Generated %d date records.", len(df))
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate dim_date dimension table locally.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the output CSV. Defaults to PROCESSED_DATA_PATH.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_date = generate_dim_date()
    
    # Append dynamic auditing columns
    import datetime
    now = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    df_date["audit_key"] = audit_key
    df_date["_created_at"] = now
    df_date["_updated_at"] = now
    df_date["_source_file"] = "populate_dim_date.py"
    
    output_path = output_dir / "dim_date_clean.csv"
    df_date.to_csv(output_path, index=False)
    
    logger.info("Saved dim_date to %s.", output_path)
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
