# Implementation Task Checklist

> **Purpose**: This is the SDD Tasks layer document. Each item is an atomic, verifiable implementation step assigned to a specific role. Tasks must be completed in the order shown within each track. Cross-track dependencies are explicitly noted.
>
> **Status Legend**: `[ ]` Not started | `[/]` In progress | `[x]` Done

---

## Track A — Environment and Foundation Setup
*Owner: All members. No dependencies.*

- `[x]` **A-01**: All members create and activate a Python 3.9+ virtual environment (`venv`).
  - *Verification*: `python --version` returns ≥ 3.9.
- `[x]` **A-02**: Install all dependencies from `requirements.txt` (`pip install -r requirements.txt`).
  - *Verification*: `pip list` shows `pandas`, `openpyxl`, `scikit-learn`, `tensorflow`, `google-cloud-bigquery`, `python-dotenv`.
- `[x]` **A-03**: Cloud Administrator creates a GCP Service Account with `BigQuery Data Editor` and `BigQuery Job User` roles. Export the JSON key.
  - *Verification*: JSON key file is accessible locally.
- `[x]` **A-04**: All members configure `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to the JSON key.
  - *Verification*: `gcloud auth application-default print-access-token` succeeds.
- `[x]` **A-05**: Create `.env` file from `.env.example`. Fill in `GCP_PROJECT_ID`, `BQ_DATASET_ID`, `RAW_DATA_PATH`, `PROCESSED_DATA_PATH`.
  - *File*: `.env` (gitignored), `.env.example` (committed).
- `[x]` **A-06**: Commit the initialized project directory structure (`data/`, `notebooks/`, `src/`, `reports/`, `sql/`) to the repository.
  - *Verification*: Structure matches `README.md` Section 3.


---

## Track B — Data Engineering (ETL + DWH)
*Owner: Trần Minh Khánh, Nguyễn Đặng Quốc Anh & Đỗ Kiến Hưng. Depends on A-01 through A-06.*

### B-1: BigQuery Schema Provisioning (Nguyễn Đặng Quốc Anh)

- `[x]` **B-01**: Create the BigQuery Dataset using the `BQ_DATASET_ID` from `.env`.
  - *File*: `sql/bigquery_schema.sql`
  - *Verification*: Dataset visible in GCP Console.
- `[x]` **B-01b**: Update `sql/bigquery_schema.sql` to include SCD Type 2 columns in `dim_bank` (`valid_from`, `valid_to`, `is_current`) and system auditing columns (`_created_at`, `_updated_at`, `_source_file`) in all tables.
  - *Verification*: Schema file matches the specification in `docs/star-schema.md`.
- `[x]` **B-01c**: Provision physical table `dim_audit` to log pipeline run execution metadata.
  - *Verification*: `dim_audit` exists in BigQuery.

- `[x]` **B-02**: Create the 4 Dimension Tables (`dim_date`, `dim_stock`, `dim_bank`, `dim_trading_session`) using `bigquery_schema.sql`.
  - *Verification*: All 4 tables exist with correct schemas matching `docs/star-schema.md`.
- `[x]` **B-03**: Create the 5 Fact Tables with partitioning and clustering as specified in `docs/star-schema.md` Section 5.
  - *Verification*: All 5 tables exist. `fact_price_history` has DAY partitioning on `date_key`. Stock fact tables have clustering on `stock_key`. Bank fact table has clustering on `bank_key`.

### B-2: Dimension Population (Trần Minh Khánh or Nguyễn Đặng Quốc Anh)

- `[x]` **B-04**: Populate `dim_date` programmatically for range 2002-01-01 to 2026-12-31.
  - *File*: `src/etl/populate_dim_date.py`
  - *Verification*: Table row count ≈ 9,131 rows. `is_trading_day` column exists.
- `[x]` **B-05**: Populate `dim_stock` with focus banks (BID, TCB, VCB, CTG) records (4 rows).
  - *File*: `src/etl/populate_dim_stock.py`
  - *Verification*: 4 rows in table.
- `[x]` **B-06**: Populate `dim_bank` with 46 bank records from the raw CAMELS file.
  - *File*: `src/etl/populate_dim_bank.py`
  - *Verification*: 46 rows in table. No null `bank_code` values.
- `[x]` **B-06b**: Implement SCD Type 2 historical comparison and update-insert flow in `populate_dim_bank.py`.
  - *Verification*: Changing bank charter capital in local csv creates a new version with updated valid windows, and sets `is_current = FALSE` for the old row.
- `[x]` **B-07**: Populate `dim_trading_session` with 4 session records per `docs/etl-spec.md` Section 4.4.
  - *Verification*: 4 rows in table.
- `[x]` **B-07b**: Update all ETL scripts under `src/etl/` to populate audit fields (`_created_at`, `_updated_at`, `_source_file`) dynamically during the transform step.
  - *Verification*: CSV outputs in `data/processed/` contain the populated system auditing columns.

### B-3: Fact Table ETL — Stock Data (Trần Minh Khánh)

- `[x]` **B-08**: Implement ETL for File F3 → `fact_price_history` (Consolidated daily history for BID, TCB, VCB, CTG - 11,835 rows).
  - *File*: `src/etl/load_price_history.py`
  - *Rules*: `docs/etl-spec.md` Section 3.1.
  - *Verification*: 11,835 rows in table. No null `close_price`. Log confirms row count.
- `[x]` **B-09**: Implement ETL for File F1 → `fact_foreign_trading` (22 rows for BID).
  - *File*: `src/etl/load_foreign_trading.py`
  - *Verification*: 22 rows. Log confirms load.
- `[x]` **B-10**: Implement ETL for File F2 → `fact_proprietary_trading` (22 rows for BID).
  - *File*: `src/etl/load_proprietary_trading.py`
  - *Verification*: 22 rows. Log confirms load.
- `[x]` **B-11**: Implement ETL for File F4 → `fact_order_stats` (22 rows for BID).
  - *File*: `src/etl/load_order_stats.py`
  - *Verification*: 22 rows. Log confirms load.

### B-4: Fact Table ETL — Bank Data (Trần Minh Khánh)

- `[x]` **B-13**: Implement ETL for Files F6–F7 → `fact_bank_performance`.
  - *File*: `src/etl/load_bank_performance.py`
  - *Rules*: `docs/etl-spec.md` Section 3.6. Median imputation required for 2002–2005.
  - *Verification*: ~667 rows. No null values in CAMELS ratio columns after imputation. `is_imputed` flag column present. Log confirms row count.
- `[x]` **B-13b**: Implement the BigQuery `MERGE` SQL upsert logic in `load_to_bigquery.py` to support incremental loading (rather than full truncation) for all tables.
  - *Verification*: Subsequent run logs indicate records were updated or ignored instead of creating duplicates.
- `[x]` **B-13c**: Implement a fallback ingestion path in `load_to_bigquery.py` using standard batch loads for projects where BigQuery DML/MERGE is blocked due to disabled billing.
  - *Verification*: Scripts load data correctly via fallback WRITE_APPEND and WRITE_TRUNCATE batch load jobs.

### B-5: Integration Validation (Both members)

- `[x]` **B-14**: Run end-to-end referential integrity check — all `date_key` values in fact tables must exist in `dim_date`.
  - *File*: `src/etl/validate_integrity.py`
  - *Verification*: Script exits with 0 errors logged.
- `[x]` **B-15**: Run data quality checks per `docs/data-dictionary.md` Section 5 rules DQ-01 through DQ-06.
  - *Verification*: All DQ rules pass.

---

## Track C — Machine Learning (Phạm Minh Quân & Nguyễn Đặng Quốc Anh)
*Depends on B-08 through B-13 being complete.*

### C-1: Feature Engineering

- `[x]` **C-01**: Query `fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading` from BigQuery. Merge into a single feature DataFrame for BID.
  - *File*: `src/models/feature_engineering_stock.py`
  - *Verification*: DataFrame has 22 rows, all columns from `docs/data-dictionary.md` Section 4 (derived features included).
- `[x]` **C-02**: Query `fact_bank_performance` from BigQuery. Apply `StandardScaler` normalization to all CAMELS ratio features.
  - *File*: `src/models/feature_engineering_bank.py`
  - *Verification*: Scaled DataFrame has mean ≈ 0 and std ≈ 1 for all numeric columns.

### C-2: LSTM Time Series Forecasting

- `[x]` **C-03**: Establish ARIMA and Moving Average baselines for BID `close_price`. Log RMSE.
  - *File*: `notebooks/03_ML_TimeSeries.ipynb` or `src/models/baseline_arima.py`
- `[x]` **C-04**: Build and train the LSTM model on valid trading days only (no weekend data).
  - *File*: `src/models/train_lstm.py`
  - *Architecture*: Per `docs/ml-spec.md` Section 1. Use `MinMaxScaler` for sequence normalization.
  - *Verification*: RMSE and MAE logged. LSTM RMSE < ARIMA RMSE.
- `[x]` **C-05**: Generate T+1 to T+5 predictions. Write results to BigQuery table `fact_model_predictions` (or equivalent).
  - *Verification*: Predictions table exists in BigQuery. Looker Studio can connect to it.

### C-3: K-Means Clustering with PCA

- `[x]` **C-06**: Apply PCA to the scaled bank feature matrix. Determine optimal number of components for ≥80% explained variance.
  - *File*: `src/models/train_kmeans.py`
  - *Verification*: Cumulative explained variance plot logged. Component count documented.
- `[x]` **C-07**: Apply K-Means. Determine optimal `k` using the Elbow Method and Silhouette Analysis.
  - *Verification*: Elbow and Silhouette plots saved to `reports/figures/`.
- `[x]` **C-08**: Train final K-Means model. Compute Silhouette Score and Davies-Bouldin Index. Log both metrics.
  - *Verification*: Both metrics logged. Cluster assignments written to BigQuery.

### C-4: Random Forest Classification

- `[x]` **C-09**: Establish Logistic Regression baseline for NPL ≥ 3% classification. Log AUC-ROC.
  - *File*: `src/models/baseline_logistic.py`
- `[x]` **C-10**: Train Random Forest classifier. Apply time-based train/test split.
  - *File*: `src/models/train_random_forest.py`
  - *Verification*: AUC-ROC > 0.80. Recall for High Risk class ≥ 85%. Both metrics logged.
- `[x]` **C-11**: Extract and log Feature Importance. Save bar chart to `reports/figures/`.
  - *Verification*: Feature importance values written to log. Chart saved.
- `[x]` **C-12**: Write classification predictions and risk labels to BigQuery.
  - *Verification*: Prediction table exists and is queryable.

---

## Track D — Business Intelligence (Đỗ Kiến Hưng & Phạm Minh Quân)
*Depends on C-05, C-08, and C-12 being complete.*

- `[x]` **D-00**: Prototype and validate all three dashboard pages (Market Movement, Bank Profiling, Risk Monitoring) locally using processed CSV files.
  - *File*: `src/models/local/generate_dashboard_plots.py`
  - *Verification*: Plots generated successfully in `reports/figures/dashboard/` and business interpretation report saved to `docs/process/bao_cao_dashboard_ml_local.md`.
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

- `[x]` ETL pipeline runs without errors and all 10 BigQuery tables are populated.
- `[x]` Data quality validation (B-14, B-15) passes with zero critical errors.
- `[x]` LSTM RMSE is lower than the ARIMA baseline.
- `[x]` Random Forest achieves AUC-ROC > 0.80 and Recall ≥ 85% for the High Risk class.
- `[x]` K-Means Silhouette Score is logged and clusters are interpretable.
- `[ ]` All 3 Looker Studio dashboard pages render from live BigQuery data.
- `[x]` All ML model metrics are logged to the Python `logging` system (no bare `print()` statements).
