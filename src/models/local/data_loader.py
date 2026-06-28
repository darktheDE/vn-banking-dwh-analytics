"""
Data Loader — Chuẩn bị dữ liệu cho ML từ local CSV.

Module này đọc dữ liệu từ thư mục data/processed/, xử lý và xuất ra
các file CSV sẵn sàng cho các mô hình ML tại thư mục data/ML_data/.

Nguồn dữ liệu:
  - fact_bank_performance_clean.csv (46 ngân hàng, 2002-2022, 667 dòng)
    -> Dùng cho K-Means Clustering và Random Forest Classification
  - dim_bank_clean.csv (thông tin định danh ngân hàng)
    -> Dùng để ghép tên ngân hàng vào kết quả
  - bid/bid_stock_history.csv (3091 ngày giao dịch, 2014-2026)
    -> Dùng cho LSTM Time Series Forecasting
  - Các file tài chính riêng lẻ của 4 ngân hàng (bid, ctg, tcb, vcb)
    -> Dùng để bổ sung dữ liệu mới (2023-2025) cho mô hình clustering/RF
"""

import os
import pandas as pd
import numpy as np

# ==============================================================================
# Đường dẫn
# ==============================================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
ML_DATA_DIR = os.path.join(BASE_DIR, "data", "data_ml")
INPUT_DIR = os.path.join(ML_DATA_DIR, "input")

BANKS = ["bid", "ctg", "tcb", "vcb"]

# Các cột CAMELS dùng cho K-Means và Random Forest
CAMELS_FEATURES = [
    "npl_ratio", "llp_ratio", "roa", "roe", "nim", "cir",
    "eta", "etd", "lta", "ltd", "gta",
]


def ensure_ml_data_dir():
    """Tạo thư mục ML_data nếu chưa tồn tại."""
    os.makedirs(ML_DATA_DIR, exist_ok=True)
    os.makedirs(INPUT_DIR, exist_ok=True)


def process_and_export_bank_camels_data() -> str:
    """Đọc fact_bank_performance_clean.csv (46 ngân hàng) và dim_bank_clean.csv.

    Đây là bộ dữ liệu CAMELS chính thức đã được team ETL tiền xử lý,
    chứa 667 quan sát (45 ngân hàng x ~15 năm). Dữ liệu này phù hợp cho
    cả K-Means (clustering) và Random Forest (classification).

    Returns:
        Đường dẫn tới file CSV đã xuất.
    """
    ensure_ml_data_dir()

    # --- Đọc dữ liệu CAMELS 46 ngân hàng (đã clean) ---
    fact_path = os.path.join(PROCESSED_DIR, "fact_bank_performance_clean.csv")
    dim_path = os.path.join(PROCESSED_DIR, "dim_bank_clean.csv")

    if not os.path.exists(fact_path):
        print(f"[ERROR] File not found: {fact_path}")
        return None

    df_fact = pd.read_csv(fact_path)
    print(f"[INFO] Loaded fact_bank_performance_clean.csv: {df_fact.shape[0]} rows, "
          f"{df_fact['bank_key'].nunique()} unique banks.")

    # --- Ghép dim_bank để lấy bank_code, bank_name ---
    if os.path.exists(dim_path):
        df_dim = pd.read_csv(dim_path)
        df_merged = pd.merge(df_fact, df_dim, on="bank_key", how="left")
        print(f"[INFO] Merged with dim_bank_clean.csv. Columns added: "
              f"{[c for c in df_dim.columns if c != 'bank_key']}")
    else:
        df_merged = df_fact.copy()
        df_merged["bank_code"] = df_merged["bank_key"].astype(str)
        print("[WARNING] dim_bank_clean.csv not found. Using bank_key as bank_code.")

    # --- Tạo cột year từ date_key (YYYYMMDD -> YYYY) ---
    df_merged["year"] = df_merged["date_key"].astype(str).str[:4].astype(int)

    # --- Xử lý npl_ratio bị thiếu: median imputation (theo AGENTS.md) ---
    npl_null_count = df_merged["npl_ratio"].isna().sum()
    if npl_null_count > 0:
        median_val = df_merged.loc[df_merged["year"] >= 2006, "npl_ratio"].median()
        mask = df_merged["npl_ratio"].isna()
        df_merged.loc[mask, "npl_ratio"] = median_val
        print(f"[INFO] Imputed {npl_null_count} null npl_ratio values with median={median_val:.6f}")

    # --- Xuất file ---
    out_path = os.path.join(INPUT_DIR, "banks_camels_46.csv")
    df_merged.to_csv(out_path, index=False)
    print(f"[INFO] Exported 46-bank CAMELS data to {out_path}")
    print(f"       Shape: {df_merged.shape}, NPL >= 3%: {(df_merged['npl_ratio'] >= 0.03).sum()} rows")
    return out_path


