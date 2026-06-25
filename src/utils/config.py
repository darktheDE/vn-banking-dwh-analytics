"""Configuration loader.

Reads all .env variables via os.getenv() using python-dotenv.
Exposes typed Config dataclass for use across all ETL and ML modules.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Immutable configuration container loaded from environment variables.

    Attributes:
        gcp_project_id: Google Cloud Platform project identifier.
        bq_dataset_id: BigQuery dataset name.
        credentials_path: Absolute path to the GCP Service Account JSON key.
        raw_data_path: Directory containing the raw Excel source files.
        processed_data_path: Directory for intermediate cleaned DataFrames.
        model_artifact_path: Directory for saved model files.
        bq_predictions_table: Target BigQuery table for ML prediction outputs.
    """

    gcp_project_id: str
    bq_dataset_id: str
    credentials_path: str
    raw_data_path: str
    processed_data_path: str
    model_artifact_path: str
    bq_predictions_table: str


def load_config() -> Config:
    """Load environment variables from .env and return a Config instance.

    Raises:
        EnvironmentError: If GCP_PROJECT_ID is not set.

    Returns:
        A populated Config dataclass.
    """
    load_dotenv()

    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    if not gcp_project_id:
        raise EnvironmentError(
            "GCP_PROJECT_ID is not set. Check your .env file."
        )

    return Config(
        gcp_project_id=gcp_project_id,
        bq_dataset_id=os.getenv("BQ_DATASET_ID", "financial_dwh"),
        credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        raw_data_path=os.getenv("RAW_DATA_PATH", "./data/raw/"),
        processed_data_path=os.getenv("PROCESSED_DATA_PATH", "./data/processed/"),
        model_artifact_path=os.getenv("MODEL_ARTIFACT_PATH", "./reports/models/"),
        bq_predictions_table=os.getenv(
            "BQ_PREDICTIONS_TABLE", "fact_model_predictions"
        ),
    )
