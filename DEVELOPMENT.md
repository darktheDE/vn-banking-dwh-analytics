# DEVELOPMENT.md — Developer Guide

> This document is intended for all team members actively contributing code to the Financial Data Analytics Platform. It covers environment setup, coding standards, Git workflow, and module architecture.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Project Architecture Overview](#3-project-architecture-overview)
4. [Coding Standards](#4-coding-standards)
5. [Git Workflow](#5-git-workflow)
6. [Module Development Guide](#6-module-development-guide)
7. [Testing and Validation](#7-testing-and-validation)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

Ensure the following tools are installed before beginning:

| Tool | Minimum Version | Installation |
|------|-----------------|-------------|
| Python | 3.9+ | [python.org](https://python.org) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |
| Google Cloud SDK (`gcloud`) | Latest | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |
| JupyterLab | Latest | Via `pip install jupyterlab` |

---

## 2. Environment Setup

### 2.1 Clone and Initialize

```bash
git clone https://github.com/darktheDE/vn-banking-dwh-analytics.git
cd vn-banking-dwh-analytics
```

### 2.2 Python Virtual Environment

Always work inside a virtual environment to prevent dependency conflicts.

```bash
# Create virtual environment
python -m venv venv

# Activate — Windows (PowerShell)
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 2.3 Environment Variables

```bash
# Copy the template
copy .env.example .env

# Edit .env with your actual values
notepad .env
```

Your `.env` must include all of the following:

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Absolute path to your GCP Service Account JSON key | `C:\keys\sa-key.json` |
| `GCP_PROJECT_ID` | Your GCP Project ID | `financial-analytics-g02` |
| `BQ_DATASET_ID` | BigQuery dataset name | `financial_dwh` |
| `RAW_DATA_PATH` | Relative path to raw data folder | `./data/raw/` |
| `PROCESSED_DATA_PATH` | Relative path to processed data folder | `./data/processed/` |
| `MODEL_ARTIFACT_PATH` | Path to save trained model files | `./reports/models/` |
| `BQ_PREDICTIONS_TABLE` | BigQuery table for ML output | `fact_model_predictions` |

### 2.4 Verify BigQuery Connection

```python
from dotenv import load_dotenv
from src.utils.bigquery_client import get_bigquery_client

load_dotenv()
client = get_bigquery_client()
print(client.project)  # Should print your GCP_PROJECT_ID
```

### 2.5 Run the Streamlit Dashboard App

To run the interactive analytics dashboard locally, execute the following command from the project root:
```bash
# Start Streamlit application
streamlit run src/dashboard/app.py
```
This command spins up a local web server and automatically opens the dashboard interface in your web browser (defaulting to `http://localhost:8501`).

---

## 3. Project Architecture Overview

```
vn-banking-dwh-analytics/
│
├── src/etl/         ← Batch ETL scripts (Extract → Transform → Load)
├── src/models/      ← ML training, inference, and BigQuery write-back
├── src/dashboard/   ← Streamlit interactive dashboard application
├── src/utils/       ← Shared: logger, BigQuery client, config loader
├── notebooks/       ← Jupyter notebooks (prototyping and EDA only)
├── data/raw/        ← Source Excel files (NOT committed to git)
├── sql/             ← BigQuery DDL for schema provisioning
├── docs/            ← All project specifications and documentation
```

### Data Flow

```
data/raw/*.xlsx
    │
    ▼  (src/etl/ using BigQuery MERGE/load with SCD Type 2)
Google BigQuery (Star Schema: 5 Dims + 2 Facts + 3 ML Tables + Audit Metadata)
    │
    ├─▶ (src/models/) ──▶ ML Predictions (written back to BQ)
    │
    ├─▶ (Looker Studio) ──▶ BI Dashboards
    └─▶ (src/dashboard/) ──▶ Interactive Streamlit Web Application
```

---

## 4. Coding Standards

All code in `src/` must adhere to these standards, as defined in `AGENTS.md`.

### 4.1 Logging — Never Use `print()`

```python
# ✅ CORRECT — use the shared logger
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Loaded %d rows into fact_stock_daily_metrics.", row_count)
logger.warning("Missing close_price for date %s — row rejected.", date_str)
logger.error("BigQuery load failed: %s", str(e))

# ❌ WRONG — bare print statements are prohibited in production scripts
print(f"Loaded {row_count} rows")
```

### 4.2 Type Hints and Docstrings

Every function and class must include full type annotations and a Google-style docstring.

```python
import pandas as pd
from google.cloud import bigquery


def load_incremental_to_bigquery(
    df: pd.DataFrame,
    table_id: str,
    client: bigquery.Client,
    primary_keys: list[str],
) -> int:
    """Load a cleaned DataFrame incrementally into BigQuery using a MERGE query.

    Ensures idempotency by updating existing records and inserting new ones
    based on the primary keys. Also populates system auditing columns.

    Args:
        df: Cleaned and transformed DataFrame.
        table_id: Fully qualified BigQuery table ID in the format
            'project.dataset.table'.
        client: An authenticated BigQuery client instance.
        primary_keys: Key columns for the MERGE join condition.

    Returns:
        The number of rows successfully processed.
    """
    # System audit columns are appended dynamically:
    # df["_created_at"] = pd.Timestamp.now()
    # df["_updated_at"] = pd.Timestamp.now()
    # df["_source_file"] = source_filename
    ...
    # MERGE INTO target USING staging ON join_condition
    # WHEN MATCHED THEN UPDATE ...
    # WHEN NOT MATCHED THEN INSERT ...
    return len(df)
```

### 4.3 No Hardcoded Credentials

```python
# ✅ CORRECT
import os
project_id = os.getenv("GCP_PROJECT_ID")

# ❌ WRONG — never commit secrets
project_id = "my-actual-project-id"
```

### 4.4 Missing Value Handling

| Data Type | Strategy | Reference |
|-----------|----------|-----------|
| Bank financial ratios 2002–2005 | Column-median imputation | `docs/etl-spec.md` §3.6 |
| Daily BID data (price, foreign, prop) | Forward-fill, max 1 day | `docs/etl-spec.md` §3.1–3.3 |
| Critical fields (`close_price`, `npl_ratio`) | Reject row; log error | `docs/data-dictionary.md` §5 |
| System Audit Columns | Append `_created_at`, `_updated_at`, and `_source_file` | `docs/star-schema.md` §5 |

### 4.5 DataFrame Best Practices

```python
# Use explicit dtypes when reading Excel to avoid silent type coercion
df = pd.read_excel(
    path,
    dtype={"Volume": "Int64", "Close": "float64"},
    parse_dates=["Date"],
)

# Always validate column presence before transformation
required_cols = {"Date", "Close", "Volume"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Source file missing required columns: {missing}")
```

---

## 5. Git Workflow

### 5.1 Branch Strategy

```
main                ← Production-ready code only
├── develop         ← Integration branch — all features merge here first
│   ├── feature/etl-price-history     ← Trần Minh Khánh, Nguyễn Đặng Quốc Anh & Đỗ Kiến Hưng feature branches
│   ├── feature/lstm-training         ← Phạm Minh Quân & Nguyễn Đặng Quốc Anh feature branches
│   └── feature/dashboard-risk-page   ← Đỗ Kiến Hưng & Phạm Minh Quân feature branches
```

### 5.2 Branch Naming Convention

```
feature/<short-description>    # New feature
fix/<short-description>        # Bug fix
refactor/<short-description>   # Code refactoring (no behavior change)
docs/<short-description>       # Documentation update only
```

Examples:
```
feature/load-bank-performance
feature/lstm-minmaxscaler-windows
fix/intraday-session-classification
docs/update-etl-spec
```

### 5.3 Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

Types: feat | fix | refactor | docs | test | chore
Scope: etl | models | utils | sql | notebooks | docs

Examples:
feat(etl): add median imputation for 2002-2005 bank data
fix(models): correct MinMaxScaler inverse transform in LSTM inference
docs(star-schema): add npl_ratio field description
refactor(utils): extract BigQuery client to singleton factory
```

### 5.4 Pull Request Rules

Before opening a PR to `develop`:
- `[ ]` All logging uses `get_logger()` — no bare `print()` calls
- `[ ]` All functions have type hints and docstrings
- `[ ]` No `.env` or service account JSON files staged in the commit
- `[ ]` `validate_integrity.py` passes (if ETL changes were made)
- `[ ]` Row counts are logged in all ETL load functions

---

## 6. Module Development Guide

### 6.1 Writing a New ETL Script

Each ETL script in `src/etl/` must follow this structure:

```python
"""Module: load_price_history.py

ETL script to extract BID OHLCV data from the raw Excel source,
apply transformation rules per docs/etl-spec.md Section 3.1,
and load the cleaned records into the fact_price_history BigQuery table.
"""

import logging
from pathlib import Path
import pandas as pd
from google.cloud import bigquery

from src.utils.logger import get_logger
from src.utils.bigquery_client import get_bigquery_client
from src.utils.config import Config

logger = get_logger(__name__)


def extract(source_path: Path) -> pd.DataFrame:
    """Extract raw price history data from the Excel source file."""
    ...


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Apply cleaning, normalization, and surrogate key mapping."""
    ...


def load(df: pd.DataFrame, client: bigquery.Client) -> int:
    """Load the cleaned DataFrame into BigQuery. Returns row count."""
    ...


def main() -> None:
    """Execute the full ETL pipeline for fact_price_history."""
    logger.info("Starting ETL: fact_price_history")
    df_raw = extract(Path(Config.RAW_DATA_PATH) / "BID_price_history.xlsx")
    df_clean = transform(df_raw)
    rows = load(df_clean, get_bigquery_client())
    logger.info("ETL complete: %d rows loaded into fact_price_history.", rows)


if __name__ == "__main__":
    main()
```

### 6.2 Writing a New ML Training Script

```python
"""Module: train_random_forest.py

Trains a Random Forest classifier to predict bank credit risk
(NPL >= 3% threshold) per docs/ml-spec.md Section 3.

Acceptance criteria:
  - AUC-ROC > 0.80
  - Recall for High Risk class >= 0.85
"""

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_features() -> tuple:
    """Query CAMELS features from BigQuery. Returns (X, y)."""
    ...


def train(X_train, y_train):
    """Train Random Forest with hyperparameter tuning."""
    ...


def evaluate(model, X_test, y_test) -> dict:
    """Compute AUC-ROC, F1-Score, and Recall per class. Log all metrics."""
    ...


def write_predictions_to_bigquery(model, X, bank_ids) -> None:
    """Write risk labels and probabilities back to BigQuery."""
    ...


def main() -> None:
    logger.info("Starting Random Forest training.")
    X, y = load_features()
    # ... train, evaluate, write back
    logger.info("Random Forest training complete.")
```

---

## 7. Testing and Validation

### 7.1 ETL Validation Checklist

After running any ETL script, run the integrity validator:

```bash
python -m src.etl.validate_integrity
```

This script checks:
- All `date_key` values in fact tables reference a valid row in `dim_date`
- `npl_ratio` values are in the range [0.0, 1.0]
- `close_price` values are strictly positive
- No null values remain in any CAMELS ratio column after imputation

### 7.2 Model Acceptance Validation

After training a model, confirm these minimum acceptance criteria are logged:

| Model | Metric | Minimum |
|-------|--------|---------|
| LSTM | RMSE vs ARIMA | LSTM RMSE < ARIMA RMSE |
| Random Forest | AUC-ROC | > 0.80 |
| Random Forest | Recall (High Risk) | ≥ 0.85 |
| K-Means | Silhouette Score | Logged and > 0 |

### 7.3 Notebook Validation

Before committing a notebook:
1. Restart the kernel and run all cells from top to bottom
2. Confirm all cells execute without errors
3. Confirm all BigQuery queries use environment variables — no hardcoded project IDs

---

## 8. Troubleshooting

### `DefaultCredentialsError` when connecting to BigQuery

**Cause**: `GOOGLE_APPLICATION_CREDENTIALS` is not set or the path is wrong.

**Fix**:
```powershell
# Windows PowerShell (set per-session)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account.json"

# Verify
python -c "from google.cloud import bigquery; print(bigquery.Client().project)"
```

### `ModuleNotFoundError: No module named 'src'`

**Cause**: Running scripts from a subdirectory instead of the project root, so Python cannot resolve the `src` package.

**Fix**: Always run from the repository root:
```bash
# ✅ Correct — run from project root
python -m src.etl.load_price_history

# ❌ Wrong — do not cd into src/ first
cd src/etl && python load_price_history.py
```

### BigQuery `403 Forbidden` on load

**Cause**: The Service Account lacks the required IAM roles.

**Fix**: The Cloud Administrator must grant both `BigQuery Data Editor` and `BigQuery Job User` roles to the Service Account in the GCP IAM console. `BigQuery Data Viewer` alone is insufficient for writes.

### `tensorflow` not found after `pip install -r requirements.txt`

**Cause**: TensorFlow 2.13+ requires Python ≤ 3.11. Python 3.12+ is not supported by this version.

**Fix**: Use Python 3.9, 3.10, or 3.11. Verify with `python --version` before installing.

### Looker Studio dashboard shows "Data source error"

**Cause**: The Google Account used to create the Looker Studio report does not have BigQuery Data Viewer access on the dataset.

**Fix**: The Cloud Administrator must grant `BigQuery Data Viewer` at the dataset level to the team member's Google Account in GCP IAM.

---

*For project architecture and feature specifications, refer to the [Documentation Index](README.md#-documentation-index) in `README.md`.*
