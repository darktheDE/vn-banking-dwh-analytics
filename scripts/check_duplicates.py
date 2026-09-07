"""Verify primary key uniqueness across all BigQuery tables.

Part of Phase R2 refactor (Issue B-01 / ADR-0001).
Queries each table in the dataset to verify that primary keys have no duplicates.

Usage:
    python scripts/check_duplicates.py

Exit code:
    0 - All tables have zero duplicates (PASS).
    1 - At least one table has duplicate primary keys (FAIL).
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
from google.cloud import bigquery

from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CREDENTIALS = "./vn-banking-dwh-analytics-67f213ad7317.json"
DEFAULT_PROJECT_ID = "vn-banking-dwh-analytics"
DEFAULT_DATASET_ID = "financial_dwh"

# Definition of primary keys per table
TABLE_PRIMARY_KEYS: Dict[str, List[str]] = {
    "dim_date": ["date_key"],
    "dim_stock": ["stock_key"],
    "dim_bank": ["bank_key", "valid_from"],
    "dim_trading_session": ["session_key"],
    "fact_stock_daily_metrics": ["date_key", "stock_key"],
    "fact_bank_performance": ["date_key", "bank_key"],
    "bank_cluster_assignments": ["bank_key"],
    "bank_risk_predictions": ["bank_key", "date_key"],
    "fact_model_predictions": ["base_date_key", "stock_key", "model_name", "horizon"],
}


def _resolve_credentials() -> None:
    """Ensure Google application credentials path is set."""
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = DEFAULT_CREDENTIALS


def check_table_duplicates(
    client: bigquery.Client, dataset_id: str, table_name: str, keys: List[str]
) -> Tuple[str, int, int]:
    """Query a table and check for duplicate keys.

    Returns:
        (table_name, total_rows, duplicate_count)
    """
    key_cols = ", ".join(keys)
    query = f"""
    SELECT {key_cols}, COUNT(*) as cnt
    FROM `{dataset_id}.{table_name}`
    GROUP BY {key_cols}
    HAVING COUNT(*) > 1
    """
    try:
        # Check total rows
        count_query = f"SELECT COUNT(*) as total FROM `{dataset_id}.{table_name}`"
        total_rows = list(client.query(count_query).result())[0].total

        # Check dupes
        dup_rows = list(client.query(query).result())
        dup_count = len(dup_rows)
        return table_name, total_rows, dup_count
    except Exception as exc:
        logger.error("Failed to query %s.%s: %s", dataset_id, table_name, exc)
        return table_name, -1, -1


def run_checks() -> int:
    """Run duplicate checks for all configured tables."""
    load_dotenv()
    _resolve_credentials()

    project_id = os.getenv("GCP_PROJECT_ID", DEFAULT_PROJECT_ID)
    dataset_id = os.getenv("BQ_DATASET_ID", DEFAULT_DATASET_ID)

    logger.info("Initializing BigQuery duplicate check for dataset: %s.%s", project_id, dataset_id)
    client = bigquery.Client(project=project_id)

    print(f"Checking primary key uniqueness on {len(TABLE_PRIMARY_KEYS)} BigQuery tables...")
    print("=" * 80)

    has_failures = False
    for table_name, keys in TABLE_PRIMARY_KEYS.items():
        tbl, total_rows, dup_count = check_table_duplicates(client, dataset_id, table_name, keys)

        if dup_count == -1:
            status = "ERROR"
            has_failures = True
            msg = "Query failed / table not found"
        elif dup_count == 0:
            status = "PASS"
            msg = f"{total_rows:>7} rows, 0 duplicate keys"
        else:
            status = "FAIL"
            has_failures = True
            msg = f"{total_rows:>7} rows, {dup_count} DUPLICATE keys detected!"

        print(f"  [{status:<5}] {tbl:<30} {msg}")

    print("=" * 80)
    if has_failures:
        logger.error("Duplicate check FAILED. Investigate duplicate records above.")
        return 1

    logger.info("Duplicate check PASSED. All tables have 100% unique primary keys.")
    return 0


if __name__ == "__main__":
    sys.exit(run_checks())
