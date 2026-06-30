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

Stores descriptive and structural information about the 46 commercial banks.
- `bank_key` of type INT64 as Primary Key: Unique surrogate key for the bank.
- `bank_code` of type STRING: Standardized bank ticker like ‘VCB’ and ‘BID’.
- `bank_name` of type STRING: Full name of the bank.
- `bank_type` of type STRING: State-owned SOCB, Joint Stock JSCB, or Foreign FOCB.
- `charter_capital` of type FLOAT64: Registered charter capital.

### 2.4 `dim_trading_session`

Stores definitions of intraday trading sessions primarily used for high-frequency intraday data.
- `session_key` of type INT64 as Primary Key: Unique surrogate key.
- `session_name` of type STRING: Name of the session including ‘ATO’, ‘Morning’, ‘Afternoon’, and ‘ATC’.
- `start_time` of type TIME: Session start time.
- `end_time` of type TIME: Session end time.

---

## 3. Fact Tables

Fact tables store the measurable, quantitative data for analysis. They contain Foreign Keys referencing the Dimension tables and metric columns.

### 3.1 `fact_price_history`

Records the daily historical price movements for stocks.
- **Foreign Keys**: `date_key`, `stock_key`
- **Metrics**:
- `open_price` of type FLOAT64
- `high_price` of type FLOAT64
- `low_price` of type FLOAT64
- `close_price` of type FLOAT64
- `trading_volume` of type INT64

### 3.2 `fact_foreign_trading`

Records daily trading activities executed by foreign investors.
- **Foreign Keys**: `date_key`, `stock_key`
- **Metrics**:
- `foreign_buy_volume` of type INT64
- `foreign_sell_volume` of type INT64
- `foreign_net_volume` of type INT64
- `foreign_net_value` of type FLOAT64
- `foreign_ownership_ratio` of type FLOAT64

### 3.3 `fact_proprietary_trading`

Records daily trading activities executed by proprietary trading desks Khối tự doanh.
- **Foreign Keys**: `date_key`, `stock_key`
- **Metrics**:
- `prop_buy_volume` of type INT64
- `prop_sell_volume` of type INT64
- `prop_net_volume` of type INT64
- `prop_net_value` of type FLOAT64

### 3.4 `fact_order_stats`

Records daily statistics on market order placements representing supply and demand.
- **Foreign Keys**: `date_key`, `stock_key`
- **Metrics**:
- `total_buy_orders` of type INT64
- `total_buy_volume` of type INT64
- `total_sell_orders` of type INT64
- `total_sell_volume` of type INT64
- `matched_volume` of type INT64

### 3.5 `fact_intraday_matching`

Records highly granular tick-level matched trades during the trading day (currently deprecated/empty as HPG was removed to focus strictly on banking).
- **Foreign Keys**: `date_key`, `stock_key`, `session_key`
- **Metrics**:
- `timestamp` of type TIMESTAMP: Exact time of the match.
- `matched_price` of type FLOAT64
- `matched_volume` of type INT64
- `cumulative_volume` of type INT64


### 3.6 `fact_bank_performance`

Records the annual and quarterly financial health indicators of the commercial banks.
- **Foreign Keys**: `date_key` pointing to the financial reporting date, `bank_key`
- **Metrics for CAMELS framework extracts**:
- `total_assets` of type FLOAT64
- `total_deposits` of type FLOAT64
- `total_loans` of type FLOAT64
- `npl_ratio` of type FLOAT64: Non-Performing Loan ratio
- `roa` of type FLOAT64: Return on Assets
- `roe` of type FLOAT64: Return on Equity
- `nim` of type FLOAT64: Net Interest Margin
- `cir` of type FLOAT64: Cost to Income Ratio

---

## 4. Entity-Relationship Overview

- **1-to-Many Relationships**:
    - One record in `dim_date` maps to multiple records across all Fact tables.
    - One record in `dim_stock` maps to multiple records in `fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading`, `fact_order_stats`, and `fact_intraday_matching`.
    - One record in `dim_bank` maps to multiple records in `fact_bank_performance`.
    - One record in `dim_trading_session` maps to multiple records in `fact_intraday_matching`.

## 5. Google BigQuery Optimizations

To ensure low latency and cost-efficiency when querying massive datasets:
- **Partitioning**: Fact tables with high volumes including `fact_intraday_matching` and `fact_price_history` will be strictly partitioned by `date_key` cast to DATE. This restricts the amount of data scanned when querying specific date ranges.
- **Clustering**: Fact tables will be clustered by `stock_key` or `bank_key`. This optimizes performance when the Looker Studio dashboard applies ticker or bank-specific filters.