def process_and_export_stock_data() -> str:
    """Đọc bid_stock_history.csv và chuẩn bị data cho LSTM.

    File bid_stock_history.csv chứa ~3091 ngày giao dịch (2014-2026) với
    các cột OHLCV. Module này sẽ:
    - Đổi tên cột cho khớp với chuẩn LSTM
    - Tính toán các feature phái sinh (price_change_pct)
    - Loại bỏ các dòng không hợp lệ

    Returns:
        Đường dẫn tới file CSV đã xuất.
    """
    ensure_ml_data_dir()
    stock_path = os.path.join(PROCESSED_DIR, "bid", "bid_stock_history.csv")

    if not os.path.exists(stock_path):
        print(f"[ERROR] BID stock history not found at {stock_path}")
        return None

    df = pd.read_csv(stock_path)

    # --- Đổi tên cột ---
    rename_map = {
        "time": "date",
        "open": "open_price",
        "high": "high_price",
        "low": "low_price",
        "close": "close_price",
        "volume": "trading_volume",
    }
    df = df.rename(columns=rename_map)

    # --- Sắp xếp theo ngày ---
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # --- Loại bỏ dòng có close_price null (theo AGENTS.md) ---
    null_close = df["close_price"].isna().sum()
    if null_close > 0:
        print(f"[WARNING] Dropping {null_close} rows with null close_price.")
        df = df.dropna(subset=["close_price"])

    # --- Feature Engineering ---
    df["price_change_pct"] = df["close_price"].pct_change().fillna(0)
    df["volume_change_pct"] = df["trading_volume"].pct_change().fillna(0)

    # --- Thêm cột cho foreign/proprietary trading (nếu có file riêng) ---
    # Hiện tại file bid_stock_history.csv không chứa dữ liệu ngoại khối/tự doanh.
    # Các file fact_foreign_trading_clean.csv và fact_proprietary_trading_clean.csv
    # chỉ có 22 dòng (tháng 5-6/2026), nên mình sẽ merge nếu có overlap.
    foreign_path = os.path.join(PROCESSED_DIR, "fact_foreign_trading_clean.csv")
    prop_path = os.path.join(PROCESSED_DIR, "fact_proprietary_trading_clean.csv")

    if os.path.exists(foreign_path):
        df_foreign = pd.read_csv(foreign_path)
        if "foreign_buy_volume" in df_foreign.columns and "foreign_sell_volume" in df_foreign.columns:
            df_foreign["foreign_net_volume"] = (
                df_foreign["foreign_buy_volume"] - df_foreign["foreign_sell_volume"]
            )
        print(f"[INFO] Loaded foreign trading data: {len(df_foreign)} rows (reference only).")

    if os.path.exists(prop_path):
        df_prop = pd.read_csv(prop_path)
        print(f"[INFO] Loaded proprietary trading data: {len(df_prop)} rows (reference only).")

    # --- Xuất file ---
    out_path = os.path.join(INPUT_DIR, "bid_lstm_data.csv")
    df.to_csv(out_path, index=False)
    print(f"[INFO] Exported BID LSTM data to {out_path}")
    print(f"       Shape: {df.shape}, Date range: {df['date'].min()} to {df['date'].max()}")
    return out_path


def process_and_export_4bank_financial_data() -> str:
    """Đọc dữ liệu tài chính riêng lẻ của 4 ngân hàng (BID, CTG, TCB, VCB).

    Dữ liệu này bổ sung thêm giai đoạn 2023-2025 (mới hơn so với
    fact_bank_performance_clean.csv chỉ có đến 2022).

    Returns:
        Đường dẫn tới file CSV đã xuất.
    """
    ensure_ml_data_dir()
    all_banks = []

    for bank in BANKS:
        bank_dir = os.path.join(PROCESSED_DIR, bank)
        fr_path = os.path.join(bank_dir, f"{bank}_financial_ratios_annual.csv")

        if not os.path.exists(fr_path):
            print(f"[WARNING] Skipping {bank.upper()}: financial_ratios_annual.csv not found.")
            continue

        df_fr = pd.read_csv(fr_path)
        df_fr["bank_code"] = bank.upper()
        all_banks.append(df_fr)
        print(f"[INFO] Loaded {bank.upper()} financial ratios: {len(df_fr)} rows.")

    if all_banks:
        df_combined = pd.concat(all_banks, ignore_index=True)
        out_path = os.path.join(INPUT_DIR, "banks_4_financial_ratios.csv")
        df_combined.to_csv(out_path, index=False)
        print(f"[INFO] Exported 4-bank financial ratios to {out_path}")
        print(f"       Shape: {df_combined.shape}")
        return out_path
    return None


if __name__ == "__main__":
    print("=" * 70)
    print("DATA LOADER — Chuẩn bị dữ liệu cho ML (Local)")
    print("=" * 70)

    print("\n--- [1/3] Processing 46-bank CAMELS data ---")
    process_and_export_bank_camels_data()

    print("\n--- [2/3] Processing BID stock history for LSTM ---")
    process_and_export_stock_data()

    print("\n--- [3/3] Processing 4-bank financial ratios (supplementary) ---")
    process_and_export_4bank_financial_data()

    print("\n" + "=" * 70)
    print("DATA LOADER COMPLETE. All files saved to data/ML_data/")
    print("=" * 70)
