# src/etl/

ETL (Extract, Transform, Load) pipeline scripts for the Financial Data Analytics Platform.

## Script Index

| Script | Task ID | Description |
|--------|---------|-------------|
| `populate_dim_date.py` | B-04 | Generate and load the `dim_date` dimension table (2002–2026) |
| `populate_dim_stock.py` | B-05 | Load `dim_stock` records for BID and HPG |
| `populate_dim_bank.py` | B-06 | Load `dim_bank` records for 46 commercial banks |
| `populate_dim_trading_session.py` | B-07 | Load `dim_trading_session` records (ATO, Morning, Afternoon, ATC) |
| `load_price_history.py` | B-08 | ETL for BID OHLCV data → `fact_price_history` |
| `load_foreign_trading.py` | B-09 | ETL for BID foreign trading data → `fact_foreign_trading` |
| `load_proprietary_trading.py` | B-10 | ETL for BID proprietary trading data → `fact_proprietary_trading` |
| `load_order_stats.py` | B-11 | ETL for BID order statistics → `fact_order_stats` |
| `load_intraday_matching.py` | B-12 | ETL for HPG intraday ticks → `fact_intraday_matching` |
| `load_bank_performance.py` | B-13 | ETL for 46 banks CAMELS data → `fact_bank_performance` |
| `validate_integrity.py` | B-14/15 | Referential integrity and data quality checks post-load |

## Transformation Rules

All transformation rules, column mappings, and missing value strategies are specified in [`docs/etl-spec.md`](../../docs/etl-spec.md).

## Coding Standards

- All functions must include type hints and docstrings.
- All BigQuery row counts must be logged via `logging.info()`.
- No hardcoded credentials. Use `os.getenv()` with `python-dotenv`.
