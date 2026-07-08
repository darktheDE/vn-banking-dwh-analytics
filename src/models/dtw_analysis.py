"""Task 2.2: Dynamic Time Warping (DTW) and Rolling Correlation Analysis.

Aligns closing price series of BID, TCB, VCB, CTG, standardizes them (Z-score),
computes pairwise DTW distances and rolling correlation matrices, and generates plots.
"""

from __future__ import annotations

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.bigquery_client import get_bigquery_client, get_full_table_id

# Set encoding for Windows console print
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def load_and_align_prices() -> pd.DataFrame:
    """Load stock closing prices and align them on common trading dates.
    """
    load_dotenv()
    try:
        client = get_bigquery_client()
        metrics_table = get_full_table_id("fact_stock_daily_metrics")
        stock_table = get_full_table_id("dim_stock")
        
        query = f"""
            SELECT f.date_key, s.ticker, f.close_price
            FROM `{metrics_table}` f
            JOIN `{stock_table}` s ON f.stock_key = s.stock_key
            ORDER BY f.date_key
        """
        df = client.query(query).to_dataframe(create_bqstorage_client=False)
        print("Đã tải dữ liệu giá từ BigQuery.")
    except Exception as e:
        print(f"Không thể kết nối BigQuery ({e}). Đang tải từ file CSV cục bộ...")
        # Fallback to local clean CSV
        csv_path = "./data/processed/fact_stock_daily_metrics_clean.csv"
        df_raw = pd.read_csv(csv_path)
        
        # Load dim_stock to map stock_key to ticker
        stock_csv = "./data/processed/dim_stock_clean.csv"
        df_stock = pd.read_csv(stock_csv)
        ticker_map = dict(zip(df_stock["stock_key"], df_stock["ticker"]))
        
        df_raw["ticker"] = df_raw["stock_key"].map(ticker_map)
        df = df_raw[["date_key", "ticker", "close_price"]].copy()

    # Pivot table: rows = date_key, columns = ticker
    df_pivot = df.pivot(index="date_key", columns="ticker", values="close_price")
    
    # Drop rows with NaN (aligns on dates where all 4 banks have price data)
    df_aligned = df_pivot.dropna().sort_index()
    print(f"Số lượng phiên giao dịch đồng nhất sau khi căn chỉnh: {len(df_aligned)} (Từ ngày {df_aligned.index.min()} đến {df_aligned.index.max()})")
    return df_aligned


def dtw_distance(s1: np.ndarray, s2: np.ndarray) -> float:
    """Compute Dynamic Time Warping (DTW) distance between two 1D arrays using dynamic programming.
    """
    l1, l2 = len(s1), len(s2)
    dtw_matrix = np.full((l1 + 1, l2 + 1), np.inf)
    dtw_matrix[0, 0] = 0
    
    for i in range(1, l1 + 1):
        for j in range(1, l2 + 1):
            cost = abs(s1[i - 1] - s2[j - 1])
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j],      # deletion
                dtw_matrix[i, j - 1],      # insertion
                dtw_matrix[i - 1, j - 1]   # match
            )
            
    return dtw_matrix[l1, l2]


