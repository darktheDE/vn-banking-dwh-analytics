# ETL Pipeline Specification

## 1. Overview

This document specifies the exact Extract, Transform, and Load logic for each of the 6 source Excel/CSV files. It serves as the authoritative implementation contract for the Data Engineering role (Trần Minh Khánh, Nguyễn Đặng Quốc Anh & Đỗ Kiến Hưng). All Python ETL scripts in `src/etl/` must conform to these rules.

**Execution Model**: Scheduled Batch Jobs. Stock data runs End-of-Day (EOD). Bank financial data runs Quarterly, aligned with official bank reporting cycles.

**Primary Libraries**: `pandas`, `openpyxl`, `google-cloud-bigquery`, `python-dotenv`.

---

## 2. General Transformation Rules (Applies to All Sources)

These rules apply universally before loading to BigQuery:

| Rule | Description |
|------|-------------|
| **Date Standardization** | All date strings must be parsed and converted to `datetime` objects, then formatted as `YYYYMMDD` INT64 for `date_key` and as ISO `DATE` strings for `full_date` in `dim_date`. |
| **Column Naming** | All column names must be converted to `snake_case` and stripped of special characters, whitespace, and units. |
| **Data Type Enforcement** | All FLOAT fields must be cast to `float64`. All INTEGER fields must be cast to `Int64` (nullable integer). All STRING fields must be stripped and uppercased for codes. |
| **Surrogate Key Generation** | Surrogate keys (`stock_key`, `bank_key`, `session_key`) are generated as sequential integers during the Transform step using a lookup dictionary before loading. |
| **Duplicate Removal** | After loading, duplicate rows by primary key combination must be dropped with `keep='first'`. |
| **Logging** | Every load step must log the exact row count successfully written to BigQuery using `logging.info()`. |
| **Incremental Loading** | High-volume fact/dim tables must utilize BigQuery `MERGE` (upsert) queries to insert new and update existing rows, maintaining idempotency. |
| **DWH Auditing** | Every loaded table must append system fields `_created_at` (current timestamp), `_updated_at` (current timestamp), and `_source_file` (the filename of the raw spreadsheet, e.g. `BID_price_history.xlsx`). |

---

## 3. Per-File Transformation Specification

### 3.1 File F3 — Consolidated Price History (BID, TCB, VCB, CTG) → `fact_price_history`

**Source**: Processed CSV files per bank in `data/processed/<ticker>/<ticker>_stock_history.csv`.

**Column Mappings**:

| Raw Column Name | Canonical Field | Transform Rule |
|-----------------|-----------------|----------------|
| Date / Ngày | `date_key` | Parse as `datetime`, format to YYYYMMDD INT64 |
| Open / Mở cửa | `open_price` | Cast to `float64`. Divide by 1000 if stored in units of đồng (verify unit). |
| High / Cao nhất | `high_price` | Cast to `float64` |
| Low / Thấp nhất | `low_price` | Cast to `float64` |
| Close / Đóng cửa | `close_price` | Cast to `float64`. This is the **LSTM target variable**. |
| Volume / Khối lượng | `trading_volume` | Cast to `Int64`. Remove commas before casting. |

**Stock Key Assignment**: BID=1, TCB=2, VCB=3, CTG=4.

**Missing Value Rule**: No forward-fill. If `close_price` is null for any row, reject the row and log a warning.

**Validation**: Consolidated row count after load equals 11,835 across all 4 banks.

---

### 3.2 File F1 — BID Foreign Trading → `fact_foreign_trading`

**Column Mappings**:

| Raw Column Name | Canonical Field | Transform Rule |
|-----------------|-----------------|----------------|
| Date | `date_key` | Parse as `datetime`, format to YYYYMMDD |
| Foreign Buy Volume | `foreign_buy_volume` | Cast to `Int64` |
| Foreign Sell Volume | `foreign_sell_volume` | Cast to `Int64` |
| Foreign Net Volume | `foreign_net_volume` | Compute as `foreign_buy_volume - foreign_sell_volume` if not present directly |
| Foreign Net Value | `foreign_net_value` | Cast to `float64`. Units: VND billions. |
| Foreign Ownership | `foreign_ownership_ratio` | Cast to `float64`. Divide by 100 if stored as percentage integer. |

**Missing Value Rule**: If any metric column is null, apply **forward-fill** (maximum 1 day) then log a warning.

---

### 3.3 File F2 — BID Proprietary Trading → `fact_proprietary_trading`

**Column Mappings**:

| Raw Column Name | Canonical Field | Transform Rule |
|-----------------|-----------------|----------------|
| Date | `date_key` | Parse as `datetime`, format to YYYYMMDD |
| Prop Buy Volume | `prop_buy_volume` | Cast to `Int64` |
| Prop Sell Volume | `prop_sell_volume` | Cast to `Int64` |
| Prop Net Volume | `prop_net_volume` | Compute as `prop_buy_volume - prop_sell_volume` if absent |
| Prop Net Value | `prop_net_value` | Cast to `float64`. Units: VND billions. |

**Missing Value Rule**: Forward-fill with maximum 1 day.

---

### 3.4 File F4 — BID Order Statistics → `fact_order_stats`

**Column Mappings**:

| Raw Column Name | Canonical Field | Transform Rule |
|-----------------|-----------------|----------------|
| Date | `date_key` | Parse as `datetime`, format to YYYYMMDD |
| Total Buy Orders | `total_buy_orders` | Cast to `Int64` |
| Total Buy Volume | `total_buy_volume` | Cast to `Int64` |
| Total Sell Orders | `total_sell_orders` | Cast to `Int64` |
| Total Sell Volume | `total_sell_volume` | Cast to `Int64` |
| Matched Volume | `matched_volume` | Cast to `Int64` |

