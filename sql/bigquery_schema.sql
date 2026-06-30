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
  is_trading_day BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_stock` (
  stock_key INT64 NOT NULL,
  ticker STRING NOT NULL,
  company_name STRING,
  exchange STRING,
  industry STRING
);

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_bank` (
  bank_key INT64 NOT NULL,
  bank_code STRING NOT NULL,
  bank_name STRING,
  bank_type STRING,
  charter_capital FLOAT64
);

CREATE TABLE IF NOT EXISTS `{dataset_id}.dim_trading_session` (
  session_key INT64 NOT NULL,
  session_name STRING NOT NULL,
  start_time TIME,
  end_time TIME
);

-- ------------------------------------------------------------
-- 2. Fact Tables
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_price_history` (
  date_key INT64 NOT NULL,
  stock_key INT64 NOT NULL,
  open_price FLOAT64,
  high_price FLOAT64,
  low_price FLOAT64,
  close_price FLOAT64,
  trading_volume INT64
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY stock_key;

CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_foreign_trading` (
  date_key INT64 NOT NULL,
  stock_key INT64 NOT NULL,
  foreign_buy_volume INT64,
  foreign_sell_volume INT64,
  foreign_net_volume INT64,
  foreign_net_value FLOAT64,
  foreign_ownership_ratio FLOAT64
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY stock_key;

CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_proprietary_trading` (
  date_key INT64 NOT NULL,
  stock_key INT64 NOT NULL,
  prop_buy_volume INT64,
  prop_sell_volume INT64,
  prop_net_volume INT64,
  prop_net_value FLOAT64
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY stock_key;

CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_order_stats` (
  date_key INT64 NOT NULL,
  stock_key INT64 NOT NULL,
  total_buy_orders INT64,
  total_buy_volume INT64,
  total_sell_orders INT64,
  total_sell_volume INT64,
  matched_volume INT64
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY stock_key;

CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_intraday_matching` (
  date_key INT64 NOT NULL,
  stock_key INT64 NOT NULL,
  session_key INT64 NOT NULL,
  timestamp TIMESTAMP,
  matched_price FLOAT64,
  matched_volume INT64,
  cumulative_volume INT64
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY stock_key;

CREATE TABLE IF NOT EXISTS `{dataset_id}.fact_bank_performance` (
  date_key INT64 NOT NULL,
  bank_key INT64 NOT NULL,
  total_assets FLOAT64,
  total_deposits FLOAT64,
  total_loans FLOAT64,
  npl_ratio FLOAT64,
  roa FLOAT64,
  roe FLOAT64,
  nim FLOAT64,
  cir FLOAT64,
  is_imputed BOOLEAN
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))
CLUSTER BY bank_key;
