"""Unified script to load cleaned CSV data into BigQuery tables.

Fulfills tasks B-04 through B-13 by reading the processed files in data/processed/
and loading them into the provisioned tables in BigQuery.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd

from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Mapping of BigQuery table names to their clean CSV files and required columns
TABLES_TO_CSV = {
    "dim_date": {
        "file": "dim_date_clean.csv",
        "columns": ["date_key", "full_date", "day", "month", "year", "quarter", "is_trading_day"],
        "types": {
            "date_key": "int64",
            "day": "int64",
            "month": "int64",
            "year": "int64",
            "quarter": "int64",
            "is_trading_day": "bool",
        }
    },
    "dim_stock": {
        "file": "dim_stock_clean.csv",
        "columns": ["stock_key", "ticker", "company_name", "exchange", "industry"],
        "types": {
            "stock_key": "int64",
        }
    },
    "dim_bank": {
        "file": "dim_bank_clean.csv",
        "columns": ["bank_key", "bank_code", "bank_name", "bank_type", "charter_capital"],
        "types": {
            "bank_key": "int64",
            "charter_capital": "float64",
        }
    },
    "dim_trading_session": {
        "file": "dim_trading_session_clean.csv",
        "columns": ["session_key", "session_name", "start_time", "end_time"],
        "types": {
            "session_key": "int64",
        }
    },
    "fact_price_history": {
        "file": "fact_price_history_clean.csv",
        "columns": ["date_key", "stock_key", "open_price", "high_price", "low_price", "close_price", "trading_volume"],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "open_price": "float64",
            "high_price": "float64",
            "low_price": "float64",
            "close_price": "float64",
            "trading_volume": "int64",
        }
    },
    "fact_foreign_trading": {
        "file": "fact_foreign_trading_clean.csv",
        "columns": ["date_key", "stock_key", "foreign_buy_volume", "foreign_sell_volume", "foreign_net_volume", "foreign_net_value", "foreign_ownership_ratio"],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "foreign_buy_volume": "int64",
            "foreign_sell_volume": "int64",
            "foreign_net_volume": "int64",
            "foreign_net_value": "float64",
            "foreign_ownership_ratio": "float64",
        }
    },
    "fact_proprietary_trading": {
        "file": "fact_proprietary_trading_clean.csv",
        "columns": ["date_key", "stock_key", "prop_buy_volume", "prop_sell_volume", "prop_net_volume", "prop_net_value"],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "prop_buy_volume": "int64",
            "prop_sell_volume": "int64",
            "prop_net_volume": "int64",
            "prop_net_value": "float64",
        }
    },
    "fact_order_stats": {
        "file": "fact_order_stats_clean.csv",
        "columns": ["date_key", "stock_key", "total_buy_orders", "total_buy_volume", "total_sell_orders", "total_sell_volume", "matched_volume"],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "total_buy_orders": "int64",
            "total_buy_volume": "int64",
            "total_sell_orders": "int64",
            "total_sell_volume": "int64",
            "matched_volume": "int64",
        }
    },
    "fact_intraday_matching": {
        "file": "fact_intraday_matching_clean.csv",
        "columns": ["date_key", "stock_key", "session_key", "timestamp", "matched_price", "matched_volume", "cumulative_volume"],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "session_key": "int64",
            "matched_price": "float64",
            "matched_volume": "int64",
            "cumulative_volume": "int64",
        }
    },
    "fact_bank_performance": {
        "file": "fact_bank_performance_clean.csv",
        "columns": [
            "date_key", "bank_key", "total_assets", "total_deposits", "total_loans", "total_equity",
            "num_employees", "num_branches", "npl_amount", "loan_loss_provision", "interest_income",
            "interest_expense", "net_interest_income", "non_interest_expense", "personnel_expense",
            "other_expense", "profit_before_tax", "profit_after_tax", "off_balance_sheet", "npl_ratio",
            "llp_ratio", "roa", "roe", "nim", "cir", "eta", "etd", "lta", "ltd", "gta", "is_imputed"
        ],
        "types": {
            "date_key": "int64",
            "bank_key": "int64",
            "total_assets": "float64",
            "total_deposits": "float64",
            "total_loans": "float64",
            "total_equity": "float64",
            "num_employees": "int64",
            "num_branches": "int64",
            "npl_amount": "float64",
            "loan_loss_provision": "float64",
            "interest_income": "float64",
            "interest_expense": "float64",
            "net_interest_income": "float64",
            "non_interest_expense": "float64",
            "personnel_expense": "float64",
            "other_expense": "float64",
            "profit_before_tax": "float64",
            "profit_after_tax": "float64",
            "off_balance_sheet": "float64",
            "npl_ratio": "float64",
            "llp_ratio": "float64",
            "roa": "float64",
            "roe": "float64",
            "nim": "float64",
            "cir": "float64",
            "eta": "float64",
            "etd": "float64",
            "lta": "float64",
            "ltd": "float64",
            "gta": "float64",
            "is_imputed": "bool",
        }
    }
}


def load_clean_data(write_disposition: str = "WRITE_TRUNCATE") -> bool:
    """Load local clean CSV files into BigQuery.

    Args:
        write_disposition: BigQuery WRITE_TRUNCATE (overwrites table) or WRITE_APPEND.

    Returns:
        True if all files loaded successfully, False otherwise.
    """
    processed_dir = Path(os.getenv("PROCESSED_DATA_PATH", "./data/processed/"))
    client = get_bigquery_client()

    success = True

    for table_name, spec in TABLES_TO_CSV.items():
        csv_path = processed_dir / spec["file"]
        if not csv_path.exists():
            logger.warning("Local CSV file not found for table %s: %s. Skipping.", table_name, csv_path)
            continue

        logger.info("Reading %s...", csv_path)
        df = pd.read_csv(csv_path)

        # Filter columns to only include those in schema spec
        df_filtered = df[[c for c in spec["columns"] if c in df.columns]].copy()

        # Handle missing columns if any
        missing_cols = set(spec["columns"]) - set(df_filtered.columns)
        for col in missing_cols:
            logger.warning("Column %s is missing from %s. Filling with nulls.", col, spec["file"])
            df_filtered[col] = None

        # Reorder columns to match schema spec
        df_filtered = df_filtered[spec["columns"]]

        # Standardize types to prevent BigQuery loading errors
        if "types" in spec:
            for col, dtype in spec["types"].items():
                try:
                    if dtype == "int64":
                        df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce").astype("Int64")
                    elif dtype == "float64":
                        df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce").astype("float64")
                    elif dtype == "bool":
                        df_filtered[col] = df_filtered[col].astype(bool)
                except Exception as e:
                    logger.error("Failed to cast column %s to %s: %s", col, dtype, str(e))

        # Handle timestamp parsing for intraday
        if table_name == "fact_intraday_matching":
            df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])

        full_table_id = get_full_table_id(table_name)
        logger.info("Loading %d rows into BigQuery table %s (%s)...", len(df_filtered), table_name, write_disposition)

        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
        )

        try:
            job = client.load_table_from_dataframe(df_filtered, full_table_id, job_config=job_config)
            job.result()  # Wait for the load job to complete
            logger.info("Loaded %d rows into %s successfully.", len(df_filtered), full_table_id)
        except Exception as e:
            logger.error("Failed to load table %s into BigQuery: %s", full_table_id, str(e))
            success = False

    return success


def main() -> int:
    load_dotenv()
    # Default to WRITE_TRUNCATE to populate tables cleanly on initial setup
    try:
        success = load_clean_data(write_disposition="WRITE_TRUNCATE")
        return 0 if success else 1
    except Exception as e:
        logger.exception("An unhandled exception occurred during BigQuery load: %s", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
