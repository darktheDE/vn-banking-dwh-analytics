"""Unified script to load cleaned CSV data into BigQuery tables.

Fulfills tasks B-04 through B-13 by reading the processed files in data/processed/
and loading them incrementally into BigQuery using SQL MERGE queries.
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import sys
import uuid

from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd

from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Mapping of BigQuery table names to their clean CSV files, keys, required columns, and types
TABLES_TO_CSV = {
    "dim_date": {
        "file": "dim_date_clean.csv",
        "keys": ["date_key"],
        "columns": [
            "date_key", "full_date", "day", "month", "year", "quarter", "is_trading_day",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "date_key": "int64",
            "day": "int64",
            "month": "int64",
            "year": "int64",
            "quarter": "int64",
            "is_trading_day": "bool",
            "audit_key": "int64",
        }
    },
    "dim_stock": {
        "file": "dim_stock_clean.csv",
        "keys": ["stock_key"],
        "columns": [
            "stock_key", "ticker", "company_name", "exchange", "industry",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "stock_key": "int64",
            "audit_key": "int64",
        }
    },
    "dim_bank": {
        "file": "dim_bank_clean.csv",
        "keys": ["bank_code", "valid_from"],
        "columns": [
            "bank_key", "bank_code", "bank_name", "bank_type", "charter_capital",
            "valid_from", "valid_to", "is_current",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "bank_key": "int64",
            "charter_capital": "float64",
            "is_current": "bool",
            "audit_key": "int64",
        }
    },
    "dim_trading_session": {
        "file": "dim_trading_session_clean.csv",
        "keys": ["session_key"],
        "columns": [
            "session_key", "session_name", "start_time", "end_time",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "session_key": "int64",
            "audit_key": "int64",
        }
    },
    "fact_price_history": {
        "file": "fact_price_history_clean.csv",
        "keys": ["date_key", "stock_key"],
        "columns": [
            "date_key", "stock_key", "open_price", "high_price", "low_price", "close_price", "trading_volume",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "open_price": "float64",
            "high_price": "float64",
            "low_price": "float64",
            "close_price": "float64",
            "trading_volume": "int64",
            "audit_key": "int64",
        }
    },
    "fact_foreign_trading": {
        "file": "fact_foreign_trading_clean.csv",
        "keys": ["date_key", "stock_key"],
        "columns": [
            "date_key", "stock_key", "foreign_buy_volume", "foreign_sell_volume", "foreign_net_volume", "foreign_net_value", "foreign_ownership_ratio",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "foreign_buy_volume": "int64",
            "foreign_sell_volume": "int64",
            "foreign_net_volume": "int64",
            "foreign_net_value": "float64",
            "foreign_ownership_ratio": "float64",
            "audit_key": "int64",
        }
    },
    "fact_proprietary_trading": {
        "file": "fact_proprietary_trading_clean.csv",
        "keys": ["date_key", "stock_key"],
        "columns": [
            "date_key", "stock_key", "prop_buy_volume", "prop_sell_volume", "prop_net_volume", "prop_net_value",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "prop_buy_volume": "int64",
            "prop_sell_volume": "int64",
            "prop_net_volume": "int64",
            "prop_net_value": "float64",
            "audit_key": "int64",
        }
    },
    "fact_order_stats": {
        "file": "fact_order_stats_clean.csv",
        "keys": ["date_key", "stock_key"],
        "columns": [
            "date_key", "stock_key", "total_buy_orders", "total_buy_volume", "total_sell_orders", "total_sell_volume", "matched_volume",
            "audit_key", "_created_at", "_updated_at", "_source_file"
        ],
        "types": {
            "date_key": "int64",
            "stock_key": "int64",
            "total_buy_orders": "int64",
            "total_buy_volume": "int64",
            "total_sell_orders": "int64",
            "total_sell_volume": "int64",
            "matched_volume": "int64",
            "audit_key": "int64",
        }
    },
    "fact_bank_performance": {
        "file": "fact_bank_performance_clean.csv",
        "keys": ["date_key", "bank_key"],
        "columns": [
            "date_key", "bank_key", "total_assets", "total_deposits", "total_loans", "total_equity",
            "num_employees", "num_branches", "npl_amount", "loan_loss_provision",
            "interest_income", "interest_expense", "net_interest_income",
            "non_interest_expense", "personnel_expense", "other_expense",
            "profit_before_tax", "profit_after_tax", "off_balance_sheet",
            "npl_ratio", "llp_ratio", "roa", "roe", "nim", "cir", "eta", "etd", "lta", "ltd", "gta", "is_imputed",
            "audit_key", "_created_at", "_updated_at", "_source_file"
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
            "audit_key": "int64",
        }
    }
}


def log_audit_run(
    client: bigquery.Client,
    dataset_id: str,
    audit_key: int,
    run_id: str,
    script_name: str,
    source_file: str,
    rows_processed: int,
    status: str
) -> None:
    """Insert run metadata into the dim_audit table.

    Frees us from streaming insert limitations in BigQuery Free Tier by loading via batch load job.
    """
    table_ref = f"{client.project}.{dataset_id}.dim_audit"
    
    row = {
        "audit_key": [audit_key],
        "run_id": [run_id],
        "run_timestamp": [pd.Timestamp(datetime.datetime.utcnow())],
        "script_name": [script_name],
        "source_file": [source_file],
        "rows_processed": [rows_processed],
        "status": [status]
    }
    df_audit = pd.DataFrame(row)
    
    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        )
        job = client.load_table_from_dataframe(df_audit, table_ref, job_config=job_config)
        job.result()
        logger.info("Logged audit run %d (%s) status as %s in dim_audit.", audit_key, script_name, status)
    except Exception as e:
        logger.error("Failed to log audit run in dim_audit: %s", str(e))


def load_incremental_via_merge(
    df: pd.DataFrame,
    table_name: str,
    client: bigquery.Client,
    dataset_id: str,
    spec: dict
) -> None:
    """Uploads DataFrame to a staging table, merges into target table, and drops staging.

    Falls back to direct WRITE_APPEND if billing is disabled.
    """
    staging_table_name = f"staging_{table_name}"
    staging_table_id = f"{client.project}.{dataset_id}.{staging_table_name}"
    target_table_id = f"{client.project}.{dataset_id}.{table_name}"
    
    try:
        logger.info("Loading %d rows into staging table %s...", len(df), staging_table_id)
        # Staging tables are always WRITE_TRUNCATE
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )
        job = client.load_table_from_dataframe(df, staging_table_id, job_config=job_config)
        job.result()
        
        # Construct MERGE query
        keys = spec["keys"]
        columns = spec["columns"]
        
        join_cond = " AND ".join([f"T.{k} = S.{k}" for k in keys])
        update_cols = [c for c in columns if c not in keys and c != "_created_at"]
        update_set = ", ".join([f"T.{c} = S.{c}" for c in update_cols])
        
        insert_cols_str = ", ".join(columns)
        insert_vals_str = ", ".join([f"S.{c}" for c in columns])
        
        merge_query = f"""
        MERGE `{target_table_id}` T
        USING `{staging_table_id}` S
        ON {join_cond}
        WHEN MATCHED THEN
          UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
          INSERT ({insert_cols_str})
          VALUES ({insert_vals_str})
        """
        
        logger.info("Executing BigQuery MERGE for target table %s...", target_table_id)
        query_job = client.query(merge_query)
        query_job.result()
        
        # Drop staging table
        client.delete_table(staging_table_id)
        logger.info("Successfully merged staging data and dropped staging table %s.", staging_table_name)
    except Exception as e:
        # Check if DML/billing is disabled (free-tier constraint)
        if "billingNotEnabled" in str(e) or "Billing has not been enabled" in str(e):
            logger.warning("Billing is disabled on this Google Cloud project. DML/MERGE is blocked in the free tier.")
            logger.warning("Falling back to loading directly via standard append load (WRITE_APPEND)...")
            
            # Clean up staging table if it was created
            try:
                client.delete_table(staging_table_id, not_found_ok=True)
            except Exception:
                pass
                
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND"
            )
            job = client.load_table_from_dataframe(df, target_table_id, job_config=job_config)
            job.result()
            logger.info("Successfully loaded %d rows directly to %s using WRITE_APPEND fallback.", len(df), table_name)
        else:
            raise e


def load_clean_data(full_reload: bool = False) -> bool:
    """Load local clean CSV files into BigQuery.

    Args:
        full_reload: If True, uses WRITE_TRUNCATE (overwrites). If False, uses SQL MERGE.

    Returns:
        True if all files loaded successfully, False otherwise.
    """
    processed_dir = Path(os.getenv("PROCESSED_DATA_PATH", "./data/processed/"))
    config = load_config()
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

        # Handle date/time conversions explicitly to prevent PyArrow object-datatype errors
        if table_name == "dim_date":
            df_filtered["full_date"] = pd.to_datetime(df_filtered["full_date"]).dt.date
        elif table_name == "dim_bank":
            # Avoid Pandas BoundDatetime nanosecond limits (max year 2262) by using timezone-agnostic datetime.date objects
            df_filtered["valid_from"] = pd.to_datetime(df_filtered["valid_from"], errors="coerce").dt.date
            df_filtered["valid_to"] = pd.to_datetime(df_filtered["valid_to"], errors="coerce").dt.date
            # Re-fill the out of bounds target date
            df_filtered["valid_to"] = df_filtered["valid_to"].fillna(datetime.date(9999, 12, 31))
        elif table_name == "dim_trading_session":
            df_filtered["start_time"] = pd.to_datetime(df_filtered["start_time"], format="%H:%M:%S").dt.time
            df_filtered["end_time"] = pd.to_datetime(df_filtered["end_time"], format="%H:%M:%S").dt.time

        # Explicitly cast system audit columns to datetime64[ns] to avoid PyArrow object translation errors
        if "_created_at" in df_filtered.columns:
            df_filtered["_created_at"] = pd.to_datetime(df_filtered["_created_at"])
        if "_updated_at" in df_filtered.columns:
            df_filtered["_updated_at"] = pd.to_datetime(df_filtered["_updated_at"])

        # Fetch audit parameters from the dataframe if present, else fallback
        audit_keys = df_filtered["audit_key"].dropna().unique()
        audit_key = int(audit_keys[0]) if len(audit_keys) > 0 else int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        run_id = str(uuid.uuid4())
        source_filename = str(df_filtered["_source_file"].dropna().unique()[0]) if "_source_file" in df_filtered.columns and len(df_filtered["_source_file"].dropna().unique()) > 0 else spec["file"]

        # Register run starting in dim_audit
        log_audit_run(client, config.bq_dataset_id, audit_key, run_id, f"load_to_bigquery:{table_name}", source_filename, len(df_filtered), "RUNNING")

        try:
            full_table_id = get_full_table_id(table_name)
            if full_reload:
                logger.info("Executing FULL RELOAD (WRITE_TRUNCATE) on table %s...", table_name)
                job_config = bigquery.LoadJobConfig(
                    write_disposition="WRITE_TRUNCATE"
                )
                job = client.load_table_from_dataframe(df_filtered, full_table_id, job_config=job_config)
                job.result()
                logger.info("Loaded %d rows into %s successfully.", len(df_filtered), full_table_id)
            else:
                logger.info("Executing INCREMENTAL MERGE load on table %s...", table_name)
                load_incremental_via_merge(df_filtered, table_name, client, config.bq_dataset_id, spec)
                
            # Log success status in dim_audit
            log_audit_run(client, config.bq_dataset_id, audit_key, run_id, f"load_to_bigquery:{table_name}", source_filename, len(df_filtered), "SUCCESS")
        except Exception as e:
            logger.error("Failed to load table %s into BigQuery: %s", table_name, str(e))
            log_audit_run(client, config.bq_dataset_id, audit_key, run_id, f"load_to_bigquery:{table_name}", source_filename, len(df_filtered), "FAILED")
            success = False

    return success


def main() -> int:
    parser = argparse.ArgumentParser(description="Load clean CSVs into BigQuery.")
    parser.add_argument(
        "--full-reload",
        action="store_true",
        help="Perform a full reload (WRITE_TRUNCATE) instead of an incremental MERGE.",
    )
    args = parser.parse_args()

    load_dotenv()
    
    try:
        success = load_clean_data(full_reload=args.full_reload)
        return 0 if success else 1
    except Exception as e:
        logger.exception("An unhandled exception occurred during BigQuery load: %s", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
