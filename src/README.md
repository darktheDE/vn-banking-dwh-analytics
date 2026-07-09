# src/

This directory contains all production-quality Python source code for the Financial Data Analytics Platform. Code here is promoted from notebook prototypes after validation.

## Structure

| Directory | Owner | Description |
|-----------|-------|-------------|
| `etl/` | Trần Minh Khánh, Nguyễn Đặng Quốc Anh & Đỗ Kiến Hưng | ETL scripts: Extract from Excel, Transform and clean, Load to BigQuery |
| `models/` | Phạm Minh Quân & Nguyễn Đặng Quốc Anh | Feature engineering, model training, inference, and BigQuery write-back |
| `utils/` | All | Shared utilities: BigQuery client, logger, config loader |

## Module Usage

All scripts use the standard Python `logging` library. Never use bare `print()` statements in production scripts.

All BigQuery credentials are loaded from environment variables. See [`docs/env-config.md`](../docs/env-config.md) and `.env.example`.

## Running ETL

```bash
# Provision schema and populate dimension tables first (one-time setup)
python -m src.etl.provision_schema
python -m src.etl.populate_dim_date
python -m src.etl.populate_dim_stock
python -m src.etl.populate_dim_bank
python -m src.etl.populate_dim_trading_session

# Transform fact tables locally
python -m src.etl.consolidate_stock_metrics
python -m src.etl.load_bank_performance

# Load to BigQuery and validate integrity
python -m src.etl.load_to_bigquery
python -m src.etl.validate_integrity
```

For full task sequence and verification criteria, see [`docs/tasks.md`](../docs/tasks.md).
