"""Task 2.1: Causal Analysis of LLP on NPL.

Implements ADF Stationarity Test, Granger Causality Test, and Lagged Panel
Regression (Fixed Effects) to evaluate the impact of Loan Loss Provisions
(llp_ratio) on Non-Performing Loans (npl_ratio).
"""

from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.bigquery_client import get_bigquery_client, get_full_table_id

# Set encoding for Windows console print
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def load_data() -> pd.DataFrame:
    """Load bank performance data from BigQuery, falling back to local clean CSV if needed.
    """
    load_dotenv()
    try:
        client = get_bigquery_client()
        table_id = get_full_table_id("fact_bank_performance")
        query = f"SELECT date_key, bank_key, npl_ratio, llp_ratio FROM `{table_id}`"
        df = client.query(query).to_dataframe(create_bqstorage_client=False)
        print("Đã tải dữ liệu thành công từ BigQuery.")
    except Exception as e:
        print(f"Không thể kết nối BigQuery ({e}). Đang tải dữ liệu từ file CSV cục bộ...")
        csv_path = "./data/processed/fact_bank_performance_clean.csv"
        df = pd.read_csv(csv_path)[["date_key", "bank_key", "npl_ratio", "llp_ratio"]]

    df["year"] = df["date_key"] // 10000
    df = df.sort_values(["bank_key", "year"]).reset_index(drop=True)
    return df


def analyze_stationarity(ts_df: pd.DataFrame, col: str) -> dict:
    """Perform Augmented Dickey-Fuller (ADF) test for stationarity.
    """
    series = ts_df[col].dropna()
    result = adfuller(series, autolag="AIC")
    return {
        "adf_stat": result[0],
        "p_value": result[1],
        "critical_values": result[4],
        "is_stationary": result[1] < 0.05
    }


def run_granger_causality(ts_df: pd.DataFrame, max_lag: int = 3) -> dict:
    """Run Granger Causality Tests.
    Tests if llp_ratio Granger-causes npl_ratio.
    Data must be a DataFrame containing columns [npl_ratio, llp_ratio].
    """
    data = ts_df[["npl_ratio", "llp_ratio"]].dropna()
    res = grangercausalitytests(data, maxlag=max_lag, verbose=False)
    
    summary = {}
    for lag, tests in res.items():
        # Get SSR F-test p-value (standard F-test)
        ssr_f_p = tests[0]["ssr_ftest"][1]
        # Get Chi2-test p-value
        ssr_chi2_p = tests[0]["ssr_chi2test"][1]
        summary[lag] = {
            "f_p_value": ssr_f_p,
            "chi2_p_value": ssr_chi2_p,
            "is_significant": ssr_f_p < 0.05
        }
    return summary


def run_lagged_panel_regression(df: pd.DataFrame) -> sm.regression.linear_model.RegressionResults:
    """Run Lagged Panel Regression with entity Fixed Effects (LSDV model).
    NPL(t) = alpha_i + beta_1 * NPL(t-1) + beta_2 * LLP(t-1) + beta_3 * LLP(t-2) + epsilon
    """
    # Create lags per bank
    panel_list = []
    for bank, group in df.groupby("bank_key"):
        group = group.sort_values("year").copy()
        group["npl_ratio_lag1"] = group["npl_ratio"].shift(1)
        group["llp_ratio_lag1"] = group["llp_ratio"].shift(1)
        group["llp_ratio_lag2"] = group["llp_ratio"].shift(2)
        panel_list.append(group)
    
    panel_df = pd.concat(panel_list).dropna().reset_index(drop=True)
    
    # Dependent and Independent variables
    y = panel_df["npl_ratio"]
    X = panel_df[["npl_ratio_lag1", "llp_ratio_lag1", "llp_ratio_lag2"]].copy()
    X = sm.add_constant(X)
    
    # Entity Fixed Effects via Least Squares Dummy Variable (LSDV)
    # Exclude first bank dummy to prevent multicollinearity (dummy variable trap)
    bank_dummies = pd.get_dummies(panel_df["bank_key"], prefix="bank", drop_first=True)
    # Convert dummy columns to float
    bank_dummies = bank_dummies.astype(float)
    X = pd.concat([X, bank_dummies], axis=1)
    
    model = sm.OLS(y, X)
    results = model.fit()
    return results, panel_df


