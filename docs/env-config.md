# Environment Configuration Guide

## 1. Overview

This document outlines the local and cloud environment setup required for all team members working on the Financial Data Analytics Platform. Standardizing the development environment ensures code consistency, prevents dependency conflicts, and secures cloud credentials across the Data Engineering, Machine Learning, and Visualization workflows.

---

## 2. Local Python Environment

### 2.1 Python Version

All team members must use **Python 3.9 or higher**.

### 2.2 Virtual Environment Setup

To isolate project dependencies, team members must create and activate a virtual environment before installing any Python packages.

**Using venv:**

```bash
# Create the virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS and Linux
source venv/bin/activate
```

### 2.3 Required Dependencies

Once the virtual environment is active, install the required libraries. The primary dependencies include:
- `pandas` and `openpyxl` for data extraction and transformation.
- `scikit-learn` for K-Means clustering, PCA, and Random Forest models.
- `tensorflow` for the LSTM time-series forecasting model.
- `google-cloud-bigquery` and `db-dtypes` for interacting with the Google Cloud Data Warehouse.
- `python-dotenv` for managing local environment variables securely.

Team members should install these via the project requirements file:

```bash
pip install -r requirements.txt
```

---

## 3. Google Cloud Authentication

### 3.1 Service Account Key

The Python ETL pipeline and ML models require programmatic access to Google BigQuery. Team members must never hardcode credentials into the Python scripts.
1. The Cloud Administrator must generate a Service Account JSON Key with **BigQuery Data Editor** and **BigQuery Job User** roles.
2. Distribute this JSON file securely to team members through encrypted channels.
3. Save the JSON file locally in a secure folder outside the public repository tracking.

### 3.2 Environment Variable Setup

Configure your operating system to recognize the Service Account key by setting the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

**On Windows PowerShell:**

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-file.json"
```

**On macOS and Linux:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-file.json"
```

---

## 4. Local Environment Variables

For project-specific configurations such as project IDs and dataset names, use a `.env` file at the root directory. This file must be added to `.gitignore` to prevent leaking configurations to GitHub.

A complete `.env.example` template is provided at the repository root. Copy it and fill in your values:

```bash
cp .env.example .env
```

**Full variable reference** (see `.env.example` for descriptions):

```
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-file.json
GCP_PROJECT_ID=your-gcp-project-id
BQ_DATASET_ID=financial_dwh
RAW_DATA_PATH=./data/raw/
PROCESSED_DATA_PATH=./data/processed/
MODEL_ARTIFACT_PATH=./reports/models/
BQ_PREDICTIONS_TABLE=fact_model_predictions
```

Inside the Python scripts, utilize the `python-dotenv` library to load these variables dynamically:

```python
from dotenv import load_dotenv
import os

load_dotenv()
project_id = os.getenv("GCP_PROJECT_ID")
```

---

## 5. Looker Studio Access Configuration

The Visualization Engineer requires specific access to build the interactive dashboards.
- Ensure the user’s Google Account is granted **BigQuery Data Viewer** access at the dataset level.
- When creating a new Looker Studio report, select the **BigQuery Native Connector**.
- Authenticate using the permitted Google Account, select the designated Project ID and Dataset, and connect directly to the defined Fact Tables and Dimension Tables.