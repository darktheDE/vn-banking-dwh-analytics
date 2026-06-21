# Implementation Task Checklist

> **Purpose**: This is the SDD Tasks layer document. Each item is an atomic, verifiable implementation step assigned to a specific role. Tasks must be completed in the order shown within each track. Cross-track dependencies are explicitly noted.
>
> **Status Legend**: `[ ]` Not started | `[/]` In progress | `[x]` Done

---

## Track A — Environment and Foundation Setup
*Owner: All members. No dependencies.*

- `[ ]` **A-01**: All members create and activate a Python 3.9+ virtual environment (`venv`).
  - *Verification*: `python --version` returns ≥ 3.9.
- `[ ]` **A-02**: Install all dependencies from `requirements.txt` (`pip install -r requirements.txt`).
  - *Verification*: `pip list` shows `pandas`, `openpyxl`, `scikit-learn`, `tensorflow`, `google-cloud-bigquery`, `python-dotenv`.
- `[ ]` **A-03**: Cloud Administrator creates a GCP Service Account with `BigQuery Data Editor` and `BigQuery Job User` roles. Export the JSON key.
  - *Verification*: JSON key file is accessible locally.
- `[ ]` **A-04**: All members configure `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to the JSON key.
  - *Verification*: `gcloud auth application-default print-access-token` succeeds.
- `[ ]` **A-05**: Create `.env` file from `.env.example`. Fill in `GCP_PROJECT_ID`, `BQ_DATASET_ID`, `RAW_DATA_PATH`, `PROCESSED_DATA_PATH`.
  - *File*: `.env` (gitignored), `.env.example` (committed).
- `[ ]` **A-06**: Commit the initialized project directory structure (`data/`, `notebooks/`, `src/`, `reports/`, `sql/`) to the repository.
  - *Verification*: Structure matches `README.md` Section 3.

---

## Track B — Data Engineering (ETL + DWH)
*Owner: Member 1 (ETL) and Member 2 (BigQuery). Depends on A-01 through A-06.*

### B-1: BigQuery Schema Provisioning (Member 2)

- `[ ]` **B-01**: Create the BigQuery Dataset using the `BQ_DATASET_ID` from `.env`.
  - *File*: `sql/bigquery_schema.sql`
  - *Verification*: Dataset visible in GCP Console.
- `[ ]` **B-02**: Create the 4 Dimension Tables (`dim_date`, `dim_stock`, `dim_bank`, `dim_trading_session`) using `bigquery_schema.sql`.
  - *Verification*: All 4 tables exist with correct schemas matching `docs/star-schema.md`.
- `[ ]` **B-03**: Create the 6 Fact Tables with partitioning and clustering as specified in `docs/star-schema.md` Section 5.
  - *Verification*: All 6 tables exist. `fact_intraday_matching` and `fact_price_history` have DAY partitioning on `date_key`. Stock fact tables have clustering on `stock_key`. Bank fact table has clustering on `bank_key`.

### B-2: Dimension Population (Member 1 or 2)

- `[ ]` **B-04**: Populate `dim_date` programmatically for range 2002-01-01 to 2026-12-31.
  - *File*: `src/etl/populate_dim_date.py`
  - *Verification*: Table row count ≈ 9,131 rows. `is_trading_day` column exists.
- `[ ]` **B-05**: Populate `dim_stock` with BID and HPG records (2 rows).
  - *File*: `src/etl/populate_dim_stock.py`
  - *Verification*: 2 rows in table.
- `[ ]` **B-06**: Populate `dim_bank` with 46 bank records from the raw CAMELS file.
  - *File*: `src/etl/populate_dim_bank.py`
  - *Verification*: 46 rows in table. No null `bank_code` values.
- `[ ]` **B-07**: Populate `dim_trading_session` with 4 session records per `docs/etl-spec.md` Section 4.4.
  - *Verification*: 4 rows in table.

### B-3: Fact Table ETL — Stock Data (Member 1)

- `[ ]` **B-08**: Implement ETL for File F3 → `fact_price_history` (22 rows for BID).
  - *File*: `src/etl/load_price_history.py`
  - *Rules*: `docs/etl-spec.md` Section 3.1.
  - *Verification*: 22 rows in table. No null `close_price`. Log confirms row count.
- `[ ]` **B-09**: Implement ETL for File F1 → `fact_foreign_trading` (22 rows for BID).
  - *File*: `src/etl/load_foreign_trading.py`
  - *Verification*: 22 rows. Log confirms load.
- `[ ]` **B-10**: Implement ETL for File F2 → `fact_proprietary_trading` (22 rows for BID).
  - *File*: `src/etl/load_proprietary_trading.py`
  - *Verification*: 22 rows. Log confirms load.
- `[ ]` **B-11**: Implement ETL for File F4 → `fact_order_stats` (22 rows for BID).
  - *File*: `src/etl/load_order_stats.py`
  - *Verification*: 22 rows. Log confirms load.
- `[ ]` **B-12**: Implement ETL for File F5 → `fact_intraday_matching` (~10,000 rows for HPG).
  - *File*: `src/etl/load_intraday_matching.py`
  - *Rules*: `docs/etl-spec.md` Section 3.5. Session classification must be applied.
  - *Verification*: Row count ≈ 10,000. No ticks outside valid HOSE hours. `cumulative_volume` is monotonically non-decreasing.

### B-4: Fact Table ETL — Bank Data (Member 1)

- `[ ]` **B-13**: Implement ETL for Files F6–F7 → `fact_bank_performance`.
  - *File*: `src/etl/load_bank_performance.py`
  - *Rules*: `docs/etl-spec.md` Section 3.6. Median imputation required for 2002–2005.
  - *Verification*: ~667 rows. No null values in CAMELS ratio columns after imputation. `is_imputed` flag column present. Log confirms row count.

### B-5: Integration Validation (Both members)

- `[ ]` **B-14**: Run end-to-end referential integrity check — all `date_key` values in fact tables must exist in `dim_date`.
  - *File*: `src/etl/validate_integrity.py`
  - *Verification*: Script exits with 0 errors logged.
- `[ ]` **B-15**: Run data quality checks per `docs/data-dictionary.md` Section 5 rules DQ-01 through DQ-06.
  - *Verification*: All DQ rules pass.

---

## Track C — Machine Learning (Member 3)
*Depends on B-08 through B-13 being complete.*

### C-1: Feature Engineering

- `[ ]` **C-01**: Query `fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading` from BigQuery. Merge into a single feature DataFrame for BID.
  - *File*: `src/models/feature_engineering_stock.py`
  - *Verification*: DataFrame has 22 rows, all columns from `docs/data-dictionary.md` Section 4 (derived features included).
- `[ ]` **C-02**: Query `fact_bank_performance` from BigQuery. Apply `StandardScaler` normalization to all CAMELS ratio features.
  - *File*: `src/models/feature_engineering_bank.py`
  - *Verification*: Scaled DataFrame has mean ≈ 0 and std ≈ 1 for all numeric columns.

### C-2: LSTM Time Series Forecasting

- `[ ]` **C-03**: Establish ARIMA and Moving Average baselines for BID `close_price`. Log RMSE.
  - *File*: `notebooks/03_ML_TimeSeries.ipynb` or `src/models/baseline_arima.py`
- `[ ]` **C-04**: Build and train the LSTM model on valid trading days only (no weekend data).
  - *File*: `src/models/train_lstm.py`
  - *Architecture*: Per `docs/ml-spec.md` Section 1. Use `MinMaxScaler` for sequence normalization.
  - *Verification*: RMSE and MAE logged. LSTM RMSE < ARIMA RMSE.
- `[ ]` **C-05**: Generate T+1 to T+5 predictions. Write results to BigQuery table `fact_model_predictions` (or equivalent).
  - *Verification*: Predictions table exists in BigQuery. Looker Studio can connect to it.

### C-3: K-Means Clustering with PCA

- `[ ]` **C-06**: Apply PCA to the scaled bank feature matrix. Determine optimal number of components for ≥80% explained variance.
  - *File*: `src/models/train_kmeans.py`
  - *Verification*: Cumulative explained variance plot logged. Component count documented.
- `[ ]` **C-07**: Apply K-Means. Determine optimal `k` using the Elbow Method and Silhouette Analysis.
  - *Verification*: Elbow and Silhouette plots saved to `reports/figures/`.
- `[ ]` **C-08**: Train final K-Means model. Compute Silhouette Score and Davies-Bouldin Index. Log both metrics.
  - *Verification*: Both metrics logged. Cluster assignments written to BigQuery.

### C-4: Random Forest Classification

- `[ ]` **C-09**: Establish Logistic Regression baseline for NPL ≥ 3% classification. Log AUC-ROC.
  - *File*: `src/models/baseline_logistic.py`
- `[ ]` **C-10**: Train Random Forest classifier. Apply time-based train/test split.
  - *File*: `src/models/train_random_forest.py`
  - *Verification*: AUC-ROC > 0.80. Recall for High Risk class ≥ 85%. Both metrics logged.
- `[ ]` **C-11**: Extract and log Feature Importance. Save bar chart to `reports/figures/`.
  - *Verification*: Feature importance values written to log. Chart saved.
- `[ ]` **C-12**: Write classification predictions and risk labels to BigQuery.
  - *Verification*: Prediction table exists and is queryable.

---

## Track D — Business Intelligence (Member 4)
*Depends on C-05, C-08, and C-12 being complete.*

- `[ ]` **D-01**: Connect Looker Studio to the BigQuery Dataset using the Native Connector.
  - *Verification*: Connection established without errors. All Fact and Dimension tables visible.
- `[ ]` **D-02**: Build the **Market Movement** dashboard page.
  - *Charts*: Line chart of actual vs LSTM-predicted `close_price`. Bar chart of `foreign_net_volume` and `prop_net_volume` by date.
  - *Filters*: Date range, Stock Ticker.
  - *Acceptance*: Per `docs/dashboard-spec.md` Section 2.
- `[ ]` **D-03**: Build the **Bank Profiling** dashboard page.
  - *Charts*: Scatter plot of PCA components colored by cluster. Radar chart of CAMELS ratios per cluster.
  - *Filters*: Bank Name, Bank Type (SOCB / JSCB / FOCB), Cluster ID.
  - *Acceptance*: Per `docs/dashboard-spec.md` Section 3.
- `[ ]` **D-04**: Build the **Risk Monitoring** dashboard page.
  - *Charts*: Risk classification table with color-coded risk labels. NPL ratio trend line per bank.
  - *Filters*: Bank Name, Year, Risk Category.
  - *Acceptance*: Per `docs/dashboard-spec.md` Section 4.
- `[ ]` **D-05**: End-to-end integration test — confirm all dashboard charts render correctly from live BigQuery data without manual CSV uploads.
  - *Verification*: All 3 dashboard pages load without errors. Non-technical team members can operate filters without SQL.

---

## Definition of Done

The project is officially complete when **all** of the following are true:

- `[ ]` ETL pipeline runs without errors and all 10 BigQuery tables are populated.
- `[ ]` Data quality validation (B-14, B-15) passes with zero critical errors.
- `[ ]` LSTM RMSE is lower than the ARIMA baseline.
- `[ ]` Random Forest achieves AUC-ROC > 0.80 and Recall ≥ 85% for the High Risk class.
- `[ ]` K-Means Silhouette Score is logged and clusters are interpretable.
- `[ ]` All 3 Looker Studio dashboard pages render from live BigQuery data.
- `[ ]` All ML model metrics are logged to the Python `logging` system (no bare `print()` statements).
