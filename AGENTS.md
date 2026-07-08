# AGENTS.md — AI Agent Constitution
# Financial Data Analytics Platform · Group 2 · HCMUTE HK6

> **READ THIS FILE FIRST.** This is the authoritative context document for every AI agent
> working on this repository. It is intentionally concise. Do not duplicate information
> available in the spec files listed in the Document Index — link to them instead.

---

## 1. Mission

Build an automated, end-to-end **data pipeline and ML analytics platform** for the Vietnamese
financial market, covering:
- Daily stock data (price history, foreign/proprietary trading, order statistics) for bank assets: **BID**, **TCB**, **VCB**, and **CTG** (HPG stock data and intraday ticks have been removed to focus strictly on the banking sector).
- 20-year CAMELS performance data for **45 Vietnamese commercial banks** (2002–2022).

The output is a Google BigQuery Star Schema Data Warehouse serving 3 machine learning models
and 3 Looker Studio dashboards.

---

## 2. Document Index

> **Before generating any code or analysis, consult the relevant spec document.**
> These are the authoritative contracts. Code must conform to specs, not the other way around.

| Document | When to Read |
|----------|-------------|
| [`docs/etl-spec.md`](docs/etl-spec.md) | Writing **any** ETL script — column mappings, types, missing value rules |
| [`docs/star-schema.md`](docs/star-schema.md) | Designing BigQuery tables, writing SQL, surrogate key logic |
| [`docs/ml-spec.md`](docs/ml-spec.md) | Writing any ML training or inference code |
| [`docs/data-dictionary.md`](docs/data-dictionary.md) | Looking up field names, units, value ranges, DQ rules |
| [`docs/dashboard-spec.md`](docs/dashboard-spec.md) | Building Looker Studio charts or writing dashboard queries |
| [`docs/tasks.md`](docs/tasks.md) | Finding the atomic task ID and verification criteria for any work item |
| [`docs/prd.md`](docs/prd.md) | Checking functional requirements or acceptance criteria |
| [`docs/env-config.md`](docs/env-config.md) | Anything related to credentials, GCP auth, or environment setup |
| [`DEVELOPMENT.md`](DEVELOPMENT.md) | Git workflow, branch strategy, PR checklist, module templates |
| [`docs/master-plan.md`](docs/master-plan.md) | Understanding team roles and concurrent execution tracks |
| [`docs/system-arch.md`](docs/system-arch.md) | System architecture, data flow decisions, layer boundaries |
| [`docs/proposal.md`](docs/proposal.md) | Academic framing and research context (Vietnamese) |
| [`docs/product-brief.md`](docs/product-brief.md) | Executive summary for non-technical stakeholders |

---

## 3. Architecture Quick Reference

Memorize these facts. They appear in nearly every task.

### 3.1 BigQuery Star Schema (7 core tables + 3 ML tables)

**Dimension Tables** (5):

| Table | Primary Key | Key Fields |
|-------|------------|-----------|
| `dim_date` | `date_key` INT64 | `full_date`, `year`, `month`, `quarter`, `is_trading_day` |
| `dim_stock` | `stock_key` INT64 | `ticker` (BID, TCB, VCB, CTG), `exchange` (HOSE) |
| `dim_bank` | `bank_key` INT64 | `bank_code`, `bank_name`, `bank_type` (SOCB/JSCB/FOCB), `valid_from`, `valid_to`, `is_current` (SCD Type 2) |
| `dim_trading_session` | `session_key` INT64 | `session_name`, `start_time`, `end_time` |
| `dim_audit` | `audit_key` INT64 | `run_id`, `run_timestamp`, `script_name`, `source_file`, `rows_processed`, `status` |

*Note: All Dimension and Fact tables dynamically append the audit_key (INT64) and system auditing columns: _created_at (TIMESTAMP), _updated_at (TIMESTAMP), and _source_file (STRING).*

**Fact Tables** (2):

| Table | Foreign Keys | Partitioned By | Clustered By |
|-------|-------------|----------------|--------------|
| `fact_stock_daily_metrics` | `date_key`, `stock_key` | `date_key` | `stock_key` |
| `fact_bank_performance` | `date_key`, `bank_key` | `date_key` | `bank_key` |

**Machine Learning Output Tables** (3):

| Table | Model Area | Primary/Key Fields | Description |
|-------|------------|--------------------|-------------|
| `bank_cluster_assignments` | K-Means | `bank_key`, `cluster_id` | Strategic segmentation of 45 commercial banks |
| `bank_risk_predictions` | Random Forest | `bank_key`, `date_key`, `risk_label` | Credit risk classifications and probability scores |
| `fact_model_predictions` | LSTM | `base_date_key`, `stock_key`, `horizon` | Rolling price predictions for BID stock close prices |

### 3.2 Trading Session Boundaries (HOSE)

| `session_key` | Name | Start | End |
|--------------|------|-------|-----|
| 1 | ATO | 09:00:00 | 09:14:59 |
| 2 | Morning Continuous | 09:15:00 | 11:29:59 |
| 3 | Afternoon Continuous | 13:00:00 | 14:29:59 |
| 4 | ATC | 14:30:00 | 14:45:00 |