def main():
    print("Bắt đầu tính toán phân tích tương đồng chuỗi thời gian DTW...")
    df_prices = load_and_align_prices()
    tickers = ["BID", "TCB", "VCB", "CTG"]
    
    # Z-score normalization
    df_normalized = (df_prices[tickers] - df_prices[tickers].mean()) / df_prices[tickers].std()
    
    # 1. Tính toán ma trận khoảng cách DTW
    print("\n1. Đang tính toán ma trận khoảng cách DTW (Z-score normalized)...")
    t0 = time.time()
    dtw_matrix = pd.DataFrame(0.0, index=tickers, columns=tickers)
    for i in range(len(tickers)):
        for j in range(i, len(tickers)):
            t1, t2 = tickers[i], tickers[j]
            if t1 == t2:
                dist = 0.0
            else:
                dist = dtw_distance(df_normalized[t1].values, df_normalized[t2].values)
            dtw_matrix.loc[t1, t2] = dist
            dtw_matrix.loc[t2, t1] = dist
    print(f"Hoàn thành tính toán DTW sau {time.time() - t0:.2f} giây.")
    print("Ma trận khoảng cách DTW:")
    print(dtw_matrix)
    
    # 2. Tính toán ma trận hệ số tương quan lăn (Rolling Correlation)
    # Cấu hình cửa sổ lăn: 60 phiên giao dịch (~3 tháng) và 250 phiên giao dịch (~1 năm)
    window_short = 60
    window_long = 250
    
    print(f"\n2. Đang tính toán ma trận tương quan lăn (Rolling window = {window_short} và {window_long} phiên)...")
    
    # Tính tương quan lăn pairwise
    roll_corr_60_list = []
    roll_corr_250_list = []
    
    # Rolling correlation between pairs
    pairs = [("BID", "TCB"), ("BID", "VCB"), ("BID", "CTG"), 
             ("TCB", "VCB"), ("TCB", "CTG"), ("VCB", "CTG")]
    
    df_corr_60 = pd.DataFrame(index=df_prices.index)
    df_corr_250 = pd.DataFrame(index=df_prices.index)
    
    for t1, t2 in pairs:
        pair_name = f"{t1}_{t2}"
        # Compute rolling correlation
        df_corr_60[pair_name] = df_prices[t1].rolling(window_short).corr(df_prices[t2])
        df_corr_250[pair_name] = df_prices[t1].rolling(window_long).corr(df_prices[t2])
        
    # Tính tương quan trung bình toàn bộ thời gian
    avg_corr_matrix = df_prices[tickers].corr()
    print("Ma trận hệ số tương quan Pearson toàn bộ thời gian:")
    print(avg_corr_matrix)
    
    # 3. Xuất kết quả
    output_dir = "./data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    report_data = {
        "dtw_distance_matrix": dtw_matrix.to_dict(),
        "pearson_correlation_matrix": avg_corr_matrix.to_dict(),
        "average_rolling_correlation_60": df_corr_60.mean().to_dict(),
        "average_rolling_correlation_250": df_corr_250.mean().to_dict()
    }
    
    report_path = os.path.join(output_dir, "dtw_correlation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)
    print(f"\nĐã lưu báo cáo dạng JSON vào: {report_path}")
    
    # 4. Trực quan hóa kết quả
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Chart 1: Z-score normalized prices
    df_normalized.plot(ax=axes[0, 0], alpha=0.8)
    axes[0, 0].set_title("Biến động giá đóng cửa chuẩn hóa Z-score (2018 - 2026)")
    axes[0, 0].set_xlabel("Phiên giao dịch")
    axes[0, 0].set_ylabel("Giá trị Z-score")
    axes[0, 0].grid(True, alpha=0.3)
    
    # Chart 2: Heatmap DTW Distance
    sns.heatmap(dtw_matrix, annot=True, fmt=".2f", cmap="YlOrRd", ax=axes[0, 1], cbar_kws={'label': 'Khoảng cách DTW'})
    axes[0, 1].set_title("Ma trận khoảng cách DTW (Z-score Close Price)")
    
    # Chart 3: Heatmap Pearson Correlation
    sns.heatmap(avg_corr_matrix, annot=True, fmt=".3f", cmap="coolwarm", vmin=-1, vmax=1, ax=axes[1, 0])
    axes[1, 0].set_title("Ma trận hệ số tương quan Pearson toàn bộ thời gian")
    
    # Chart 4: Rolling Correlation (60 days)
    df_corr_60.plot(ax=axes[1, 1], alpha=0.7)
    axes[1, 1].set_title("Hệ số tương quan lăn 60 phiên giao dịch (~3 tháng)")
    axes[1, 1].set_xlabel("Phiên giao dịch")
    axes[1, 1].set_ylabel("Hệ số tương quan")
    axes[1, 1].axhline(0, color="black", linestyle="--", alpha=0.5)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend(loc="lower left", ncol=2)
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "dtw_correlation_plots.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Đã lưu biểu đồ phân tích vào: {plot_path}")


if __name__ == "__main__":
    main()
