"""generate_dashboard_plots.py

Script to generate local dashboard plots and statistics matching the Looker Studio dashboard specification.
Processes local CSV files and ML outputs to create visualization figures and a markdown summary.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Ensure the root of the project is in the search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
ML_DATA_DIR = os.path.join(BASE_DIR, "data", "data_ml")
INPUT_DIR = os.path.join(ML_DATA_DIR, "input")
OUTPUT_DIR = os.path.join(ML_DATA_DIR, "output")
DASHBOARD_DIR = os.path.join(BASE_DIR, "reports", "figures", "dashboard")

# Set theme
sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = "Arial"
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False

# Colors
PRIMARY_BLUE = "#1f77b4"
DASHED_ORANGE = "#ff7f0e"
GREEN_BUY = "#2ca02c"
RED_SELL = "#d62728"
TEAL = "#008080"
PINK = "#ff69b4"


def ensure_dirs():
    """Ensure the target dashboard directory exists."""
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    logger.info("Created dashboard figures directory: %s", DASHBOARD_DIR)


def parse_date_key(date_key):
    """Convert date_key (int YYYYMMDD or str) to YYYY-MM-DD string."""
    s = str(int(date_key))
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"


def generate_page1_market_movement():
    """Page 1 — Market Movement (BID Stock Forecasting).

    Generates line chart of actual vs predicted BID stock prices and bar charts of foreign and prop trading.
    """
    logger.info("Generating Page 1: Market Movement...")

    # 1. Load LSTM input (actual history) and predictions
    lstm_data_path = os.path.join(INPUT_DIR, "bid_lstm_data.csv")
    predictions_path = os.path.join(OUTPUT_DIR, "lstm_predictions_local.csv")

    if not os.path.exists(lstm_data_path) or not os.path.exists(predictions_path):
        logger.warning("LSTM data or predictions not found. Skipping Page 1.")
        return None

    df_lstm = pd.read_csv(lstm_data_path)
    df_pred = pd.read_csv(predictions_path)

    # 2. Process dates and actual data
    df_lstm["date"] = pd.to_datetime(df_lstm["date"])
    df_lstm = df_lstm.sort_values("date").reset_index(drop=True)

    # Last 60 days of actual data for visual clarity
    df_actual_recent = df_lstm.tail(60).copy()

    # Generate dates for predictions (next 5 trading days after the last actual date)
    last_actual_date = df_actual_recent["date"].iloc[-1]
    
    # Simple mapping of T+1 to T+5 to the next business days
    pred_dates = []
    curr_date = last_actual_date
    for _ in range(len(df_pred)):
        curr_date += pd.tseries.offsets.BDay(1)
        pred_dates.append(curr_date)
    df_pred["date"] = pred_dates

    # 3. Load foreign and proprietary trading data (to align with the last 60 actual days)
    foreign_path = os.path.join(PROCESSED_DIR, "fact_foreign_trading_clean.csv")
    prop_path = os.path.join(PROCESSED_DIR, "fact_proprietary_trading_clean.csv")

    foreign_available = os.path.exists(foreign_path)
    prop_available = os.path.exists(prop_path)

    # Plot
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=False, gridspec_kw={"height_ratios": [3, 1.2, 1.2]})

    # Axis 1: Stock Price (Actual vs Predicted)
    ax_price = axes[0]
    ax_price.plot(df_actual_recent["date"], df_actual_recent["close_price"], label="Actual Close Price", color=PRIMARY_BLUE, linewidth=2.5)
    
    # Add connecting line from last actual to T+1 prediction
    connect_dates = [df_actual_recent["date"].iloc[-1], df_pred["date"].iloc[0]]
    connect_prices = [df_actual_recent["close_price"].iloc[-1], df_pred["predicted_close_price"].iloc[0]]
    ax_price.plot(connect_dates, connect_prices, color=DASHED_ORANGE, linestyle="--", alpha=0.7)
    
    ax_price.plot(df_pred["date"], df_pred["predicted_close_price"], label="LSTM Predicted (T+1 to T+5)", color=DASHED_ORANGE, linestyle="--", marker="o", linewidth=2)
    ax_price.set_title("BIDV Stock Price Actual vs. LSTM Forecast (T+1 to T+5)", fontsize=14, fontweight="bold")
    ax_price.set_ylabel("Price (Thousand VND)", fontsize=12)
    ax_price.legend(loc="upper left")
    ax_price.grid(True, linestyle=":", alpha=0.6)

    # Plot aligned date range for foreign and prop trading
    if foreign_available:
        df_for = pd.read_csv(foreign_path)
        df_for["date"] = pd.to_datetime(df_for["date_key"].apply(parse_date_key))
        df_for = df_for.sort_values("date").reset_index(drop=True)
        # Filter for dates visible in the price chart
        df_for_filtered = df_for[df_for["date"] >= df_actual_recent["date"].iloc[0]].copy()
        
        ax_for = axes[1]
        colors_for = [GREEN_BUY if val >= 0 else RED_SELL for val in df_for_filtered["foreign_net_volume"]]
        ax_for.bar(df_for_filtered["date"], df_for_filtered["foreign_net_volume"] / 1000, color=colors_for, width=0.6, alpha=0.85)
        ax_for.set_title("Foreign Investors Net Trading Volume (fact_foreign_trading)", fontsize=11, fontweight="semibold")
        ax_for.set_ylabel("Net Vol (k shares)", fontsize=10)
        ax_for.grid(True, linestyle=":", alpha=0.6)
    else:
        axes[1].text(0.5, 0.5, "Foreign Trading Data Unavailable", ha="center", va="center")
        axes[1].set_title("Foreign Investors Net Trading Volume")

    if prop_available:
        df_prop = pd.read_csv(prop_path)
        df_prop["date"] = pd.to_datetime(df_prop["date_key"].apply(parse_date_key))
        df_prop = df_prop.sort_values("date").reset_index(drop=True)
        # Filter for dates visible in the price chart
        df_prop_filtered = df_prop[df_prop["date"] >= df_actual_recent["date"].iloc[0]].copy()
        
        ax_prop = axes[2]
        colors_prop = [TEAL if val >= 0 else PINK for val in df_prop_filtered["prop_net_volume"]]
        ax_prop.bar(df_prop_filtered["date"], df_prop_filtered["prop_net_volume"] / 1000, color=colors_prop, width=0.6, alpha=0.85)
        ax_prop.set_title("Proprietary Trading Net Volume (fact_proprietary_trading)", fontsize=11, fontweight="semibold")
        ax_prop.set_ylabel("Net Vol (k shares)", fontsize=10)
        ax_prop.grid(True, linestyle=":", alpha=0.6)
    else:
        axes[2].text(0.5, 0.5, "Proprietary Trading Data Unavailable", ha="center", va="center")
        axes[2].set_title("Proprietary Trading Net Volume")

    # Formatting x-axis to align dates
    fig.autofmt_xdate()
    fig.tight_layout()
    
    out_path = os.path.join(DASHBOARD_DIR, "page1_market_movement.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved Page 1 plot to %s", out_path)
    return {
        "latest_actual": df_actual_recent["close_price"].iloc[-1],
        "pred_t1": df_pred["predicted_close_price"].iloc[0],
        "pred_t5": df_pred["predicted_close_price"].iloc[-1],
    }

#test commit 2
def generate_page2_bank_profiling():
    """Page 2 — Bank Profiling (K-Means Clustering).

    Generates PCA cluster scatter plot, radar chart of cluster profiles, and type distribution pie chart.
    """
    logger.info("Generating Page 2: Bank Profiling...")

    # Load data
    camels_path = os.path.join(INPUT_DIR, "banks_camels_46.csv")
    cluster_path = os.path.join(OUTPUT_DIR, "kmeans_clusters_local.csv")

    if not os.path.exists(camels_path) or not os.path.exists(cluster_path):
        logger.warning("Clustering data or outputs not found. Skipping Page 2.")
        return None

    df_camels = pd.read_csv(camels_path)
    df_cluster = pd.read_csv(cluster_path)

    # Get latest snapshot per bank
    df_latest = df_camels.sort_values("date_key").groupby("bank_key").last().reset_index()
    
    # Merge with cluster IDs
    df_merged = pd.merge(df_latest, df_cluster[["bank_key", "cluster_id"]], on="bank_key", how="inner")
    
    # Standardize and compute PCA coordinates for plotting
    features = ["npl_ratio", "llp_ratio", "roa", "roe", "nim", "cir", "eta", "etd", "lta", "ltd", "gta"]
    available_features = [f for f in features if f in df_merged.columns]
    
    X = df_merged[available_features].fillna(0).values
    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    df_merged["PC1"] = X_pca[:, 0]
    df_merged["PC2"] = X_pca[:, 1]

    # Create figure layout
    fig = plt.figure(figsize=(16, 12))
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1])

    # 1. Scatter Plot (PC1 vs PC2)
    ax_scatter = fig.add_subplot(grid[0, 0])
    sns.scatterplot(
        data=df_merged, x="PC1", y="PC2", hue="cluster_id", 
        style="bank_type", palette="Set1", s=100, ax=ax_scatter, alpha=0.85
    )
    # Annotate some notable banks
    for i, row in df_merged.iterrows():
        if row["bank_code"] in ["BIDV", "VCB", "CTG", "TCB", "DAB"]:
            ax_scatter.text(row["PC1"] + 0.1, row["PC2"] + 0.1, row["bank_code"], fontsize=9, fontweight="semibold")
            
    ax_scatter.set_title("BP-01: K-Means Clustering on PC1 & PC2", fontsize=12, fontweight="bold")
    ax_scatter.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)")
    ax_scatter.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)")
    ax_scatter.grid(True, linestyle=":", alpha=0.5)

    # 2. Pie Chart (Bank Type distribution per cluster)
    ax_pie = fig.add_subplot(grid[0, 1])
    type_counts = df_merged.groupby(["cluster_id", "bank_type"]).size().unstack(fill_value=0)
    
    type_counts.plot(kind="bar", stacked=True, color=["#1f77b4", "#ff7f0e", "#2ca02c"], ax=ax_pie, width=0.5)
    ax_pie.set_title("BP-04: Bank Type Distribution by Cluster", fontsize=12, fontweight="bold")
    ax_pie.set_xlabel("Cluster ID")
    ax_pie.set_ylabel("Count of Banks")
    ax_pie.set_xticklabels(ax_pie.get_xticklabels(), rotation=0)
    ax_pie.legend(title="Bank Type")
    ax_pie.grid(True, axis="y", linestyle=":", alpha=0.5)

    # 3. Radar Chart (Cluster average CAMELS profile)
    ax_radar = fig.add_subplot(grid[1, :], polar=True)
    
    radar_features = ["roa", "roe", "nim", "cir", "eta", "npl_ratio"]
    # Normalize features to 0-1 for display comparison
    df_norm = df_merged.copy()
    for f in radar_features:
        min_val = df_norm[f].min()
        max_val = df_norm[f].max()
        if max_val - min_val > 0:
            df_norm[f] = (df_norm[f] - min_val) / (max_val - min_val)
        else:
            df_norm[f] = 0.5
            
    cluster_means = df_norm.groupby("cluster_id")[radar_features].mean()
    
    angles = np.linspace(0, 2 * np.pi, len(radar_features), endpoint=False).tolist()
    angles += angles[:1] # close the loop
    
    colors = ["#d62728", "#1f77b4", "#2ca02c"]
    
    for cluster_id in cluster_means.index:
        values = cluster_means.loc[cluster_id].tolist()
        values += values[:1]
        
        ax_radar.plot(angles, values, color=colors[cluster_id % len(colors)], linewidth=2, label=f"Cluster {cluster_id}")
        ax_radar.fill(angles, values, color=colors[cluster_id % len(colors)], alpha=0.25)
        
    ax_radar.set_theta_offset(np.pi / 2)
    ax_radar.set_theta_direction(-1)
    ax_radar.set_thetagrids(np.degrees(angles[:-1]), [f.upper() for f in radar_features])
    ax_radar.set_title("BP-02: Radar Chart of Cluster CAMELS Profiles (Normalized Scale)", fontsize=12, fontweight="bold", pad=20)
    ax_radar.legend(loc="upper right", bbox_to_anchor=(1.1, 1.1))

    fig.tight_layout()
    out_path = os.path.join(DASHBOARD_DIR, "page2_bank_profiling.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved Page 2 plot to %s", out_path)
    
    return {
        "clusters_summary": df_merged.groupby("cluster_id").size().to_dict(),
        "dab_cluster": int(df_merged[df_merged["bank_code"] == "DAB"]["cluster_id"].iloc[0]) if "DAB" in df_merged["bank_code"].values else None
    }


def generate_page3_risk_monitoring():
    """Page 3 — Risk Monitoring (Random Forest Classification).

    Generates NPL trend for flagged high-risk banks and feature importances.
    """
    logger.info("Generating Page 3: Risk Monitoring...")

    # Load data
    rf_pred_path = os.path.join(OUTPUT_DIR, "rf_predictions_local.csv")
    rf_feat_path = os.path.join(OUTPUT_DIR, "rf_feature_importance_local.csv")

    if not os.path.exists(rf_pred_path) or not os.path.exists(rf_feat_path):
        logger.warning("RF predictions or feature importances not found. Skipping Page 3.")
        return None

    df_pred = pd.read_csv(rf_pred_path)
    df_feat = pd.read_csv(rf_feat_path)

    # 1. High Risk flagged banks
    # Find banks flagged as "High Risk" (predicted_risk_label = 1) in ANY year to ensure visible trend lines
    high_risk_banks = df_pred[df_pred["predicted_risk_label"] == 1]["bank_code"].unique()
    logger.info("Flagged High Risk Banks in predictions: %s", high_risk_banks)

    # Create figure
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [1.2, 1]})

    # Plot 1: NPL Trend for High-Risk Flagged Banks
    ax_trend = axes[0]
    if len(high_risk_banks) > 0:
        # Plot NPL trends for those specific banks
        df_trends = df_pred[df_pred["bank_code"].isin(high_risk_banks)].sort_values(["bank_code", "year"])
        for bank in high_risk_banks:
            df_bank_trend = df_trends[df_trends["bank_code"] == bank]
            ax_trend.plot(df_bank_trend["year"], df_bank_trend["npl_ratio"] * 100, marker="o", linewidth=2, label=f"{bank} NPL")
        ax_trend.axhline(y=3.0, color="red", linestyle="--", label="3% NPL Threshold")
        ax_trend.set_title("RM-02: Historical NPL Ratio Trend for Flagged High-Risk Banks", fontsize=12, fontweight="bold")
        ax_trend.set_ylabel("NPL Ratio (%)", fontsize=11)
        ax_trend.set_xlabel("Year", fontsize=11)
        ax_trend.set_xticks(sorted(df_pred["year"].unique()))
        ax_trend.legend()
        ax_trend.grid(True, linestyle=":", alpha=0.5)
    else:
        ax_trend.text(0.5, 0.5, "No High Risk Banks Flagged in Latest Year", ha="center", va="center")
        ax_trend.set_title("Historical NPL Ratio Trend")

    # Plot 2: Feature Importance
    ax_feat = axes[1]
    df_feat_sorted = df_feat.sort_values("importance", ascending=True).head(10) # Plot top 10 descending
    ax_feat.barh(df_feat_sorted["feature"], df_feat_sorted["importance"], color="#4c72b0", edgecolor="grey")
    ax_feat.set_title("RM-03: Random Forest Feature Importance (Top 10 CAMELS features)", fontsize=12, fontweight="bold")
    ax_feat.set_xlabel("Importance Score", fontsize=11)
    ax_feat.grid(True, axis="x", linestyle=":", alpha=0.5)

    fig.tight_layout()
    out_path = os.path.join(DASHBOARD_DIR, "page3_risk_monitoring.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Saved Page 3 plot to %s", out_path)

    return {
        "high_risk_banks": high_risk_banks.tolist(),
        "top_feature": df_feat.sort_values("importance", ascending=False)["feature"].iloc[0]
    }


def write_summary_report(p1_stats, p2_stats, p3_stats):
    """Write markdown summary report file."""
    report_path = os.path.join(DASHBOARD_DIR, "summary_report.md")
    
    content = f"""# Báo Cáo Phân Tích Dữ Liệu và Dự Báo (Môi Trường Cục Bộ)