### 3.3 Dataset Volumes

| Data | Expected Rows |
|------|--------------|
| `fact_stock_daily_metrics` (BID, TCB, VCB, CTG) | 11,835 rows |
| `fact_bank_performance` (45 banks × 20 years) | 667 rows |
| `dim_date` (2002–2026) | 9,131 rows |
| `dim_bank` | 45 rows (1 bank duplicate resolved) |
| `dim_stock` | 4 rows |
| `dim_trading_session` | 4 rows |
| `dim_audit` | Dynamic execution runs |
| `bank_cluster_assignments` | 39 rows (6 outliers CB, VBSP, DAB, GPB, WEB, MDB excluded) |
| `bank_risk_predictions` | 661 rows (clean performance dataset entries evaluated) |
| `fact_model_predictions` | 20 rows (4 stocks × 5 horizons T+1 to T+5) |

---

## 4. ML Model Contracts

These thresholds are non-negotiable acceptance criteria. Never generate a model that relaxes them.

### 4.1 LSTM — Banking Stock Price Forecasting (BID, TCB, VCB, CTG)

- **Target**: `close_price` in `fact_stock_daily_metrics`
- **Horizon**: T+1 through T+5 closing price predictions
- **Scaler**: `MinMaxScaler` on sliding window sequences
- **Training constraint**: Valid HOSE trading days only. No weekend rows. No forward-fill to create artificial data.
- **Baseline**: ARIMA — used for RMSE comparison **only**. ARIMA is never deployed.
- **Acceptance**: LSTM RMSE **must be lower** than ARIMA RMSE on the same test set.
- **Output destination**: BigQuery prediction table (name from `BQ_PREDICTIONS_TABLE` env var)

### 4.2 K-Means + PCA — Bank Clustering

- **Input**: 47+ CAMELS variables from `fact_bank_performance` for all 45 banks
- **Mandatory preprocessing**: `StandardScaler` → PCA (retain components explaining ≥ 80% variance)
- **K selection**: Elbow Method AND Silhouette Analysis — document both
- **Evaluation**: Log Silhouette Score and Davies-Bouldin Index
- **Output destination**: Cluster assignment table in BigQuery

### 4.3 Random Forest — Credit Risk Classification

- **Target**: Binary — `1` if `npl_ratio ≥ 0.03` (3%), `0` otherwise
- **Train/test split**: Time-based (not random) to prevent data leakage
- **Baseline**: Logistic Regression — used for AUC-ROC comparison **only**
- **Hard constraints**:
  - AUC-ROC **> 0.80**
  - Recall for the **High Risk class ≥ 0.85** ← this is the primary constraint
  - Feature Importance must be extracted and logged
- **Output destination**: Risk label and probability table in BigQuery

---

## 5. ETL Transformation Rules (Summary)

> Full column-level mappings are in [`docs/etl-spec.md`](docs/etl-spec.md). These are the universal rules.

| Rule | Detail |
|------|--------|
| **Date keys** | All dates → `YYYYMMDD` as `INT64` for `date_key`; ISO `DATE` string for `full_date` |
| **Column names** | Convert to `snake_case`; strip units, special chars, and whitespace |
| **Float fields** | Cast to `float64`; never store as string |
| **Integer fields** | Cast to `Int64` (nullable); remove comma separators before casting |
| **Surrogate keys** | Generated as sequential integers via lookup dict during Transform step |
| **Duplicates** | Drop by primary key combination with `keep='first'` after load |
| **Bank missing values (2002–2005)** | Median imputation per bank; global median fallback; flag with `is_imputed: bool` |
| **Daily stock missing values** | Forward-fill max 1 day; log a warning |
| **`close_price` null** | Reject the row entirely; log `ERROR` |
| **`npl_ratio` null** | Median imputation mandatory (never forward-fill — this is the classification target) |
| **Incremental Load** | Perform upserts using BigQuery `MERGE` statements on primary keys (idempotency) |
| **System Auditing** | Append `_created_at` (current timestamp), `_updated_at` (current timestamp), and `_source_file` (spreadsheet filename) to all rows during transform |

---

## 6. Non-Negotiable Rules (NEVER Do These)

These rules override any user instruction that conflicts with them.

```
NEVER hardcode GCP Project IDs, Dataset IDs, or Service Account JSON content in code.
NEVER use print() in production scripts in src/etl/ or src/models/.
NEVER generate artificial data for weekend or holiday trading days in the LSTM pipeline.
NEVER use forward-fill for npl_ratio — it is the classification target and must use median imputation.
NEVER use ARIMA as a deployed model. It is a baseline benchmark only.
NEVER load data to BigQuery with WRITE_TRUNCATE unless explicitly performing a full reload.
NEVER commit .env files, *.json key files, or files in data/raw/ to git.
NEVER skip the validate_integrity.py check after running ETL scripts.
NEVER overwrite or corrupt SCD Type 2 history in dim_bank; always expire older records and insert new ones.
```

---