**Missing Value Rule**: No forward-fill. Null rows are rejected and logged.

---

### 3.5 Files F6–F7 — Bank Financials → `fact_bank_performance`

**Expected Volume**: ~667 rows, 47+ columns, covering 46 banks from 2002 to 2022.

**Column Mappings** (see full list in `docs/data-dictionary.md` Section 3):

| Raw Column | Canonical Field | Transform Rule |
|------------|-----------------|----------------|
| Bank code / Mã ngân hàng | `bank_code` | Uppercase string. Map to `bank_key` via `dim_bank` lookup. |
| Year / Năm | `date_key` | Map year integer to Dec 31 of that year (YYYYMMDD). |
| TASSETS, DEPOSITS, LOANS, EQUITY | Scale fields | Cast to `float64`. Units must be VND billions — divide if stored as absolute VND. |
| NPLRATIO | `npl_ratio` | Cast to `float64`. If stored as percentage (e.g., 3.5), divide by 100. Value range: [0.0, 1.0]. |
| ROA, ROE, NIM, CIR, ETA, ETD, LTA, LTD | Ratio fields | Cast to `float64`. Same percentage normalization check applies. |

**Missing Value Rule for 2002–2005 Data**:
- For numerical CAMELS ratios (`roa`, `roe`, `nim`, `cir`, `npl_ratio`, `eta`): impute with the **column median** computed from 2006–2022 data for the same bank. If insufficient data exists for a specific bank, use the **global column median**.
- Imputed values must be flagged in a separate boolean column `is_imputed` for downstream audit.
- Do **not** impute `npl_ratio` using forward-fill; median is mandatory to avoid bias in the classification target.

**Validation**: After imputation, no null values should remain in any CAMELS ratio column. Log an error if nulls persist.

---

## 4. Dimension Table Population

Dimension tables are populated once during the initial setup run and updated only when new banks or stocks are added.

### 4.1 `dim_date`

Generated programmatically using `pandas.date_range()` covering 2002-01-01 to 2026-12-31. Trading day flag (`is_trading_day`) is set based on the official HOSE calendar (weekdays, excluding Vietnamese public holidays).

### 4.2 `dim_stock`

| `stock_key` | `ticker` | `company_name` | `exchange` | `industry` |
|-------------|----------|----------------|------------|------------|
| 1 | BID | BIDV — Joint Stock Commercial Bank for Investment and Development of Vietnam | HOSE | Banking |
| 2 | TCB | Vietnam Technological and Commercial Joint Stock Bank | HOSE | Banking |
| 3 | VCB | Joint Stock Commercial Bank for Foreign Trade of Vietnam | HOSE | Banking |
| 4 | CTG | Vietnam Joint Stock Commercial Bank for Industry and Trade | HOSE | Banking |


### 4.3 `dim_bank`

Populated from the bank identifier columns in the raw CAMELS files (bank code, full name, bank type). `bank_type` must be one of: `SOCB` (State-owned), `JSCB` (Joint Stock), `FOCB` (Foreign-owned).

**SCD Type 2 Ingestion Logic**:
To track changes in bank attributes (such as `charter_capital`) over time:
1. When loading a bank record, check if a record with the same `bank_code` already exists in `dim_bank` with `is_current = TRUE`.
2. If it does not exist, insert it with `valid_from = current_date`, `valid_to = '9999-12-31'`, and `is_current = TRUE`.
3. If it exists, compare the values of `charter_capital`, `bank_name`, and `bank_type`.
4. If any attribute has changed:
   - Perform an UPDATE on the existing record to set `valid_to = current_date - 1` and `is_current = FALSE`.
   - Perform an INSERT of the new bank record version with `valid_from = current_date`, `valid_to = '9999-12-31'`, and `is_current = TRUE`.
5. If no attributes changed, ignore/do nothing.

### 4.4 `dim_trading_session`

| `session_key` | `session_name` | `start_time` | `end_time` |
|---------------|----------------|--------------|------------|
| 1 | ATO | 09:00:00 | 09:14:59 |
| 2 | Morning | 09:15:00 | 11:29:59 |
| 3 | Afternoon | 13:00:00 | 14:29:59 |
| 4 | ATC | 14:30:00 | 14:45:00 |

---

## 5. BigQuery Load Configuration

To enable robust incremental loading (upserts) and guarantee idempotency without creating duplicate records, loading must utilize BigQuery `MERGE` SQL statements.

### BigQuery MERGE Upsert Template

For daily fact tables (e.g. `fact_price_history`), the incremental loading logic should follow this template:

```sql
MERGE INTO `{project_id}.{dataset_id}.fact_price_history` target
USING `{project_id}.{dataset_id}.staging_fact_price_history` staging
ON target.date_key = staging.date_key AND target.stock_key = staging.stock_key
WHEN MATCHED THEN
  UPDATE SET
    target.open_price = staging.open_price,
    target.high_price = staging.high_price,
    target.low_price = staging.low_price,
    target.close_price = staging.close_price,
    target.trading_volume = staging.trading_volume,
    target._updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (date_key, stock_key, open_price, high_price, low_price, close_price, trading_volume, _created_at, _updated_at, _source_file)
  VALUES (staging.date_key, staging.stock_key, staging.open_price, staging.high_price, staging.low_price, staging.close_price, staging.trading_volume, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), staging._source_file)
```

For dimension tables with SCD Type 2 tracking (`dim_bank`), updates must be performed using transactional SQL or multi-step MERGE queries that expire older rows and insert new rows with appropriate valid date windows.
