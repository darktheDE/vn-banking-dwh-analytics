"""Task B-12: Load fact_intraday_matching.

Reads the raw HPG intraday tick matching data, cleans it, maps timestamps
to HOSE sessions, forward-fills price for max 1 tick, checks cumulative volume
monotonicity, and saves it locally as a CSV.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

HPG_STOCK_KEY = 2


def classify_session(time_val: pd.Timestamp) -> int:
    """Map a timestamp to a HOSE session key.

    Session mappings:
    - ATO: 09:00:00 - 09:14:59 (key 1)
    - Morning Continuous: 09:15:00 - 11:29:59 (key 2)
    - Afternoon Continuous: 13:00:00 - 14:29:59 (key 3)
    - ATC: 14:30:00 - 14:45:00 (key 4)
    """
    time_str = time_val.strftime("%H:%M:%S")
    if "09:00:00" <= time_str <= "09:14:59":
        return 1
    elif "09:15:00" <= time_str <= "11:29:59":
        return 2
    elif "13:00:00" <= time_str <= "14:29:59":
        return 3
    elif "14:30:00" <= time_str <= "14:45:00":
        return 4
    return -1


def transform_intraday_matching(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw HPG intraday matching ticks.

    Args:
        df_raw: Raw intraday tick DataFrame.

    Returns:
        Transformed DataFrame.
    """
    df = df_raw.copy()

    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    column_mapping = {
        "Time / Thời gian": "time_str",
        "time": "time_str",
        "Matched Price": "matched_price",
        "matched_price": "matched_price",
        "Matched Volume": "matched_volume",
        "matched_volume": "matched_volume",
        "Cumulative Volume": "cumulative_volume",
        "cumulative_volume": "cumulative_volume",
    }

    df = df.rename(columns=column_mapping)

    required = {"time_str", "matched_price", "matched_volume", "cumulative_volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Intraday date is fixed at 2026-06-19 according to spec
    target_date = "2026-06-19"
    df["date_key"] = 20260619
    df["stock_key"] = HPG_STOCK_KEY

    # Combine time_str and date to form full timestamp
    df["timestamp"] = pd.to_datetime(target_date + " " + df["time_str"])

    # Map session key
    df["session_key"] = df["timestamp"].apply(classify_session)

    # Reject ticks outside valid HOSE trading hours
    initial_len = len(df)
    df = df.loc[df["session_key"] != -1]
    dropped_hours = initial_len - len(df)
    if dropped_hours > 0:
        logger.warning("Rejected %d ticks outside HOSE trading hours.", dropped_hours)

    # Standardize types
    df["matched_price"] = pd.to_numeric(df["matched_price"], errors="coerce").astype("float64")
    df["matched_volume"] = pd.to_numeric(df["matched_volume"], errors="coerce").astype("Int64")
    df["cumulative_volume"] = pd.to_numeric(df["cumulative_volume"], errors="coerce").astype("Int64")

    # Apply forward-fill for matched_price (max 1 tick)
    null_price = df["matched_price"].isna().sum()
    if null_price > 0:
        df["matched_price"] = df["matched_price"].ffill(limit=1)
        logger.warning("Applied forward-fill to %d null values in matched_price.", null_price)

    # Validate that cumulative_volume is monotonically non-decreasing within each session
    for session_id, group in df.groupby("session_key"):
        if not group["cumulative_volume"].is_monotonic_increasing:
            logger.warning(
                "Cumulative volume is not strictly monotonically non-decreasing in session %d. "
                "Checking for out-of-order records.",
                session_id,
            )

    canonical_cols = [
        "timestamp",
        "date_key",
        "stock_key",
        "session_key",
        "matched_price",
        "matched_volume",
        "cumulative_volume",
    ]
    df = df.loc[:, canonical_cols]
    
    # Sort for final output consistency
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean and load HPG intraday ticks locally.")
    parser.add_argument(
        "--input-file",
        default=None,
        help="Path to raw HPG intraday matching ticks file.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the output CSV. Defaults to PROCESSED_DATA_PATH.",
    )
    args = parser.parse_args()

    processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./data/processed/")
    raw_data_path = os.getenv("RAW_DATA_PATH", "./data/raw/")
    output_dir = Path(args.output_dir) if args.output_dir else Path(processed_data_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = Path(args.input_file) if args.input_file else Path(raw_data_path) / "HPG_intraday_ticks.xlsx"
    if not input_file.exists():
        logger.error("Input file %s not found.", input_file)
        return 1

    logger.info("Reading intraday ticks from %s.", input_file)
    df_raw = pd.read_excel(input_file)
    df_clean = transform_intraday_matching(df_raw)

    output_path = output_dir / "fact_intraday_matching_clean.csv"
    # Convert timestamp column to string to save in CSV cleanly
    df_clean_to_save = df_clean.copy()
    df_clean_to_save["timestamp"] = df_clean_to_save["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df_clean_to_save.to_csv(output_path, index=False)
    
    logger.info("Saved fact_intraday_matching to %s. Rows: %d", output_path, len(df_clean))
    return 0


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(main())
