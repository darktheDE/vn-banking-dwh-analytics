# data/

This directory stores all data files used by the Financial Data Analytics Platform. It is divided into three subdirectories based on the processing stage of the data.

> **Important**: Raw and processed data files are excluded from version control via `.gitignore`. Distribute source Excel files securely through encrypted channels, not through Git.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `raw/` | Original, unmodified source Excel/CSV files (6 files). Never edit files in this directory. |
| `processed/` | Cleaned and transformed DataFrames saved as Parquet or CSV after the ETL Transform step, before the BigQuery Load. |
| `external/` | Optional external reference data, such as Vietnamese public holiday calendars used to populate `dim_date.is_trading_day`. |

## Source File Index (place in `raw/`)

| File | Description | Target Fact Table |
|------|-------------|-------------------|
| `BID_foreign_trading.xlsx` | BID daily foreign investor trading data | `fact_foreign_trading` |
| `BID_proprietary_trading.xlsx` | BID daily proprietary desk trading data | `fact_proprietary_trading` |
| `BID_price_history.xlsx` | BID daily OHLCV price history | `fact_price_history` |
| `BID_order_stats.xlsx` | BID daily order placement statistics | `fact_order_stats` |
| `bank_financials_part1.xlsx` | CAMELS financial data for 45 banks (Part 1) | `fact_bank_performance` |
| `bank_financials_part2.xlsx` | CAMELS financial data for 45 banks (Part 2) | `fact_bank_performance` |

For full column mappings and transformation rules, see [`docs/etl-spec.md`](../docs/etl-spec.md).
