# Data Warehouse Architecture: Star Schema Design

## 1. Overview

The Financial Data Analytics Platform utilizes a **Star Schema** architecture deployed on **Google BigQuery**. This design is highly optimized for Online Analytical Processing queries, enabling rapid aggregation, filtering, and joining for the Looker Studio dashboard and Machine Learning data pipelines.

The schema consists of a centralized set of **Fact Tables** recording quantitative events and metrics surrounded by **Dimension Tables** storing descriptive attributes.

---

## 2. Dimension Tables

Dimension tables contain descriptive attributes that provide context to the fact records. They are generally smaller in size and serve as lookup tables for filtering and grouping.

### 2.1 `dim_date`

Stores calendar information to enable time-series analysis and granular aggregations such as weekly, monthly, and quarterly views.
- `date_key` of type INT64 as Primary Key: Format YYYYMMDD like 20260619.
- `full_date` of type DATE: Standard date format.
- `day` of type INT64: Day of the month.
- `month` of type INT64: Month of the year.
- `year` of type INT64: Year like 2026.
- `quarter` of type INT64: Quarter.
- `is_trading_day` of type BOOLEAN: Flag indicating if the date is a valid stock market trading day.

### 2.2 `dim_stock`

Stores descriptive information about the traded stock assets.
- `stock_key` of type INT64 as Primary Key: Unique surrogate key for the stock.
- `ticker` of type STRING: Stock symbol like 'BID', 'TCB', 'VCB', and 'CTG'.
- `company_name` of type STRING: Full name of the company.
- `exchange` of type STRING: Trading exchange like 'HOSE'.
- `industry` of type STRING: Sector classification.

### 2.3 `dim_bank`

Stores descriptive and structural information about the 45 commercial banks. Includes Slowly Changing Dimension (SCD Type 2) columns to track historical modifications (e.g. charter capital increases) over time.
- `bank_key` of type INT64 as Primary Key: Unique surrogate key for the bank.
- `bank_code` of type STRING: Standardized bank ticker like ‘VCB’ and ‘BID’.
- `bank_name` of type STRING: Full name of the bank.
- `bank_type` of type STRING: State-owned SOCB, Joint Stock JSCB, or Foreign FOCB.
- `charter_capital` of type FLOAT64: Registered charter capital.
- `valid_from` of type DATE: The start date from which this bank version record is valid.
- `valid_to` of type DATE: The end date until which this bank version record was valid (defaults to `9999-12-31` for current records).
- `is_current` of type BOOLEAN: Flag indicating if this record represents the most recent/active version of the bank.

### 2.4 `dim_trading_session`

Stores definitions of intraday trading sessions primarily used for high-frequency intraday data.
- `session_key` of type INT64 as Primary Key: Unique surrogate key.
- `session_name` of type STRING: Name of the session including ‘ATO’, ‘Morning’, ‘Afternoon’, and ‘ATC’.
- `start_time` of type TIME: Session start time.
- `end_time` of type TIME: Session end time.

### 2.5 `dim_audit`

Stores run metadata for every ETL pipeline execution to track data lineage, processing status, and auditing.
- `audit_key` of type INT64 as Primary Key: Dynamic integer key formatted as `YYYYMMDDHHMMSS` based on script execution start time.
- `run_id` of type STRING: Unique UUID generated for the specific runtime execution.
- `run_timestamp` of type TIMESTAMP: Execution start timestamp.
- `script_name` of type STRING: The filename of the Python loader script that ran (e.g. `load_price_history.py`).
- `source_file` of type STRING: The filename of the raw spreadsheet read.
- `rows_processed` of type INT64: Count of data rows successfully processed.
- `status` of type STRING: The execution status of the job (e.g. `RUNNING`, `SUCCESS`, `FAILED`).

---

## 3. Fact Tables

Fact tables store the measurable, quantitative data for analysis. They contain Foreign Keys referencing the Dimension tables and metric columns.

### 3.1 `fact_stock_daily_metrics`

Records the daily trading metrics, prices, and orders for stocks.
- **Foreign Keys**: `date_key`, `stock_key`
- **Metrics**:
  - `open_price` of type FLOAT64
  - `high_price` of type FLOAT64
  - `low_price` of type FLOAT64
  - `close_price` of type FLOAT64
  - `trading_volume` of type INT64
  - `foreign_buy_volume` of type INT64
  - `foreign_sell_volume` of type INT64
  - `foreign_net_volume` of type INT64
  - `foreign_net_value` of type FLOAT64
  - `foreign_ownership_ratio` of type FLOAT64
  - `prop_buy_volume` of type INT64
  - `prop_sell_volume` of type INT64
  - `prop_net_volume` of type INT64
  - `prop_net_value` of type FLOAT64
  - `total_buy_orders` of type INT64
  - `total_buy_volume` of type INT64
  - `total_sell_orders` of type INT64
  - `total_sell_volume` of type INT64
  - `matched_volume` of type INT64


### 3.5 `fact_bank_performance`

