# Data Dictionary

## Overview

This document defines all data entities, source fields, and derived variables used across the Financial Data Analytics Platform. It serves as the **authoritative data contract** between the ETL layer, the BigQuery Star Schema, and the Machine Learning models.

**Ground Truth**: The raw data originates from 7 structured Excel files. This dictionary maps raw source columns to their canonical BigQuery field names and data types.

---

## 1. Source File Inventory

| File ID | Source File Description | Target Fact Table | Granularity |
|---------|------------------------|-------------------|-------------|
| `F1` | BID — Foreign Trading (Net Volume, Value) | `fact_foreign_trading` | Daily (22 sessions) |
| `F2` | BID — Proprietary Trading (Net Volume, Value) | `fact_proprietary_trading` | Daily (22 sessions) |
| `F3` | BID — Price History (OHLCV) | `fact_price_history` | Daily (22 sessions) |
| `F4` | BID — Order Statistics (Buy/Sell Orders, Matched Vol) | `fact_order_stats` | Daily (22 sessions) |
| `F5` | HPG — Intraday Tick Matching (~10,000 ticks) | `fact_intraday_matching` | Tick-level (1 session: 2026-06-19) |
| `F6–F7` | 46 Commercial Banks — CAMELS Financials (2002–2022) | `fact_bank_performance` | Annual / per bank |

---

## 2. Stock Market Variables (BID and HPG)

### 2.1 Foreign Trading (`fact_foreign_trading`)

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| Date | `date_key` | INT64 (FK) | Trading date in YYYYMMDD format |
| Ticker | `stock_key` | INT64 (FK) | References `dim_stock` |
| Foreign Buy Volume | `foreign_buy_volume` | INT64 | Total shares purchased by foreign investors |
| Foreign Sell Volume | `foreign_sell_volume` | INT64 | Total shares sold by foreign investors |
| Foreign Net Volume | `foreign_net_volume` | INT64 | Buy Volume minus Sell Volume |
| Foreign Net Value | `foreign_net_value` | FLOAT64 | Net transaction value in VND billions |
| Foreign Ownership Ratio | `foreign_ownership_ratio` | FLOAT64 | Percentage of shares held by foreign investors |

### 2.2 Proprietary Trading (`fact_proprietary_trading`)

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| Date | `date_key` | INT64 (FK) | Trading date in YYYYMMDD format |
| Ticker | `stock_key` | INT64 (FK) | References `dim_stock` |
| Prop Buy Volume | `prop_buy_volume` | INT64 | Total shares purchased by proprietary desks (Khối tự doanh) |
| Prop Sell Volume | `prop_sell_volume` | INT64 | Total shares sold by proprietary desks |
| Prop Net Volume | `prop_net_volume` | INT64 | Buy minus Sell volume |
| Prop Net Value | `prop_net_value` | FLOAT64 | Net value in VND billions |

### 2.3 Price History OHLCV (`fact_price_history`)

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| Date | `date_key` | INT64 (FK) | Trading date in YYYYMMDD format |
| Ticker | `stock_key` | INT64 (FK) | References `dim_stock` |
| Open | `open_price` | FLOAT64 | Opening price of the session (VND) |
| High | `high_price` | FLOAT64 | Highest traded price of the session (VND) |
| Low | `low_price` | FLOAT64 | Lowest traded price of the session (VND) |
| Close | `close_price` | FLOAT64 | **Primary LSTM target variable.** Closing price (VND) |
| Volume | `trading_volume` | INT64 | Total matched volume in the session |

### 2.4 Order Statistics (`fact_order_stats`)

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| Date | `date_key` | INT64 (FK) | Trading date |
| Ticker | `stock_key` | INT64 (FK) | References `dim_stock` |
| Total Buy Orders | `total_buy_orders` | INT64 | Number of buy order placements |
| Total Buy Volume | `total_buy_volume` | INT64 | Total volume in buy orders |
| Total Sell Orders | `total_sell_orders` | INT64 | Number of sell order placements |
| Total Sell Volume | `total_sell_volume` | INT64 | Total volume in sell orders |
| Matched Volume | `matched_volume` | INT64 | Total volume successfully matched |

### 2.5 Intraday Tick Matching — HPG (`fact_intraday_matching`)

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| Timestamp | `timestamp` | TIMESTAMP | Exact HH:MM:SS of the matched trade |
| Date | `date_key` | INT64 (FK) | Trading date (2026-06-19) |
| Ticker | `stock_key` | INT64 (FK) | References `dim_stock` (HPG) |
| Session | `session_key` | INT64 (FK) | References `dim_trading_session` |
| Matched Price | `matched_price` | FLOAT64 | Price at which the order was executed (VND) |
| Matched Volume | `matched_volume` | INT64 | Volume executed at this tick |
| Cumulative Volume | `cumulative_volume` | INT64 | Running total of matched volume within the session |

---

## 3. Bank Financial Variables — CAMELS Framework

**Source**: 46 commercial banks, 2002–2022 (approximately 667 rows, 47+ columns).

