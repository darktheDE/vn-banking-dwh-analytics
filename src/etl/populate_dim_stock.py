"""Task B-05: Populate dim_stock.

Generates stock dimension records for BID, TCB, VCB, and CTG, and saves them locally
as a CSV file in the processed data directory.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_dim_stock() -> pd.DataFrame:
    """Generate stock dimension records.

    Returns:
        DataFrame with columns: stock_key, ticker, company_name, exchange, industry.
    """
    records = [
        {
            "stock_key": 1,
            "ticker": "BID",
            "company_name": "Joint Stock Commercial Bank for Investment and Development of Vietnam",
            "exchange": "HOSE",
            "industry": "Banking",
        },
        {
            "stock_key": 2,
            "ticker": "TCB",
            "company_name": "Vietnam Technological and Commercial Joint Stock Bank",
            "exchange": "HOSE",
            "industry": "Banking",
        },
        {
            "stock_key": 3,
            "ticker": "VCB",
            "company_name": "Joint Stock Commercial Bank for Foreign Trade of Vietnam",
            "exchange": "HOSE",
            "industry": "Banking",
        },
        {
            "stock_key": 4,
            "ticker": "CTG",
            "company_name": "Vietnam Joint Stock Commercial Bank for Industry and Trade",
            "exchange": "HOSE",
            "industry": "Banking",
        },
    ]
    df = pd.DataFrame(records)
    logger.info("Generated %d stock records (BID, TCB, VCB, CTG).", len(df))
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate dim_stock table locally.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the output CSV. Defaults to PROCESSED_DATA_PATH.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_stock = generate_dim_stock()
    
    # Append dynamic auditing columns
    import datetime
    now = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    df_stock["audit_key"] = audit_key
    df_stock["_created_at"] = now
    df_stock["_updated_at"] = now
    df_stock["_source_file"] = "populate_dim_stock.py"
    
    output_path = output_dir / "dim_stock_clean.csv"
    df_stock.to_csv(output_path, index=False)

    logger.info("Saved dim_stock to %s.", output_path)
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
