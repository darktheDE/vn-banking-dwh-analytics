-- ============================================================
-- BigQuery DDL: Financial Data Analytics Platform Star Schema
-- See docs/star-schema.md for full specification.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Dimension Tables
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_date` (
  date_key INT64 NOT NULL,
  full_date DATE NOT NULL,
  day INT64 NOT NULL,
  month INT64 NOT NULL,
  year INT64 NOT NULL,
  quarter INT64 NOT NULL,
  is_trading_day BOOLEAN NOT NULL,
  audit_key INT64 NOT NULL,
  _created_at TIMESTAMP,
  _updated_at TIMESTAMP,
  _source_file STRING
);

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_stock` (
  stock_key INT64 NOT NULL,
  ticker STRING NOT NULL,
  company_name STRING,
  exchange STRING,
  industry STRING,
  audit_key INT64 NOT NULL,
  _created_at TIMESTAMP,
  _updated_at TIMESTAMP,
  _source_file STRING
);

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_bank` (
  bank_key INT64 NOT NULL,
  bank_code STRING NOT NULL,
  bank_name STRING,
  bank_type STRING,
  charter_capital FLOAT64,
  valid_from DATE,
  valid_to DATE,
  is_current BOOLEAN,
  audit_key INT64 NOT NULL,
  _created_at TIMESTAMP,
  _updated_at TIMESTAMP,
  _source_file STRING
);

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_trading_session` (
  session_key INT64 NOT NULL,
  session_name STRING NOT NULL,
  start_time TIME,
  end_time TIME,
  audit_key INT64 NOT NULL,
  _created_at TIMESTAMP,
  _updated_at TIMESTAMP,
  _source_file STRING
);

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_audit` (
  audit_key INT64 NOT NULL,
  run_id STRING NOT NULL,
  run_timestamp TIMESTAMP NOT NULL,
  script_name STRING NOT NULL,
  source_file STRING,
  rows_processed INT64,
  status STRING
);

-- ------------------------------------------------------------
-- 2. Fact Tables
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_stock_daily_metrics` (
  date_key INT64 NOT NULL,
  stock_key INT64 NOT NULL,
  open_price FLOAT64,
  high_price FLOAT64,
  low_price FLOAT64,
  close_price FLOAT64,
  trading_volume INT64,
  audit_key INT64 NOT NULL,
  _created_at TIMESTAMP,
  _updated_at TIMESTAMP,
  _source_file STRING
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY stock_key;


CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_bank_performance` (
  date_key INT64 NOT NULL,
  bank_key INT64 NOT NULL,
  total_assets FLOAT64,
  total_deposits FLOAT64,
  total_loans FLOAT64,
  total_equity FLOAT64,
  num_employees INT64,
  num_branches INT64,
  npl_amount FLOAT64,
  loan_loss_provision FLOAT64,
  interest_income FLOAT64,
  interest_expense FLOAT64,
  net_interest_income FLOAT64,
  non_interest_expense FLOAT64,
  personnel_expense FLOAT64,
  other_expense FLOAT64,
  profit_before_tax FLOAT64,
  profit_after_tax FLOAT64,
  off_balance_sheet FLOAT64,
  npl_ratio FLOAT64,
  llp_ratio FLOAT64,
  roa FLOAT64,
  roe FLOAT64,
  nim FLOAT64,
  cir FLOAT64,
  eta FLOAT64,
  etd FLOAT64,
  lta FLOAT64,
  ltd FLOAT64,
  gta FLOAT64,
  is_imputed BOOLEAN,
  audit_key INT64 NOT NULL,
  _created_at TIMESTAMP,
  _updated_at TIMESTAMP,
  _source_file STRING
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY bank_key;
