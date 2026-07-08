"""Script to drop obsolete mock tables (fact_price_history, fact_foreign_trading, fact_proprietary_trading, fact_order_stats) on BigQuery.
"""

from __future__ import annotations

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.bigquery_client import get_bigquery_client
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    load_dotenv()
    config = load_config()
    client = get_bigquery_client()
    
    obsolete_tables = [
        "fact_price_history",
        "fact_foreign_trading",
        "fact_proprietary_trading",
        "fact_order_stats"
    ]
    
    dataset_id = config.bq_dataset_id
    project_id = os.getenv("GCP_PROJECT_ID")
    
    logger.info("Dropping obsolete mock tables in dataset %s.%s...", project_id, dataset_id)
    
    for table_name in obsolete_tables:
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        try:
            client.delete_table(table_ref, not_found_ok=True)
            logger.info("Successfully dropped obsolete table: %s", table_name)
        except Exception as e:
            logger.error("Failed to drop table %s: %s", table_name, str(e))
            
    logger.info("Database cleanup completed.")

if __name__ == "__main__":
    main()
