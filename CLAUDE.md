# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository guidance

Read [AGENTS.md](AGENTS.md) before making code or data-model changes. It is the project constitution and contains the non-negotiable ETL, BigQuery, ML, credential, logging, and communication rules. The detailed contracts are in the `docs/` specifications; consult the one relevant to the change rather than duplicating its contents here:

- [docs/etl-spec.md](docs/etl-spec.md) for source mappings and transformations.
- [docs/star-schema.md](docs/star-schema.md) for BigQuery tables, keys, partitioning, clustering, and SCD Type 2 behavior.
- [docs/ml-spec.md](docs/ml-spec.md) for model architecture and acceptance criteria.
- [docs/data-dictionary.md](docs/data-dictionary.md) for field definitions and data-quality rules.
- [docs/dashboard-spec.md](docs/dashboard-spec.md) for dashboard requirements.
- [docs/tasks.md](docs/tasks.md) for task-level acceptance criteria.
- [DEVELOPMENT.md](DEVELOPMENT.md) for coding standards and Git workflow.

No Cursor or Copilot instruction files are present in this repository.

## Common commands

Run commands from the repository root so imports such as `src.utils...` resolve correctly. The project targets Python 3.9+, but TensorFlow compatibility currently requires Python 3.9–3.11.

```bash
python -m venv venv
```

Windows PowerShell activation:

```bash
venv\Scripts\Activate.ps1
```

macOS/Linux activation:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create local configuration by copying `.env.example` to `.env`, then set GCP credentials, `GCP_PROJECT_ID`, and the local data/model paths. BigQuery-backed commands require valid Google credentials and the required IAM roles.

Start the Streamlit dashboard:

```bash
streamlit run src/dashboard/app.py
```

Run the full initialization pipeline on Windows or Unix-like systems:

```bash
run_setup.bat
```

```bash
./run_setup.sh
```

The setup scripts run extraction, BigQuery schema provisioning, dimension population, local fact transformation, BigQuery loading, integrity validation, and model feature engineering/training in sequence. Use individual module commands when iterating or when a full rerun is not appropriate.

Provision and populate the warehouse manually:

```bash
python -m src.etl.provision_schema
python -m src.etl.populate_dim_date
python -m src.etl.populate_dim_stock
python -m src.etl.populate_dim_bank
python -m src.etl.populate_dim_trading_session
python -m src.etl.consolidate_stock_metrics
python -m src.etl.load_bank_performance
python -m src.etl.load_to_bigquery
python -m src.etl.validate_integrity
```

Run the production ML stages manually:

```bash
python -m src.models.feature_engineering_stock
python -m src.models.feature_engineering_bank
python -m src.models.baseline_arima
python -m src.models.train_lstm
python -m src.models.train_kmeans
python -m src.models.baseline_logistic
python -m src.models.train_random_forest
```

There is no configured test runner, lint script, or test suite currently present. Do not invent a `pytest` command as an existing project command. For a focused smoke check, run the specific module with `python -m ...`; for ETL changes, the required validation command is:

```bash
python -m src.etl.validate_integrity
```

For a single notebook check, restart the kernel and run all cells top-to-bottom; notebooks are for EDA/prototyping rather than the production pipeline.

## Architecture

This is a Python batch analytics platform with a Streamlit presentation layer and Google BigQuery as the analytical warehouse. The overall flow is:

```text
raw Excel/CSV sources
  -> src.etl extract/transform/load jobs
  -> BigQuery star schema
  -> src.models feature engineering and ML jobs
  -> BigQuery ML output tables
  -> Streamlit dashboard and Looker Studio
```

`src/etl/` contains independent command-line modules for extraction, normalization, dimension population, fact preparation, BigQuery loading, schema provisioning, and integrity checks. The ETL layer converts source columns to snake_case and typed fields, generates date and surrogate keys, appends audit metadata, and loads warehouse tables. BigQuery writes are intended to be incremental/idempotent; preserve the schema's partitioning/clustering and SCD Type 2 behavior when changing loaders. `src/etl/load_to_bigquery.py` is the central load orchestration module, while the `populate_dim_*` and `load_*` modules can be run independently.

`sql/bigquery_schema.sql` defines the warehouse DDL. The warehouse uses dimensions for dates, stocks, banks, trading sessions, and audit runs; facts for daily stock metrics and annual bank performance; and ML output tables for LSTM predictions, bank clusters, and bank risk predictions. Local cleaned data and committed ML samples/results live under `data/`; raw source files are expected under the configured, normally ignored `data/raw/` path.

`src/models/` contains three analytical tracks. Stock feature engineering feeds the LSTM forecasting workflow, with ARIMA as a comparison-only baseline. Bank feature engineering feeds K-Means/PCA clustering and Random Forest credit-risk classification, with logistic regression as the classification baseline. Training/inference modules may query BigQuery and write predictions or assignments back to configured tables; local analysis variants and generated artifacts should remain separate from the production modules.

`src/utils/` centralizes environment loading (`config.py`), BigQuery client/table-ID construction (`bigquery_client.py`), and stdout logging (`logger.py`). Production ETL and model code should use `get_logger()` rather than `print()`, load configuration through environment variables, and be invoked as modules from the root.

`src/dashboard/app.py` is the Streamlit application that presents predictions, risk classification, clustering, and analytical views. Looker Studio is a separate BigQuery-connected BI consumer; dashboard behavior and required charts are specified in [docs/dashboard-spec.md](docs/dashboard-spec.md).

## Data and model invariants

Preserve the contracts in [AGENTS.md](AGENTS.md), especially these implementation constraints:

- Do not hardcode GCP project IDs, dataset IDs, or service-account contents; use `.env` and `src.utils.config`.
- Do not create artificial weekend/holiday observations for stock forecasting.
- Daily stock gaps may be forward-filled for at most one day; a null `close_price` row is rejected.
- Bank missing values use the specified median-imputation rules; `npl_ratio` is never forward-filled.
- Random Forest risk target is `npl_ratio >= 0.03`, with time-based splitting, AUC-ROC above 0.80, and high-risk recall at least 0.85.
- LSTM forecasts horizons T+1 through T+5 and must be evaluated against the ARIMA baseline.
- K-Means uses StandardScaler then PCA retaining at least 80% explained variance, and documents both elbow and silhouette analyses.
- Run `validate_integrity` after ETL changes or pipeline runs.
- Avoid `WRITE_TRUNCATE` except for an explicitly intended full reload, and never overwrite SCD Type 2 history.

For project overview, dataset context, pipeline stages, and the documented quick start, see [README.md](README.md). For environment details, see [docs/env-config.md](docs/env-config.md).
