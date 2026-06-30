"""Task B-02 / B-03: BigQuery Star Schema Provisioning.

Reads DDL statements from sql/bigquery_schema.sql and executes them
on BigQuery to provision all Dimension and Fact tables.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from src.utils.bigquery_client import get_bigquery_client
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def provision_schema() -> bool:
    """Read sql/bigquery_schema.sql and execute the DDL queries.

    Returns:
        True if all DDL queries executed successfully, False otherwise.
    """
    config = load_config()
    client = get_bigquery_client()

    sql_file = Path("sql/bigquery_schema.sql")
    if not sql_file.exists():
        logger.error("DDL schema file not found at: %s", sql_file)
        return False

    logger.info("Reading DDL statements from %s", sql_file)
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Resolve dataset placeholder
    sql_resolved = sql_content.replace("{dataset_id}", config.bq_dataset_id)

    # Split queries by semicolon to execute them individually
    # Filter out empty queries
    queries = [q.strip() for q in sql_resolved.split(";") if q.strip()]

    logger.info("Starting schema provisioning in dataset '%s'...", config.bq_dataset_id)
    success = True

    for i, query in enumerate(queries, 1):
        # Extract the table name or operation type for logging
        first_line = query.split("\n")[0]
        logger.info("Executing DDL query [%d/%d]: %s...", i, len(queries), first_line)

        try:
            query_job = client.query(query)
            query_job.result()  # Wait for the job to complete
            logger.info("Query [%d/%d] executed successfully.", i, len(queries))
        except Exception as e:
            logger.error("Failed to execute query [%d/%d]: %s", i, len(queries), str(e))
            success = False

    if success:
        logger.info("All Dimension and Fact tables have been provisioned successfully in BigQuery.")
    else:
        logger.error("Schema provisioning completed with errors.")

    return success


def main() -> int:
    load_dotenv()
    try:
        success = provision_schema()
        return 0 if success else 1
    except Exception as e:
        logger.exception("An unhandled exception occurred during schema provisioning: %s", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