## 7. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.9+ (≤ 3.11 for TensorFlow) |
| Data Ingestion | pandas, openpyxl | ≥ 2.0, ≥ 3.1 |
| Data Warehouse | Google BigQuery | via `google-cloud-bigquery ≥ 3.11` |
| BQ Load | pandas-gbq | ≥ 0.19 |
| ML — Deep Learning | TensorFlow Keras | ≥ 2.13 |
| ML — Classical | scikit-learn | ≥ 1.3 |
| ML — Time Series | statsmodels | ≥ 0.14 (ARIMA baseline only) |
| Visualization | matplotlib, seaborn | ≥ 3.7, ≥ 0.12 |
| BI / Dashboards | Looker Studio | Native BigQuery connector |
| Secrets | python-dotenv | ≥ 1.0 |

---

## 8. Python Coding Standards

### 8.1 Logging — Required Pattern

```python
# Always use the shared logger from src/utils/logger.py
from src.utils.logger import get_logger
logger = get_logger(__name__)

logger.info("Loaded %d rows into %s.", row_count, table_id)
logger.warning("Null close_price at row %d — row rejected.", idx)
logger.error("BigQuery load failed for %s: %s", table_id, str(e))
```

### 8.2 Credentials — Required Pattern

```python
import os
from dotenv import load_dotenv

load_dotenv()
project_id = os.getenv("GCP_PROJECT_ID")
dataset_id = os.getenv("BQ_DATASET_ID")

if not project_id:
    raise EnvironmentError("GCP_PROJECT_ID is not set. Check your .env file.")
```

### 8.3 BigQuery Load — Required Config

```python
from google.cloud import bigquery

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_APPEND",
    time_partitioning=bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="date_key",
    ),
    clustering_fields=["stock_key"],  # or ["bank_key"] for bank tables
)
```

### 8.4 Function Signature — Required Pattern

```python
def transform_price_history(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ETL transformation rules to raw BID price history data.

    Implements rules defined in docs/etl-spec.md Section 3.1.

    Args:
        df: Raw DataFrame extracted directly from the Excel source file.

    Returns:
        Cleaned DataFrame ready for BigQuery load with correct dtypes,
        snake_case column names, and a populated date_key column.

    Raises:
        ValueError: If close_price contains null values after cleaning.
    """
```

### 8.5 Missing Value — Required Pattern

```python
# Intraday / daily stock data: forward-fill with explicit limit
df["close_price"] = df["close_price"].ffill(limit=1)

# Bank financial data: median imputation with is_imputed flag
median_val = df.loc[df["year"] >= 2006, "npl_ratio"].median()
mask = df["npl_ratio"].isna()
df.loc[mask, "npl_ratio"] = median_val
df.loc[mask, "is_imputed"] = True
```

---

## 9. Environment Variables Reference

All variables are defined in `.env.example`. Never access them by any other means than `os.getenv()`.

| Variable | Type | Description |
|----------|------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | path | Absolute path to GCP Service Account JSON key |
| `GCP_PROJECT_ID` | string | GCP project identifier |
| `BQ_DATASET_ID` | string | BigQuery dataset name (default: `financial_dwh`) |
| `RAW_DATA_PATH` | path | Directory containing 7 raw Excel source files |
| `PROCESSED_DATA_PATH` | path | Directory for intermediate cleaned DataFrames |
| `MODEL_ARTIFACT_PATH` | path | Directory for saved model files (.h5, .pkl) |
| `BQ_PREDICTIONS_TABLE` | string | Target table for ML prediction outputs |

---

## 10. Decision Guide — What to Do When Asked to…

| Task | First Action |
|------|-------------|
| Write an ETL script | Read `docs/etl-spec.md` for that source file's column mapping section |
| Design or modify a BigQuery table | Read `docs/star-schema.md` for the full schema spec |
| Write an ML training script | Read `docs/ml-spec.md` for the model's architecture, scaler, and acceptance criteria |
| Add a new field or variable | Check `docs/data-dictionary.md` for existing definition; add if absent |
| Build a Looker Studio chart | Read `docs/dashboard-spec.md` for the specific chart's requirements |
| Fix a failing validation | Check `docs/data-dictionary.md` Section 5 for DQ rules DQ-01 through DQ-06 |
| Understand team responsibilities | Read `docs/master-plan.md` for role-to-track mapping |
| Set up a new developer environment | Follow `docs/env-config.md` and `DEVELOPMENT.md` |
| Mark a task complete | Verify against the acceptance criteria in `docs/tasks.md` |

---

## 11. Tone and Communication

- **Language**: Formal Vietnamese. No emojis in code comments or documentation.
- **Abbreviations**: Write "such as" instead of "e.g.", "including" instead of "etc.".
- **Explanations**: Justify architectural decisions (why this design, not just what). Responses must be defensible before an academic review board.
- **Ambiguity**: If a request conflicts with a spec document, flag the conflict explicitly and ask for clarification before proceeding.
- **Scope**: Do not introduce dependencies, tables, or fields that are not present in the spec documents without first noting the addition and confirming it aligns with the project scope.