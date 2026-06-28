"""Task B-14 / B-15: Referential integrity and data quality validation.

Validates the local cleaned CSV files in data/processed/ to ensure they conform
to the Star Schema referential integrity and Data Quality (DQ-01 to DQ-06) rules.
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_pipeline() -> bool:
    processed_dir = Path(os.getenv("PROCESSED_DATA_PATH", "./data/processed/"))
    if not processed_dir.exists():
        logger.error("Processed data directory %s does not exist. Run ETL scripts first.", processed_dir)
        return False

    errors_count = 0

    # 1. Load Dimension Tables
    dims = {}
    dim_files = {
        "dim_date": "dim_date_clean.csv",
        "dim_stock": "dim_stock_clean.csv",
        "dim_bank": "dim_bank_clean.csv",
        "dim_trading_session": "dim_trading_session_clean.csv",
    }
    
    for name, filename in dim_files.items():
        filepath = processed_dir / filename
        if not filepath.exists():
            logger.error("Missing dimension file: %s", filepath)
            return False
        dims[name] = pd.read_csv(filepath)
        logger.info("Loaded %d rows from %s for validation.", len(dims[name]), filename)

    # 2. Load Fact Tables
    facts = {}
    fact_files = {
        "fact_price_history": "fact_price_history_clean.csv",
        "fact_foreign_trading": "fact_foreign_trading_clean.csv",
        "fact_proprietary_trading": "fact_proprietary_trading_clean.csv",
        "fact_order_stats": "fact_order_stats_clean.csv",
        "fact_intraday_matching": "fact_intraday_matching_clean.csv",
        "fact_bank_performance": "fact_bank_performance_clean.csv",
    }

    for name, filename in fact_files.items():
        filepath = processed_dir / filename
        if not filepath.exists():
            logger.warning("Missing fact file: %s. Skipping this table's check.", filepath)
            continue
        facts[name] = pd.read_csv(filepath)
        logger.info("Loaded %d rows from %s for validation.", len(facts[name]), filename)

    logger.info("=== STARTING REFERENTIAL INTEGRITY CHECKS (B-14) ===")
    
    # Check 1: Date Key reference
    for name, df in facts.items():
        missing_dates = df.loc[~df["date_key"].isin(dims["dim_date"]["date_key"]), "date_key"].unique()
        if len(missing_dates) > 0:
            logger.error("[%s] Found date_keys not in dim_date: %s", name, missing_dates)
            errors_count += len(missing_dates)
        else:
            logger.info("[%s] All date_key values are valid in dim_date.", name)

    # Check 2: Stock Key reference
    stock_facts = ["fact_price_history", "fact_foreign_trading", "fact_proprietary_trading", "fact_order_stats", "fact_intraday_matching"]
    for name in stock_facts:
        if name in facts:
            df = facts[name]
            missing_stocks = df.loc[~df["stock_key"].isin(dims["dim_stock"]["stock_key"]), "stock_key"].unique()
            if len(missing_stocks) > 0:
                logger.error("[%s] Found stock_keys not in dim_stock: %s", name, missing_stocks)
                errors_count += len(missing_stocks)
            else:
                logger.info("[%s] All stock_key values are valid in dim_stock.", name)

    # Check 3: Bank Key reference
    if "fact_bank_performance" in facts:
        df = facts["fact_bank_performance"]
        missing_banks = df.loc[~df["bank_key"].isin(dims["dim_bank"]["bank_key"]), "bank_key"].unique()
        if len(missing_banks) > 0:
            logger.error("[fact_bank_performance] Found bank_keys not in dim_bank: %s", missing_banks)
            errors_count += len(missing_banks)
        else:
            logger.info("[fact_bank_performance] All bank_key values are valid in dim_bank.")

    # Check 4: Session Key reference
    if "fact_intraday_matching" in facts:
        df = facts["fact_intraday_matching"]
        missing_sessions = df.loc[~df["session_key"].isin(dims["dim_trading_session"]["session_key"]), "session_key"].unique()
        if len(missing_sessions) > 0:
            logger.error("[fact_intraday_matching] Found session_keys not in dim_trading_session: %s", missing_sessions)
            errors_count += len(missing_sessions)
        else:
            logger.info("[fact_intraday_matching] All session_key values are valid in dim_trading_session.")

    logger.info("=== STARTING DATA QUALITY CHECKS (B-15) ===")

    # DQ-01 & DQ-02: Keys not null
    for name, df in facts.items():
        if df["date_key"].isna().any():
            logger.error("[%s] Found null values in date_key.", name)
            errors_count += 1
        key_col = "bank_key" if name == "fact_bank_performance" else "stock_key"
        if df[key_col].isna().any():
            logger.error("[%s] Found null values in %s.", name, key_col)
            errors_count += 1

    # DQ-03: close_price not null
    if "fact_price_history" in facts:
        df = facts["fact_price_history"]
        if df["close_price"].isna().any():
            logger.error("[fact_price_history] Found null values in close_price.")
            errors_count += 1

    # DQ-04: npl_ratio not null after imputation
    if "fact_bank_performance" in facts:
        df = facts["fact_bank_performance"]
        if df["npl_ratio"].isna().any():
            logger.error("[fact_bank_performance] Found null values in npl_ratio.")
            errors_count += 1

    # DQ-05: Intraday matching times are valid HOSE hours (session_key is not -1)
    if "fact_intraday_matching" in facts:
        df = facts["fact_intraday_matching"]
        invalid_sessions = (df["session_key"] == -1).sum()
        if invalid_sessions > 0:
            logger.error("[fact_intraday_matching] Found %d records with invalid session hours (-1).", invalid_sessions)
            errors_count += invalid_sessions

    # DQ-06: Duplicates check (primary keys must be unique)
    pk_definitions = {
        "dim_date": ["date_key"],
        "dim_stock": ["stock_key"],
        "dim_bank": ["bank_key"],
        "dim_trading_session": ["session_key"],
        "fact_price_history": ["date_key", "stock_key"],
        "fact_foreign_trading": ["date_key", "stock_key"],
        "fact_proprietary_trading": ["date_key", "stock_key"],
        "fact_order_stats": ["date_key", "stock_key"],
        "fact_bank_performance": ["date_key", "bank_key"],
    }

    all_tables = {**dims, **facts}
    for name, df in all_tables.items():
        if name in pk_definitions:
            pks = pk_definitions[name]
            dups = df.duplicated(subset=pks).sum()
            if dups > 0:
                logger.error("[%s] Found %d duplicate records on primary keys %s.", name, dups, pks)
                errors_count += dups
            else:
                logger.info("[%s] Primary key uniqueness validated.", name)

    logger.info("=== VALIDATION COMPLETED. TOTAL ERRORS FOUND: %d ===", errors_count)
    return errors_count == 0


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    success = validate_pipeline()
    import sys
    sys.exit(0 if success else 1)