> Ngày tạo: 2026-06-30
> Phục vụ: Kiểm thử kết quả Dashboard trước khi triển khai BigQuery

---

## 1. Kết Quả Dự Báo Cổ Phiếu BIDV (Trang 1 — Market Movement)
- **Giá đóng cửa thực tế phiên cuối (2026-06-26)**: {p1_stats['latest_actual']:.2f} nghìn VND
- **Dự báo LSTM phiên kế tiếp (T+1)**: {p1_stats['pred_t1']:.2f} nghìn VND
- **Dự báo LSTM phiên thứ 5 (T+5)**: {p1_stats['pred_t5']:.2f} nghìn VND
- **Biểu đồ biến động giá thực tế BID & LSTM dự báo**:
![Biểu đồ biến động giá thực tế BID & LSTM dự báo](page1_market_movement.png)

---

## 2. Phân Nhóm Hệ Thống Ngân Hàng (Trang 2 — Bank Profiling)
- **Số lượng ngân hàng phân cụm**:
"""
    for cid, count in p2_stats["clusters_summary"].items():
        content += f"  - **Cluster {cid}**: {count} ngân hàng\n"
        
    if p2_stats["dab_cluster"] is not None:
        content += f"- **Nhận xét**: Ngân hàng **DAB** (Đông Á Bank) được phân vào **Cluster {p2_stats['dab_cluster']}** do các chỉ số tài chính cá biệt (ngoại lai), tách biệt hoàn toàn so với nhóm các ngân hàng còn lại tại Cluster {1 - p2_stats['dab_cluster']}.\n"
    
    content += f"""- **Biểu đồ phân cụm ngân hàng & radar profile**:
