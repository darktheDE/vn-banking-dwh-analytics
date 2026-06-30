# ETL Pipeline Specification

## 1. Overview

This document specifies the exact Extract, Transform, and Load logic for each of the 7 source Excel files. It serves as the authoritative implementation contract for the Data Engineering role (Trần Minh Khánh, Nguyễn Đặng Quốc Anh & Đỗ Kiến Hưng). All Python ETL scripts in `src/etl/` must conform to these rules.

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

---

## 3. Per-File Transformation Specification

### 3.1 File F3 — BID Price History → `fact_price_history`

**Source Sheet**: Sheet 1 of the BID Price file.

**Column Mappings**:

| Raw Column Name | Canonical Field | Transform Rule |
|-----------------|-----------------|----------------|
| Date / Ngày | `date_key` | Parse as `datetime`, format to YYYYMMDD INT64 |
| Open / Mở cửa | `open_price` | Cast to `float64`. Divide by 1000 if stored in units of đồng (verify unit). |
| High / Cao nhất | `high_price` | Cast to `float64` |
| Low / Thấp nhất | `low_price` | Cast to `float64` |
| Close / Đóng cửa | `close_price` | Cast to `float64`. This is the **LSTM target variable**. |
| Volume / Khối lượng | `trading_volume` | Cast to `Int64`. Remove commas before casting. |

**Missing Value Rule**: No forward-fill. If `close_price` is null for any row, reject the row and log a warning.

**Validation**: Row count after load must equal 22. If not, raise a critical error.

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

### 3.5 File F5 — HPG Intraday Ticks (Deprecated/Removed)

This file and task are deprecated/removed as HPG was removed to focus strictly on the banking sector. The table `fact_intraday_matching` remains in the schema but is empty.


---

### 3.6 Files F6–F7 — Bank Financials → `fact_bank_performance`

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

### 4.4 `dim_trading_session`

| `session_key` | `session_name` | `start_time` | `end_time` |
|---------------|----------------|--------------|------------|
| 1 | ATO | 09:00:00 | 09:14:59 |
| 2 | Morning | 09:15:00 | 11:29:59 |
| 3 | Afternoon | 13:00:00 | 14:29:59 |
| 4 | ATC | 14:30:00 | 14:45:00 |

---

## 5. BigQuery Load Configuration

All Fact tables must be loaded using `pandas_gbq` or the `google-cloud-bigquery` Python client with the following settings:

```python
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_APPEND",  # Use WRITE_TRUNCATE for full reloads
    time_partitioning=bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="date_key",  # Cast to DATE in BigQuery table definition
    ),
    clustering_fields=["stock_key"],  # or ["bank_key"] for bank fact tables
)
```

**Idempotency**: Before appending, the ETL script must check if records for the target date already exist in BigQuery and skip the load to prevent duplicates.