### 3.1 Identification Variables

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| Bank Code | `bank_code` | STRING | Standardized ticker such as VCB, BID, TCB |
| Year | `date_key` | INT64 (FK) | Reporting year mapped to `dim_date` |
| Bank | `bank_key` | INT64 (FK) | References `dim_bank` |

### 3.2 Scale Variables

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| TASSETS | `total_assets` | FLOAT64 | Total assets (VND billions) |
| DEPOSITS | `total_deposits` | FLOAT64 | Total customer deposits (VND billions) |
| LOANS | `total_loans` | FLOAT64 | Total loan portfolio (VND billions) |
| EQUITY | `total_equity` | FLOAT64 | Total shareholder equity (VND billions) |
| NE | `num_employees` | INT64 | Number of employees |
| NB | `num_branches` | INT64 | Number of branches |

### 3.3 Asset Quality Variables

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| NPL | `npl_amount` | FLOAT64 | Non-Performing Loan balance (VND billions) |
| NPLRATIO | `npl_ratio` | FLOAT64 | **Classification target variable.** NPL / Total Loans. Threshold ≥ 3% = High Risk |
| LLP | `loan_loss_provision` | FLOAT64 | Loan Loss Provision balance (VND billions) |
| LLPRATIO | `llp_ratio` | FLOAT64 | LLP / Total Loans — proxy for credit risk conservatism |

### 3.4 Income and Expense Variables

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| II | `interest_income` | FLOAT64 | Total interest income (VND billions) |
| IE | `interest_expense` | FLOAT64 | Total interest expense (VND billions) |
| NI | `net_interest_income` | FLOAT64 | II minus IE |
| NIE | `non_interest_expense` | FLOAT64 | Operating expenses excluding interest |
| PE | `personnel_expense` | FLOAT64 | Staff and salary costs |
| OE | `other_expense` | FLOAT64 | Other operating expenses |
| PBT | `profit_before_tax` | FLOAT64 | Profit before tax (VND billions) |
| PAT | `profit_after_tax` | FLOAT64 | Profit after tax (VND billions) |
| OBS | `off_balance_sheet` | FLOAT64 | Off-balance-sheet exposures (VND billions) |

### 3.5 CAMELS Performance Ratios (Primary ML Features)

| Raw Column | Canonical Field | BigQuery Type | CAMELS Component | Description |
|------------|-----------------|---------------|-----------------|-------------|
| ROA | `roa` | FLOAT64 | Earnings (E) | Return on Assets = PAT / TASSETS |
| ROE | `roe` | FLOAT64 | Earnings (E) | Return on Equity = PAT / EQUITY |
| NIM | `nim` | FLOAT64 | Earnings (E) | Net Interest Margin = NI / TASSETS |
| CIR | `cir` | FLOAT64 | Earnings (E) | Cost-to-Income Ratio = NIE / (NI + Non-interest Income) |
| ETA | `eta` | FLOAT64 | Capital (C) | Equity-to-Total Assets = EQUITY / TASSETS |
| ETD | `etd` | FLOAT64 | Capital (C) | Equity-to-Total Deposits |
| LTA | `lta` | FLOAT64 | Liquidity (L) | Loans-to-Total Assets = LOANS / TASSETS |
| LTD | `ltd` | FLOAT64 | Liquidity (L) | Loans-to-Total Deposits = LOANS / DEPOSITS |
| GTA | `gta` | FLOAT64 | Sensitivity (S) | Gross Loans-to-Total Assets |

---

## 4. Derived / Engineered Features

The following features are created during the Feature Engineering step and are not present in the raw Excel sources.

| Feature Name | Derived From | Purpose |
|--------------|-------------|---------|
| `price_change_pct` | `close_price` | Daily percentage change for momentum signal in LSTM |
| `active_buy_ratio` | `total_buy_orders` / (`total_buy_orders` + `total_sell_orders`) | Market sentiment indicator for intraday HPG analysis |
| `risk_label` | `npl_ratio` ≥ 0.03 → 1, else 0 | Binary target variable for Random Forest classification |
| `foreign_net_lag_1` | `foreign_net_volume` shifted by 1 day | Lagged foreign flow signal as LSTM regressor |
| `prop_net_lag_1` | `prop_net_volume` shifted by 1 day | Lagged proprietary flow signal as LSTM regressor |

---

## 5. Data Quality Rules and Constraints

| Rule ID | Scope | Rule | Action on Violation |
|---------|-------|------|---------------------|
| DQ-01 | All Fact tables | `date_key` must reference a valid row in `dim_date` | Reject record; log error |
| DQ-02 | `fact_bank_performance` | `npl_ratio` must be in range [0.0, 1.0] | Flag for manual review |
| DQ-03 | `fact_price_history` | `close_price` must be > 0 | Reject record; log error |
| DQ-04 | `fact_bank_performance` | Missing values for years 2002–2005 must be imputed using column median | Impute during ETL Transform step |
| DQ-05 | `fact_intraday_matching` | `timestamp` must fall within valid HOSE session hours (09:00–14:30) | Reject out-of-range ticks |
| DQ-06 | `fact_foreign_trading` | `foreign_buy_volume` and `foreign_sell_volume` must be ≥ 0 | Reject negative values |
