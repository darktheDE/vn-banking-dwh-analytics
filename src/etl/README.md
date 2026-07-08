# src/etl/

ETL (Extract, Transform, Load) pipeline scripts for the Financial Data Analytics Platform.

## Script Index

| Script | Task ID | Description |
|--------|---------|-------------|
| `populate_dim_date.py` | B-04 | Generate and load the `dim_date` dimension table (2002–2026) |
| `populate_dim_stock.py` | B-05 | Load `dim_stock` records for focus banks (BID, TCB, VCB, CTG) |
| `populate_dim_bank.py` | B-06 | Load `dim_bank` records for 45 commercial banks |
| `populate_dim_trading_session.py` | B-07 | Load `dim_trading_session` records (ATO, Morning, Afternoon, ATC) |
| `load_price_history.py` | B-08 | ETL for bank OHLCV price history data → `fact_stock_daily_metrics` (pre-consolidation) |
| `load_bank_performance.py` | B-13 | ETL for 45 banks CAMELS data → `fact_bank_performance` |
| `consolidate_stock_metrics.py` | - | Consolidate and finalize stock metrics → `fact_stock_daily_metrics` |
| `validate_integrity.py` | B-14/15 | Referential integrity and data quality checks post-load |

## Transformation Rules

All transformation rules, column mappings, and missing value strategies are specified in [`docs/etl-spec.md`](../../docs/etl-spec.md).

## Coding Standards

- All functions must include type hints and docstrings.
- All BigQuery row counts must be logged via `logging.info()`.
- No hardcoded credentials. Use `os.getenv()` with `python-dotenv`.
