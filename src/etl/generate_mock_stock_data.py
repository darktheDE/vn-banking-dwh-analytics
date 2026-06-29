"""Utility to generate mock raw stock Excel files.

Generates the missing raw Excel files in data/raw/ so the local ETL pipeline
can run and be tested end-to-end.
"""

from __future__ import annotations

import os
from pathlib import Path
import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_all_mock_data():
    raw_dir = Path("./data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Price History (Extract last 22 rows of bid_stock_history.csv and convert to Excel)
    csv_path = Path("./data/bid_stock_history.csv")
    if csv_path.exists():
        df_csv = pd.read_csv(csv_path)
        df_price = df_csv.tail(22).copy()
        # Rename columns to match raw Excel specification in etl-spec.md
        df_price = df_price.rename(columns={
            "time": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        })
    else:
        logger.warning("bid_stock_history.csv not found, generating random price history.")
        dates = pd.date_range(start="2026-05-19", periods=22, freq="B")
        df_price = pd.DataFrame({
            "Date": dates.strftime("%Y-%m-%d"),
            "Open": np.random.uniform(40.0, 45.0, 22),
            "High": np.random.uniform(45.0, 48.0, 22),
            "Low": np.random.uniform(38.0, 40.0, 22),
            "Close": np.random.uniform(40.0, 45.0, 22),
            "Volume": np.random.randint(500000, 2000000, 22)
        })
        
    price_excel_path = raw_dir / "BID_price_history.xlsx"
    df_price.to_excel(price_excel_path, index=False)
    logger.info("Saved mock price history to %s", price_excel_path)
    
    # Get the 22 dates used
    dates = df_price["Date"].tolist()
    
    # 2. Foreign Trading Excel
    df_foreign = pd.DataFrame({
        "Date": dates,
        "Foreign Buy Volume": np.random.randint(10000, 100000, 22),
        "Foreign Sell Volume": np.random.randint(10000, 100000, 22),
        "Foreign Ownership Ratio": np.random.uniform(0.15, 0.18, 22)
    })
    # Compute Net Volume and Net Value (in billions VND)
    df_foreign["Foreign Net Volume"] = df_foreign["Foreign Buy Volume"] - df_foreign["Foreign Sell Volume"]
    df_foreign["Foreign Net Value"] = df_foreign["Foreign Net Volume"] * np.random.uniform(0.040, 0.045, 22) / 1000.0 # simple scale
    
    foreign_excel_path = raw_dir / "BID_foreign_trading.xlsx"
    df_foreign.to_excel(foreign_excel_path, index=False)
    logger.info("Saved mock foreign trading to %s", foreign_excel_path)
    
    # 3. Proprietary Trading Excel
    df_prop = pd.DataFrame({
        "Date": dates,
        "Prop Buy Volume": np.random.randint(5000, 50000, 22),
        "Prop Sell Volume": np.random.randint(5000, 50000, 22),
    })
    df_prop["Prop Net Volume"] = df_prop["Prop Buy Volume"] - df_prop["Prop Sell Volume"]
    df_prop["Prop Net Value"] = df_prop["Prop Net Volume"] * np.random.uniform(0.040, 0.045, 22) / 1000.0
    
    prop_excel_path = raw_dir / "BID_proprietary_trading.xlsx"
    df_prop.to_excel(prop_excel_path, index=False)
    logger.info("Saved mock proprietary trading to %s", prop_excel_path)
    
    # 4. Order Statistics Excel
    df_order = pd.DataFrame({
        "Date": dates,
        "Total Buy Orders": np.random.randint(1000, 5000, 22),
        "Total Buy Volume": np.random.randint(1000000, 5000000, 22),
        "Total Sell Orders": np.random.randint(1000, 5000, 22),
        "Total Sell Volume": np.random.randint(1000000, 5000000, 22),
        "Matched Volume": np.random.randint(500000, 2000000, 22)
    })
    order_excel_path = raw_dir / "BID_order_stats.xlsx"
    df_order.to_excel(order_excel_path, index=False)
    logger.info("Saved mock order stats to %s", order_excel_path)
    
    # 5. HPG Intraday Ticks Excel (~10,000 rows for 2026-06-19)
    # Generate timestamps from 09:00:00 to 14:45:00
    times = []
    # ATO: 09:00 to 09:15 (e.g. 500 ticks)
    # Morning: 09:15 to 11:30 (e.g. 4500 ticks)
    # Afternoon: 13:00 to 14:30 (e.g. 4500 ticks)
    # ATC: 14:30 to 14:45 (e.g. 500 ticks)
    
    np.random.seed(42)
    
    # Generate timestamps
    def gen_times(start_h, start_m, end_h, end_m, num_ticks):
        start_sec = start_h * 3600 + start_m * 60
        end_sec = end_h * 3600 + end_m * 60
        secs = np.sort(np.random.randint(start_sec, end_sec, num_ticks))
        return [f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}" for s in secs]
        
    ato_times = gen_times(9, 0, 9, 15, 500)
    morning_times = gen_times(9, 15, 11, 30, 4500)
    afternoon_times = gen_times(13, 0, 14, 30, 4500)
    atc_times = gen_times(14, 30, 14, 45, 500)
    
    all_times = ato_times + morning_times + afternoon_times + atc_times
    n_ticks = len(all_times)
    
    # Price path: starting at 28.5 (VND thousands)
    price_changes = np.random.normal(0, 0.05, n_ticks)
    prices = 28.5 + np.cumsum(price_changes)
    # execution volume per tick
    volumes = np.random.randint(10, 500, n_ticks) * 10
    
    # Cumulative volume is running sum within each session
    # Actually cumulative volume in HOSE is cumulative over the whole day
    cum_volumes = []
    current_cum = 0
    for v in volumes:
        current_cum += v
        cum_volumes.append(current_cum)
        
    df_hpg = pd.DataFrame({
        "Time / Thời gian": all_times,
        "Matched Price": np.round(prices, 2),
        "Matched Volume": volumes,
        "Cumulative Volume": cum_volumes
    })
    
    hpg_excel_path = raw_dir / "HPG_intraday_ticks.xlsx"
    df_hpg.to_excel(hpg_excel_path, index=False)
    logger.info("Saved mock HPG intraday ticks to %s. Rows: %d", hpg_excel_path, len(df_hpg))


if __name__ == "__main__":
    generate_all_mock_data()
