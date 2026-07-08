# Data Dictionary

## Overview

This document defines all data entities, source fields, and derived variables used across the Financial Data Analytics Platform. It serves as the **authoritative data contract** between the ETL layer, the BigQuery Star Schema, and the Machine Learning models.

**Ground Truth**: The raw data originates from 7 structured Excel files. This dictionary maps raw source columns to their canonical BigQuery field names and data types.

---

## 1. Source File Inventory

| File ID | Source File Description | Target Fact Table | Granularity |
|---------|------------------------|-------------------|-------------|
| `F3` | BID, TCB, VCB, CTG — Price History (OHLCV) | `fact_stock_daily_metrics` | Daily (11,835 rows total) |
| `F6–F7` | 45 Commercial Banks — CAMELS Financials (2002–2022) | `fact_bank_performance` | Annual / per bank |

---

## 2. Stock Market Variables (BID, TCB, VCB, CTG)

### 2.1 Daily Stock Metrics (`fact_stock_daily_metrics`)

| Raw Column | Canonical Field | BigQuery Type | Description |
|------------|-----------------|---------------|-------------|
| Date | `date_key` | INT64 (FK) | Trading date in YYYYMMDD format |
| Ticker | `stock_key` | INT64 (FK) | References `dim_stock` |
| Open | `open_price` | FLOAT64 | Opening price of the session (VND) |
| High | `high_price` | FLOAT64 | Highest traded price of the session (VND) |
| Low | `low_price` | FLOAT64 | Lowest traded price of the session (VND) |
| Close | `close_price` | FLOAT64 | **Primary LSTM target variable.** Closing price (VND) |
| Volume | `trading_volume` | INT64 | Total matched volume in the session |



---

## 3. Bank Financial Variables — CAMELS Framework

**Source**: 45 commercial banks, 2002–2022 (approximately 667 rows, 47+ columns).

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
| `active_buy_ratio` | `total_buy_orders` / (`total_buy_orders` + `total_sell_orders`) | Market sentiment indicator for order statistics analysis |
| `risk_label` | `npl_ratio` ≥ 0.03 → 1, else 0 | Binary target variable for Random Forest classification |
| `foreign_net_lag_1` | `foreign_net_volume` shifted by 1 day | Lagged foreign flow signal as LSTM regressor |
| `prop_net_lag_1` | `prop_net_volume` shifted by 1 day | Lagged proprietary flow signal as LSTM regressor |

### 4.2 Machine Learning Prediction Outputs

These fields are populated by the ML training and inference runs and stored in target BigQuery tables:

#### 4.2.1 `bank_cluster_assignments` (K-Means Clustering)
- `bank_key` (INT64): References `dim_bank.bank_key`.
- `bank_code` (STRING): Ticker code of the bank.
- `bank_name` (STRING): Corporate name of the bank.
- `bank_type` (STRING): Classification (`SOCB`/`JSCB`/`FOCB`).
- `cluster_id` (INT64): Strategic cluster assigned to the bank.
- `model_name` (STRING): Deployed model label (e.g. `'KMeans_PCA'`).

#### 4.2.2 `bank_risk_predictions` (Random Forest Classification)
- `bank_key` (INT64): References `dim_bank.bank_key`.
- `bank_code` (STRING): Standard bank code.
- `date_key` (INT64): Target reporting year key.
- `risk_label` (INT64): Risk classification (`1` if NPL ratio ≥ 3%, `0` otherwise).
- `risk_probability` (FLOAT64): RF model probability score.
- `actual_npl_ratio` (FLOAT64): True historical NPL ratio.
- `model_name` (STRING): Model label (e.g. `'RandomForest_Classifier'`).

#### 4.2.3 `fact_model_predictions` (LSTM Time Series Forecasting)
- `base_date_key` (INT64): The date of prediction generation.
- `stock_key` (INT64): References `dim_stock.stock_key`.
- `horizon` (STRING): Forecast window (`'T+1'` through `'T+5'`).
- `predicted_close_price` (FLOAT64): Predicted close price in VND.
- `model_name` (STRING): Model identifier (e.g. `'LSTM_Forecaster'`).

---

## 5. Data Quality Rules and Constraints

| Rule ID | Scope | Rule | Action on Violation |
|---------|-------|------|---------------------|
| DQ-01 | All Fact tables | `date_key` must reference a valid row in `dim_date` | Reject record; log error |
| DQ-02 | `fact_bank_performance` | `npl_ratio` must be in range [0.0, 1.0] | Flag for manual review |
| DQ-03 | `fact_stock_daily_metrics` | `close_price` must be > 0 | Reject record; log error |
| DQ-04 | `fact_bank_performance` | Missing values for years 2002–2005 must be imputed using column median | Impute during ETL Transform step |
| DQ-05 | All tables | `audit_key` must be present and not null | Reject record; log error |
| DQ-06 | `fact_stock_daily_metrics` | `foreign_buy_volume` and `foreign_sell_volume` must be ≥ 0 (when present) | Reject negative values |
