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
# Populate dimension tables first (one-time setup)
python -m src.etl.populate_dim_date
python -m src.etl.populate_dim_stock
python -m src.etl.populate_dim_bank
python -m src.etl.populate_dim_trading_session

# Load fact tables
python -m src.etl.load_price_history
python -m src.etl.load_foreign_trading
python -m src.etl.load_proprietary_trading
python -m src.etl.load_order_stats
python -m src.etl.load_bank_performance

# Validate integrity
python -m src.etl.validate_integrity
```

For full task sequence and verification criteria, see [`docs/tasks.md`](../docs/tasks.md).
