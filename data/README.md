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
| `VN banks dataset (updated August 2023).xlsx` | CAMELS financial data for 45 commercial banks (2002–2022) | `fact_bank_performance` |

*Note: Daily stock OHLCV data for BID, TCB, VCB, and CTG is programmatically crawled using [extract_data.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/extract_data.py) and loaded directly into the pipeline without requiring manual spreadsheet downloads.*

For full column mappings and transformation rules, see [`docs/etl-spec.md`](../docs/etl-spec.md).
