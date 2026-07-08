"""Script to drop existing BigQuery tables and run provisioning to solve schema mismatches.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.bigquery_client import get_bigquery_client
from src.utils.config import load_config
from src.etl.provision_schema import provision_schema

def main():
    load_dotenv()
    config = load_config()
    client = get_bigquery_client()
    
    tables = [
        "fact_stock_daily_metrics",
        "fact_bank_performance",
        "dim_date",
        "dim_stock",
        "dim_bank",
        "dim_trading_session",
        "dim_audit",
        "bank_cluster_assignments",
        "bank_risk_predictions",
        "fact_model_predictions"
    ]
    
    dataset_id = config.bq_dataset_id
    project_id = os.getenv("GCP_PROJECT_ID")
    
    print(f"Dropping existing tables in dataset {project_id}.{dataset_id}...")
    for table_name in tables:
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        try:
            client.delete_table(table_ref, not_found_ok=True)
            print(f"Dropped table: {table_name}")
        except Exception as e:
            print(f"Failed to drop table {table_name}: {e}")
            
    print("\nRunning provision_schema to recreate core tables...")
    success = provision_schema()
    if success:
        print("Tables successfully recreated.")
    else:
        print("Failed to recreate tables.")

if __name__ == "__main__":
    main()
