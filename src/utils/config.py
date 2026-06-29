import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file at the root of the project
load_dotenv()

@dataclass(frozen=True)
class ConfigClass:
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    BQ_DATASET_ID: str = os.getenv("BQ_DATASET_ID", "financial_dwh")
    RAW_DATA_PATH: str = os.getenv("RAW_DATA_PATH", "./data/raw/")
    PROCESSED_DATA_PATH: str = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    MODEL_ARTIFACT_PATH: str = os.getenv("MODEL_ARTIFACT_PATH", "./reports/models/")
    BQ_PREDICTIONS_TABLE: str = os.getenv("BQ_PREDICTIONS_TABLE", "fact_model_predictions")

Config = ConfigClass()