![Biểu đồ phân cụm ngân hàng & radar profile](page2_bank_profiling.png)

---

## 3. Cảnh Báo Sớm Rủi Ro Nợ Xấu (Trang 3 — Risk Monitoring)
- **Danh sách ngân hàng bị cảnh báo rủi ro cao (NPL >= 3% dự kiến)**:
"""
    if len(p3_stats["high_risk_banks"]) > 0:
        for bank in p3_stats["high_risk_banks"]:
            content += f"  - **{bank}**\n"
    else:
        content += "  - Không có ngân hàng nào bị gắn nhãn rủi ro cao trong năm gần nhất.\n"
        
    content += f"""- **Đặc trưng CAMELS ảnh hưởng mạnh nhất đến rủi ro tín dụng**: `{p3_stats['top_feature']}` (Độ quan trọng cao nhất).
- **Biểu đồ rủi ro nợ xấu & feature importance**:
![Biểu đồ rủi ro nợ xấu & feature importance](page3_risk_monitoring.png)

---

*Lưu ý: Báo cáo này được tự động sinh bằng code từ dữ liệu local-first trong `data/processed/` và `data/data_ml/output/`.*
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    logger.info("Saved markdown summary report to %s", report_path)


def main():
    ensure_dirs()
    p1 = generate_page1_market_movement()
    p2 = generate_page2_bank_profiling()
    p3 = generate_page3_risk_monitoring()
    
    if p1 and p2 and p3:
        write_summary_report(p1, p2, p3)
        logger.info("=== DASHBOARD GENERATION COMPLETED SUCCESSFULLY ===")
    else:
        logger.error("Some dashboard generation steps failed. Please check logs.")


if __name__ == "__main__":
    main()