def main():
    print("Bắt đầu phân tích nhân quả giữa LLP và NPL...")
    df = load_data()
    
    # 1. Tạo chuỗi thời gian tổng hợp (Aggregated Annual Time Series) để chạy Granger Causality
    ts_annual = df.groupby("year")[["npl_ratio", "llp_ratio"]].mean().reset_index()
    ts_annual = ts_annual.sort_values("year").reset_index(drop=True)
    
    # 2. Kiểm định tính dừng (ADF Test)
    print("\n=== KIỂM ĐỊNH TÍNH DỪNG (ADF TEST) ===")
    adf_npl = analyze_stationarity(ts_annual, "npl_ratio")
    adf_llp = analyze_stationarity(ts_annual, "llp_ratio")
    
    print(f"NPL Ratio ADF Stat: {adf_npl['adf_stat']:.4f}, p-value: {adf_npl['p_value']:.4f} (Dừng: {adf_npl['is_stationary']})")
    print(f"LLP Ratio ADF Stat: {adf_llp['adf_stat']:.4f}, p-value: {adf_llp['p_value']:.4f} (Dừng: {adf_llp['is_stationary']})")
    
    # Nếu không dừng, lấy sai phân bậc 1 (First Difference)
    ts_diff = ts_annual.copy()
    ts_diff["npl_ratio"] = ts_diff["npl_ratio"].diff()
    ts_diff["llp_ratio"] = ts_diff["llp_ratio"].diff()
    ts_diff = ts_diff.dropna().reset_index(drop=True)
    
    print("\n=== KIỂM ĐỊNH TÍNH DỪNG SAU SAI PHÂN BẬC 1 ===")
    adf_npl_diff = analyze_stationarity(ts_diff, "npl_ratio")
    adf_llp_diff = analyze_stationarity(ts_diff, "llp_ratio")
    print(f"Sai phân NPL ADF Stat: {adf_npl_diff['adf_stat']:.4f}, p-value: {adf_npl_diff['p_value']:.4f} (Dừng: {adf_npl_diff['is_stationary']})")
    print(f"Sai phân LLP ADF Stat: {adf_llp_diff['adf_stat']:.4f}, p-value: {adf_llp_diff['p_value']:.4f} (Dừng: {adf_llp_diff['is_stationary']})")
    
    # Chọn chuỗi thời gian phù hợp để chạy Granger Causality
    causal_data = ts_diff if not (adf_npl["is_stationary"] and adf_llp["is_stationary"]) else ts_annual
    print(f"\nSử dụng dữ liệu {'Sai phân bậc 1' if causal_data is ts_diff else 'Nguyên bản'} để kiểm định Granger.")
    
    # 3. Kiểm định nhân quả Granger
    print("\n=== KIỂM ĐỊNH NHÂN QUẢ GRANGER ===")
    granger_res = run_granger_causality(causal_data, max_lag=3)
    for lag, metrics in granger_res.items():
        print(f"Độ trễ (Lag) {lag}: F-test p-value = {metrics['f_p_value']:.4f} (Có ý nghĩa: {metrics['is_significant']})")
        
    # 4. Hồi quy bảng trễ (Lagged Panel Regression)
    print("\n=== HỒI QUY BẢNG TRỄ (LSDV FIXED EFFECTS) ===")
    reg_results, panel_df = run_lagged_panel_regression(df)
    
    # In kết quả các biến chính
    main_vars = ["const", "npl_ratio_lag1", "llp_ratio_lag1", "llp_ratio_lag2"]
    summary_table = reg_results.summary2().tables[1].loc[main_vars]
    print(summary_table)
    print(f"R-squared: {reg_results.rsquared:.4f}, Adjusted R-squared: {reg_results.rsquared_adj:.4f}")
    
    # 5. Xuất báo cáo text
    output_dir = "./data/processed"
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "causal_analysis_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("BÁO CÁO PHÂN TÍCH NHÂN QUẢ Granger VÀ HỒI QUY BẢNG TRỄ\n")
        f.write("=====================================================\n\n")
        f.write("1. Kiểm định tính dừng ADF (Aggregated Time Series):\n")
        f.write(f"  - NPL Ratio (Mức): ADF={adf_npl['adf_stat']:.4f}, p={adf_npl['p_value']:.4f}\n")
        f.write(f"  - LLP Ratio (Mức): ADF={adf_llp['adf_stat']:.4f}, p={adf_llp['p_value']:.4f}\n")
        f.write(f"  - NPL Ratio (Sai phân bậc 1): ADF={adf_npl_diff['adf_stat']:.4f}, p={adf_npl_diff['p_value']:.4f}\n")
        f.write(f"  - LLP Ratio (Sai phân bậc 1): ADF={adf_llp_diff['adf_stat']:.4f}, p={adf_llp_diff['p_value']:.4f}\n\n")
        
        f.write("2. Kiểm định nhân quả Granger (llp_ratio -> npl_ratio):\n")
        for lag, metrics in granger_res.items():
            f.write(f"  - Độ trễ {lag} năm: F-p_value={metrics['f_p_value']:.4f}, chi2-p_value={metrics['chi2_p_value']:.4f} (Ý nghĩa: {metrics['is_significant']})\n")
        f.write("\n")
        
        f.write("3. Hồi quy bảng trễ (Entity Fixed Effects LSDV):\n")
        f.write(reg_results.summary().as_text())
        
    print(f"\nĐã lưu báo cáo thống kê chi tiết vào: {report_path}")
    
    # 6. Vẽ biểu đồ xu hướng
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=ts_annual, x="year", y="npl_ratio", label="Tỷ lệ nợ xấu trung bình (NPL Ratio)", marker="o", color="crimson")
    ax2 = plt.twinx()
    sns.lineplot(data=ts_annual, x="year", y="llp_ratio", label="Tỷ lệ dự phòng rủi ro trung bình (LLP Ratio)", marker="s", color="royalblue", ax=ax2)
    
    plt.title("Xu hướng Tỷ lệ Nợ xấu (NPL) và Tỷ lệ Dự phòng Rủi ro (LLP) (2002 - 2022)")
    plt.grid(True, linestyle="--", alpha=0.5)
    
    # Gộp legend từ 2 trục
    lines, labels = plt.gca().get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc="upper left")
    
    plot_path = os.path.join(output_dir, "llp_npl_causality.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Đã lưu biểu đồ xu hướng vào: {plot_path}")


if __name__ == "__main__":
    main()
