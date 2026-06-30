"""Task B-06: Populate dim_bank.

Reads the banks list from the raw CAMELS Excel file, standardizes the bank records,
and implements Slowly Changing Dimension (SCD Type 2) tracking for updates.
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger
from src.utils.config import load_config
from src.utils.bigquery_client import get_bigquery_client

logger = get_logger(__name__)

WORKBOOK_NAME = "VN banks dataset (updated August 2023).xlsx"
BANKS_SHEET_NAME = "Banks List"


def populate_bank_dimension(workbook_path: Path, audit_key: int, now_ts: datetime.datetime) -> pd.DataFrame:
    """Extract bank list from the Excel workbook and format as dim_bank.

    Args:
        workbook_path: Path to the raw Excel workbook.
        audit_key: The audit run key.
        now_ts: Execution timestamp.

    Returns:
        DataFrame with dim_bank columns.
    """
    logger.info("Reading bank list from sheet '%s' in %s.", BANKS_SHEET_NAME, workbook_path)
    
    # Read sheet
    df_raw = pd.read_excel(workbook_path, sheet_name=BANKS_SHEET_NAME)
    
    # Clean column names
    df_raw.columns = [c.strip() if isinstance(c, str) else c for c in df_raw.columns]
    
    required = {"No.", "Bank", "Bank Code", "Type of ownership"}
    missing = required - set(df_raw.columns)
    if missing:
        raise ValueError(f"Banks List sheet is missing columns: {sorted(missing)}")
        
    df_clean = df_raw.dropna(subset=["No.", "Bank", "Bank Code", "Type of ownership"])
    
    # Rename to schema
    df_dim = df_clean.loc[:, ["No.", "Bank", "Bank Code", "Type of ownership"]].rename(
        columns={
            "No.": "bank_key",
            "Bank": "bank_name",
            "Bank Code": "bank_code",
            "Type of ownership": "bank_type",
        }
    )
    
    # Format columns
    df_dim["bank_key"] = pd.to_numeric(df_dim["bank_key"], errors="coerce").astype("Int64")
    df_dim["bank_code"] = df_dim["bank_code"].astype(str).str.strip().str.upper()
    df_dim["bank_name"] = df_dim["bank_name"].astype(str).str.strip()
    df_dim["bank_type"] = df_dim["bank_type"].astype(str).str.strip().str.upper()
    df_dim["charter_capital"] = pd.NA  # Raw Excel does not contain charter capital data; initialized as NULL for future extension
    
    # Clean duplicates
    df_dim = df_dim.dropna(subset=["bank_key", "bank_code", "bank_name", "bank_type"])
    df_dim = df_dim.drop_duplicates(subset=["bank_code"], keep="first").sort_values("bank_key").reset_index(drop=True)
    
    logger.info("Extracted %d bank records from source file.", len(df_dim))
    return df_dim


def apply_scd_type2(df_new: pd.DataFrame, existing_df: pd.DataFrame | None, audit_key: int, now_ts: datetime.datetime, source_filename: str) -> pd.DataFrame:
    """Applies Slowly Changing Dimension Type 2 updates between new file and existing DWH dim_bank.
    """
    today_date = now_ts.date()
    default_start = datetime.date(2002, 1, 1)
    future_end = datetime.date(9999, 12, 31)

    # If no existing history, initialize all as current
    if existing_df is None or existing_df.empty:
        logger.info("No existing records found. Initializing all banks with default SCD Type 2 windows.")
        df_new["valid_from"] = default_start
        df_new["valid_to"] = future_end
        df_new["is_current"] = True
        df_new["audit_key"] = audit_key
        df_new["_created_at"] = now_ts
        df_new["_updated_at"] = now_ts
        df_new["_source_file"] = source_filename
        return df_new

    # Convert existing columns to proper types for comparison
    existing_df["valid_from"] = pd.to_datetime(existing_df["valid_from"]).dt.date
    existing_df["valid_to"] = pd.to_datetime(existing_df["valid_to"]).dt.date
    existing_df["is_current"] = existing_df["is_current"].astype(bool)
    existing_df["bank_key"] = existing_df["bank_key"].astype("Int64")
    
    updated_records = []
    
    # Map existing code to active rows for fast lookup
    active_rows = existing_df[existing_df["is_current"] == True].set_index("bank_code").to_dict(orient="index")
    
    # Track which bank_codes from existing we processed
    processed_codes = set()

    for _, row in df_new.iterrows():
        code = row["bank_code"]
        processed_codes.add(code)
        
        # Check if bank code already exists as active in BigQuery
        if code in active_rows:
            active_row = active_rows[code]
            
            # Compare descriptive fields (bank_name, bank_type, charter_capital)
            has_changed = (
                row["bank_name"] != active_row["bank_name"] or
                row["bank_type"] != active_row["bank_type"] or
                (pd.notna(row["charter_capital"]) and row["charter_capital"] != active_row["charter_capital"])
            )
            
            if has_changed:
                logger.info("SCD Type 2: Change detected for bank %s. Expiring old record and creating new version.", code)
                
                # 1. Expire existing active record in the historical dataframe
                # Find index of this record in the original existing_df
                idx = existing_df[(existing_df["bank_code"] == code) & (existing_df["is_current"] == True)].index
                if len(idx) > 0:
                    existing_df.loc[idx, "valid_to"] = today_date - datetime.timedelta(days=1)
                    existing_df.loc[idx, "is_current"] = False
                    existing_df.loc[idx, "_updated_at"] = now_ts
                    existing_df.loc[idx, "audit_key"] = audit_key
                
                # 2. Add new record version
                new_version = {
                    "bank_key": row["bank_key"],
                    "bank_code": code,
                    "bank_name": row["bank_name"],
                    "bank_type": row["bank_type"],
                    "charter_capital": row["charter_capital"],
                    "valid_from": today_date,
                    "valid_to": future_end,
                    "is_current": True,
                    "audit_key": audit_key,
                    "_created_at": now_ts,
                    "_updated_at": now_ts,
                    "_source_file": source_filename
                }
                updated_records.append(new_version)
        else:
            # New bank not previously tracked in DWH
            logger.info("SCD Type 2: New bank %s detected. Creating initial record.", code)
            new_record = {
                "bank_key": row["bank_key"],
                "bank_code": code,
                "bank_name": row["bank_name"],
                "bank_type": row["bank_type"],
                "charter_capital": row["charter_capital"],
                "valid_from": default_start,
                "valid_to": future_end,
                "is_current": True,
                "audit_key": audit_key,
                "_created_at": now_ts,
                "_updated_at": now_ts,
                "_source_file": source_filename
            }
            updated_records.append(new_record)

    # Append new/updated records to existing historical dataframe
    if updated_records:
        df_updated = pd.DataFrame(updated_records)
        existing_df = pd.concat([existing_df, df_updated], ignore_index=True)
        
    return existing_df


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate dim_bank table locally with SCD Type 2.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the output CSV. Defaults to PROCESSED_DATA_PATH.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    raw_data_path = os.getenv("RAW_DATA_PATH", "./data/")
    output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    workbook_path = Path(raw_data_path) / WORKBOOK_NAME
    if not workbook_path.exists():
        workbook_path = Path("./data") / WORKBOOK_NAME
        
    if not workbook_path.exists():
        logger.error("Raw bank dataset not found at %s. Please check configuration.", workbook_path)
        return 1

    # Auditing parameters
    now = datetime.datetime.utcnow()
    audit_key = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    # Fetch existing dim_bank rows from BigQuery for SCD checks
    existing_df = None
    try:
        config = load_config()
        client = get_bigquery_client()
        table_id = f"{config.bq_dataset_id}.dim_bank"
        query = f"SELECT * FROM `{client.project}.{table_id}`"
        query_job = client.query(query)
        existing_df = query_job.to_dataframe()
        logger.info("Retrieved %d existing bank records from BigQuery for SCD tracking.", len(existing_df))
    except Exception as e:
        logger.info("Could not fetch existing dim_bank records (it may not exist yet): %s. Running initial load.", str(e))

    df_new = populate_bank_dimension(workbook_path, audit_key, now)
    
    # Process SCD Type 2
    df_consolidated = apply_scd_type2(df_new, existing_df, audit_key, now, WORKBOOK_NAME)
    
    output_path = output_dir / "dim_bank_clean.csv"
    df_consolidated.to_csv(output_path, index=False)

    logger.info("Saved dim_bank with SCD history to %s. Total rows: %d.", output_path, len(df_consolidated))
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
