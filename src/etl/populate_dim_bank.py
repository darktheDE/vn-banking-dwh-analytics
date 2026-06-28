"""Task B-06: Populate dim_bank.

Reads the banks list from the raw CAMELS Excel file, standardizes the bank records,
and saves them locally as a CSV file in the processed data directory.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

WORKBOOK_NAME = "VN banks dataset (updated August 2023).xlsx"
BANKS_SHEET_NAME = "Banks List"


def populate_bank_dimension(workbook_path: Path) -> pd.DataFrame:
    """Extract bank list from the Excel workbook and format as dim_bank.

    Args:
        workbook_path: Path to the raw Excel workbook.

    Returns:
        DataFrame with columns: bank_key, bank_code, bank_name, bank_type, charter_capital.
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
    df_dim["charter_capital"] = pd.NA
    
    # Clean duplicates
    df_dim = df_dim.dropna(subset=["bank_key", "bank_code", "bank_name", "bank_type"])
    df_dim = df_dim.drop_duplicates(subset=["bank_code"], keep="first").sort_values("bank_key").reset_index(drop=True)
    
    logger.info("Extracted %d bank records.", len(df_dim))
    return df_dim


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate dim_bank table locally.")
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
        # Fallback to check directly in project root's data folder
        workbook_path = Path("./data") / WORKBOOK_NAME
        
    if not workbook_path.exists():
        logger.error("Raw bank dataset not found at %s. Please check configuration.", workbook_path)
        return 1

    df_bank = populate_bank_dimension(workbook_path)
    output_path = output_dir / "dim_bank_clean.csv"
    df_bank.to_csv(output_path, index=False)

    logger.info("Saved dim_bank to %s.", output_path)
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
