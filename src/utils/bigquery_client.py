"""Shared BigQuery client factory.

Reads GOOGLE_APPLICATION_CREDENTIALS from environment.
See docs/env-config.md for setup instructions.
"""

from google.cloud import bigquery

from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_bigquery_client() -> bigquery.Client:
    """Create and return a BigQuery client using project-level credentials.

    The client automatically uses the GOOGLE_APPLICATION_CREDENTIALS
    environment variable for authentication.

    Returns:
        An authenticated BigQuery Client instance.

    Raises:
        EnvironmentError: If GCP_PROJECT_ID is not configured.
    """
    config = load_config()
    client = bigquery.Client(project=config.gcp_project_id)
    logger.info(
        "BigQuery client initialized for project '%s'.",
        config.gcp_project_id,
    )
    return client


def get_full_table_id(table_name: str) -> str:
    """Return the fully qualified BigQuery table identifier.

    Args:
        table_name: The short table name, such as 'fact_price_history'.

    Returns:
        A string in the format 'project.dataset.table'.
    """
    config = load_config()
    return f"{config.gcp_project_id}.{config.bq_dataset_id}.{table_name}"
