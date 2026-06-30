"""Task B-07: Populate dim_trading_session.

Generates HOSE trading session dimension records and saves them locally
as a CSV file in the processed data directory.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_dim_trading_session() -> pd.DataFrame:
    """Generate trading session records.

    Returns:
        DataFrame with columns: session_key, session_name, start_time, end_time.
    """
    records = [
        {
            "session_key": 1,
            "session_name": "ATO",
            "start_time": "09:00:00",
            "end_time": "09:14:59",
        },
        {
            "session_key": 2,
            "session_name": "Morning",
            "start_time": "09:15:00",
            "end_time": "11:29:59",
        },
        {
            "session_key": 3,
            "session_name": "Afternoon",
            "start_time": "13:00:00",
            "end_time": "14:29:59",
        },
        {
            "session_key": 4,
            "session_name": "ATC",
            "start_time": "14:30:00",
            "end_time": "14:45:00",
        },
    ]
    df = pd.DataFrame(records)
    logger.info("Generated %d trading session records.", len(df))
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate dim_trading_session table locally.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the output CSV. Defaults to PROCESSED_DATA_PATH.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_session = generate_dim_trading_session()
    
    # Append dynamic auditing columns
    import datetime
    now = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    df_session["audit_key"] = audit_key
    df_session["_created_at"] = now
    df_session["_updated_at"] = now
    df_session["_source_file"] = "populate_dim_trading_session.py"
    
    output_path = output_dir / "dim_trading_session_clean.csv"
    df_session.to_csv(output_path, index=False)

    logger.info("Saved dim_trading_session to %s.", output_path)
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