Records the annual and quarterly financial health indicators of the commercial banks.
- **Foreign Keys**: `date_key` pointing to the financial reporting date, `bank_key`
- **Scale Metrics**:
- `total_assets` of type FLOAT64: Total assets (VND billions)
- `total_deposits` of type FLOAT64: Total customer deposits (VND billions)
- `total_loans` of type FLOAT64: Total loan portfolio (VND billions)
- `total_equity` of type FLOAT64: Total shareholder equity (VND billions)
- `num_employees` of type INT64: Number of employees
- `num_branches` of type INT64: Number of branches
- **Asset Quality Metrics**:
- `npl_amount` of type FLOAT64: Non-Performing Loan balance (VND billions)
- `loan_loss_provision` of type FLOAT64: Loan Loss Provision balance (VND billions)
- `npl_ratio` of type FLOAT64: NPL / Total Loans (Classification target, threshold >= 3%)
- `llp_ratio` of type FLOAT64: LLP / Total Loans
- **Income and Expense Metrics**:
- `interest_income` of type FLOAT64
- `interest_expense` of type FLOAT64
- `net_interest_income` of type FLOAT64
- `non_interest_expense` of type FLOAT64
- `personnel_expense` of type FLOAT64
- `other_expense` of type FLOAT64
- `profit_before_tax` of type FLOAT64
- `profit_after_tax` of type FLOAT64
- `off_balance_sheet` of type FLOAT64
- **CAMELS Performance Ratios**:
- `roa` of type FLOAT64: Return on Assets
- `roe` of type FLOAT64: Return on Equity
- `nim` of type FLOAT64: Net Interest Margin
- `cir` of type FLOAT64: Cost to Income Ratio
- `eta` of type FLOAT64: Equity to Total Assets (Capital Adequacy)
- `etd` of type FLOAT64: Equity to Total Deposits
- `lta` of type FLOAT64: Loans to Total Assets (Liquidity)
- `ltd` of type FLOAT64: Loans to Total Deposits
- `gta` of type FLOAT64: Gross Loans to Total Assets (Sensitivity)
- **ETL Flag**:
- `is_imputed` of type BOOLEAN: True if any value was median-imputed (2002-2005 data)

### 3.6 Machine Learning Output Tables

To serve predictions downstream, three dedicated output tables are defined in BigQuery:

#### 3.6.1 `bank_cluster_assignments` (K-Means Outputs)
Stores strategic cluster labels assigned to each commercial bank.
- `bank_key` of type INT64
- `bank_code` of type STRING
- `bank_name` of type STRING
- `bank_type` of type STRING
- `cluster_id` of type INT64: Assigned cluster identifier
- `model_name` of type STRING: Model identification string

#### 3.6.2 `bank_risk_predictions` (Random Forest Outputs)
Stores credit risk classifications and probabilities for each bank.
- `bank_key` of type INT64
- `bank_code` of type STRING
- `date_key` of type INT64
- `risk_label` of type INT64: Binary classification (`1` for NPL ≥ 3%, `0` otherwise)
- `risk_probability` of type FLOAT64: Probability score of the risk class
- `actual_npl_ratio` of type FLOAT64: Historical ground truth NPL ratio
- `model_name` of type STRING

#### 3.6.3 `fact_model_predictions` (LSTM Outputs)
Stores daily multi-horizon predictions for banking stock close prices (BID, TCB, VCB, CTG).
- `base_date_key` of type INT64: The date on which the prediction was generated
- `stock_key` of type INT64
- `horizon` of type STRING: Prediction window label (e.g. `'T+1'`, `'T+2'`, ..., `'T+5'`)
- `predicted_close_price` of type FLOAT64: Predicted closing price
- `model_name` of type STRING

---

## 4. Entity-Relationship Overview

- **1-to-Many Relationships**:
    - One record in `dim_date` maps to multiple records across all Fact tables.
    - One record in `dim_stock` maps to multiple records in `fact_stock_daily_metrics`.
    - One record in `dim_bank` maps to multiple records in `fact_bank_performance`.
    - One record in `dim_audit` maps to multiple records across all Dimension and Fact tables.

## 5. Google BigQuery Optimizations

To ensure low latency and cost-efficiency when querying massive datasets:
- **Partitioning**: Fact tables with high volumes such as `fact_stock_daily_metrics` will be strictly partitioned by `date_key` via integer range bucket. This restricts the amount of data scanned when querying specific date ranges.
- **Clustering**: Fact tables will be clustered by `stock_key` or `bank_key`. This optimizes performance when the Looker Studio dashboard applies ticker or bank-specific filters.
- **DWH Auditing**: To support tracking, lineage, and data processing verification, all tables (both Fact and Dimension) include `audit_key` (referencing `dim_audit`) and dynamically append the following system columns during the transformation phase:
    - `audit_key` of type INT64: The key pointing to the corresponding `dim_audit` execution row.
    - `_created_at` of type TIMESTAMP: The timestamp indicating when the row was first loaded.
    - `_updated_at` of type TIMESTAMP: The timestamp indicating when the row was last updated.
    - `_source_file` of type STRING: The filename of the source file from which this data row was extracted.