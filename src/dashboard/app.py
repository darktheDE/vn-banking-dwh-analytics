"""Interactive Streamlit dashboard for the Vietnamese Financial Market Analytics DWH.

Visualizes stock forecasting (LSTM), bank clustering (K-Means), and risk classification (Random Forest).
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pickle
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src.utils.bigquery_client import get_bigquery_client, get_full_table_id

# ─────────────────────────────────────────────────────────────
# Cấu hình trang & Thiết lập
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Báo Cáo Phân Tích Dữ Liệu Ngân Hàng",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tự động hỗ trợ giao diện Sáng/Tối (Light/Dark Mode) qua prefers-color-scheme
st.markdown("""
    <style>
    /* Kiểu dáng chung cho Card */
    .stCard {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    /* Ghi đè kiểu dáng khi ở chế độ Dark Mode của hệ thống */
    @media (prefers-color-scheme: dark) {
        .stCard {
            background-color: #1e293b;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
    }
    </style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Các hàm tải dữ liệu (trực tiếp từ BigQuery DWH)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_stock_dimension():
    client = get_bigquery_client()
    table_id = get_full_table_id("dim_stock")
    query = f"SELECT stock_key, ticker, company_name FROM `{table_id}` ORDER BY stock_key"
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df


@st.cache_data(ttl=600)
def fetch_actual_price_history(stock_key: int, limit: int = 60):
    client = get_bigquery_client()
    price_table = get_full_table_id("fact_price_history")
    date_table = get_full_table_id("dim_date")
    query = f"""
        SELECT
            d.full_date,
            p.open_price,
            p.high_price,
            p.low_price,
            p.close_price,
            p.trading_volume
        FROM `{price_table}` p
        JOIN `{date_table}` d ON p.date_key = d.date_key
        WHERE p.stock_key = {stock_key}
        ORDER BY d.full_date DESC
        LIMIT {limit}
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    df["full_date"] = pd.to_datetime(df["full_date"])
    return df.sort_values("full_date").reset_index(drop=True)


@st.cache_data(ttl=600)
def fetch_lstm_predictions(stock_key: int):
    client = get_bigquery_client()
    pred_table = get_full_table_id("fact_model_predictions")
    # Training uses WRITE_TRUNCATE (all 4 stocks in one atomic write),
    # so each stock always has exactly 5 rows — one per T+1 to T+5 horizon.
    query = f"""
        SELECT
            horizon,
            predicted_close_price
        FROM `{pred_table}`
        WHERE stock_key = {stock_key}
          AND model_name = 'LSTM'
        ORDER BY horizon
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df


@st.cache_data(ttl=600)
def fetch_bank_clusters():
    client = get_bigquery_client()
    cluster_table = get_full_table_id("bank_cluster_assignments")
    perf_table = get_full_table_id("fact_bank_performance")
    
    # Query latest performance ratios and cluster assignments
    query = f"""
        WITH latest_perf AS (
            SELECT
                bank_key,
                npl_ratio, roa, roe, nim, cir, eta, etd, lta, ltd, gta,
                ROW_NUMBER() OVER (PARTITION BY bank_key ORDER BY date_key DESC) as rn
            FROM `{perf_table}`
        )
        SELECT
            c.bank_code,
            c.bank_name,
            c.bank_type,
            c.cluster_id,
            p.npl_ratio, p.roa, p.roe, p.nim, p.cir, p.eta, p.etd, p.lta, p.ltd, p.gta
        FROM `{cluster_table}` c
        LEFT JOIN latest_perf p ON c.bank_key = p.bank_key AND p.rn = 1
        ORDER BY c.cluster_id, c.bank_code
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df


@st.cache_data(ttl=600)
def fetch_credit_risk_predictions():
    client = get_bigquery_client()
    pred_table = get_full_table_id("bank_risk_predictions")
    query = f"""
        SELECT
            bank_code,
            date_key,
            risk_label,
            risk_probability,
            actual_npl_ratio
        FROM `{pred_table}`
        ORDER BY date_key DESC, risk_probability DESC
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df


# ─────────────────────────────────────────────────────────────
# Giao diện chính của Dashboard
# ─────────────────────────────────────────────────────────────
def main():
    load_dotenv()
    
    st.title("🏦 Phân Tích Dữ Liệu Lịch Sử & Dự Báo ML Ngành Ngân Hàng")
    st.markdown("---")
    
    # Menu bên trái (Sidebar)
    st.sidebar.title("Điều Hướng")
    app_mode = st.sidebar.radio(
        "Chọn phân hệ báo cáo",
        [
            "Dự Báo Giá Cổ Phiếu (LSTM)",
            "Phân Nhóm Ngân Hàng (K-Means)",
            "Phân Loại Rủi Ro Tín Dụng (Random Forest)",
            "Trạng Thái Hệ Thống DWH"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Nguồn dữ liệu: Google BigQuery Star Schema Data Warehouse")
    
    if app_mode == "Dự Báo Giá Cổ Phiếu (LSTM)":
        show_price_forecasting_section()
    elif app_mode == "Phân Nhóm Ngân Hàng (K-Means)":
        show_bank_clustering_section()
    elif app_mode == "Phân Loại Rủi Ro Tín Dụng (Random Forest)":
        show_credit_risk_section()
    else:
        show_dwh_status_section()


# ─────────────────────────────────────────────────────────────
# Phân hệ 1: Dự báo giá cổ phiếu (LSTM)
# ─────────────────────────────────────────────────────────────
def show_price_forecasting_section():
    st.header("📈 Dự Báo Giá Cổ Phiếu Trọng Điểm (LSTM)")
    st.write("Mô hình học sâu LSTM thực hiện dự báo giá đóng cửa của các cổ phiếu ngân hàng trong 5 ngày giao dịch tiếp theo (T+1 đến T+5).")
    
    # Load stocks
    stocks_df = fetch_stock_dimension()
    if stocks_df.empty:
        st.error("Không tìm thấy dữ liệu danh mục cổ phiếu.")
        return
        
    stock_options = {row["ticker"]: row["stock_key"] for _, row in stocks_df.iterrows()}
    selected_ticker = st.selectbox("Chọn mã cổ phiếu ngân hàng", list(stock_options.keys()))
    stock_key = stock_options[selected_ticker]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Load historical prices
        hist_df = fetch_actual_price_history(stock_key)
        
        # Load predictions
        pred_df = fetch_lstm_predictions(stock_key)
        
        if not hist_df.empty and not pred_df.empty:
            # Reconstruct prediction dates sequentially
            last_date = hist_df["full_date"].iloc[-1]
            future_dates = []
            current_date = last_date
            while len(future_dates) < len(pred_df):
                current_date += pd.Timedelta(days=1)
                # Skip weekends
                if current_date.weekday() < 5:
                    future_dates.append(current_date)
            
            pred_df["full_date"] = future_dates
            
            # Combine actuals and predictions for plotting
            actual_trace = go.Scatter(
                x=hist_df["full_date"],
                y=hist_df["close_price"] * 1000, # convert back to VND
                name="Giá lịch sử thực tế",
                line=dict(color="#3b82f6", width=2.5)
            )
            
            pred_trace = go.Scatter(
                x=pred_df["full_date"],
                y=pred_df["predicted_close_price"] * 1000,
                name="Giá dự báo từ LSTM",
                line=dict(color="#f43f5e", width=2.5, dash="dash"),
                marker=dict(size=8, symbol="circle")
            )
            
            fig = go.Figure(data=[actual_trace, pred_trace])
            fig.update_layout(
                title=f"Lịch Sử Giá & Dự Báo Giá 5 Ngày Cổ Phiếu {selected_ticker} (VND)",
                xaxis_title="Thời Gian",
                yaxis_title="Giá Cổ Phiếu (VND)",
                hovermode="x unified",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        else:
            st.warning("Không đủ dữ liệu trong Kho dữ liệu để biểu diễn đồ thị dự báo.")
            
    with col2:
        st.subheader("Kết Quả Dự Báo (T+1 đến T+5)")
        if not pred_df.empty:
            last_close = hist_df["close_price"].iloc[-1] * 1000
            st.metric(
                label="Giá đóng cửa gần nhất",
                value=f"{last_close:,.0f} VND",
                delta=None
            )
            
            # Table of forecasts
            forecast_table = []
            for idx, row in pred_df.iterrows():
                pred_val = row["predicted_close_price"] * 1000
                diff = pred_val - last_close
                diff_pct = (diff / last_close) * 100
                
                forecast_table.append({
                    "Thời Gian": row["horizon"],
                    "Ngày Dự Báo": row["full_date"].strftime("%Y-%m-%d"),
                    "Giá Dự Báo (VND)": f"{pred_val:,.0f}",
                    "Biến Động (%)": f"{diff_pct:+.2f}%"
                })
            
            st.table(pd.DataFrame(forecast_table))
        else:
            st.info("Không tìm thấy kết quả dự báo trong DWH.")


# ─────────────────────────────────────────────────────────────
# Phân hệ 2: Phân nhóm ngân hàng (K-Means)
# ─────────────────────────────────────────────────────────────
def show_bank_clustering_section():
    st.header("📊 Phân Nhóm & Phác Họa Đặc Trưng Ngân Hàng (K-Means)")
    st.write("Phân nhóm 46 ngân hàng thương mại Việt Nam dựa trên 10 tỷ số tài chính CAMELS đã được chuẩn hóa và giảm chiều bằng PCA.")
    
    # Load clusters data
    clusters_df = fetch_bank_clusters()
    if clusters_df.empty:
        st.error("Không tìm thấy dữ liệu phân nhóm ngân hàng.")
        return
        
    st.subheader("Không Gian Phân Tích Phân Nhóm 2D PCA")
    # Standardize and calculate first 2 PCA components on the fly for visualization
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    
    feature_cols = ["npl_ratio", "roa", "roe", "nim", "cir", "eta", "etd", "lta", "ltd", "gta"]
    df_clean = clusters_df.dropna(subset=feature_cols).copy()
    
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_clean[feature_cols])
    
    pca = PCA(n_components=2)
    pca_data = pca.fit_transform(scaled_features)
    
    df_clean["PC1"] = pca_data[:, 0]
    df_clean["PC2"] = pca_data[:, 1]
    
    # Scatter plot
    fig = px.scatter(
        df_clean,
        x="PC1",
        y="PC2",
        color="cluster_id",
        text="bank_code",
        hover_data=["bank_name", "bank_type"],
        title="Biểu Đồ Phân Tán Các Ngân Hàng Trên Hệ Tọa Độ PCA",
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig.update_traces(textposition="top center", marker=dict(size=12, line=dict(color="white", width=1)))
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    
    # Show radar comparison
    st.subheader("So Sánh Đặc Trưng Chỉ Số Tài Chính Giữa Các Nhóm")
    
    avg_profiles = df_clean.groupby("cluster_id")[feature_cols].mean().reset_index()
    
    # Transpose for easier comparison chart
    melted_profiles = pd.melt(avg_profiles, id_vars=["cluster_id"], value_vars=feature_cols, var_name="Chỉ Số Tài Chính", value_name="Giá Trị Trung Bình")
    
    # Map to Vietnamese labels
    ratio_vn_map = {
        "npl_ratio": "Tỷ lệ nợ xấu (NPL)",
        "roa": "Tỷ suất sinh lời/Tài sản (ROA)",
        "roe": "Tỷ suất sinh lời/Vốn CSH (ROE)",
        "nim": "Biên lãi thuần (NIM)",
        "cir": "Tỷ lệ chi phí/Thu nhập (CIR)",
        "eta": "Vốn CSH/Tổng tài sản (ETA)",
        "etd": "Vốn CSH/Tiền gửi (ETD)",
        "lta": "Dư nợ cho vay/Tổng tài sản (LTA)",
        "ltd": "Dư nợ cho vay/Tiền gửi (LTD)",
        "gta": "Cho vay gộp/Tổng tài sản (GTA)"
    }
    melted_profiles["Chỉ Số Tài Chính"] = melted_profiles["Chỉ Số Tài Chính"].map(ratio_vn_map)
    
    fig_bar = px.bar(
        melted_profiles,
        x="Chỉ Số Tài Chính",
        y="Giá Trị Trung Bình",
        color="cluster_id",
        barmode="group",
        title="Giá Trị Trung Bình Các Chỉ Số Camels Phân Theo Nhóm Ngân Hàng",
        labels={"cluster_id": "Mã Nhóm (Cluster ID)"}
    )
    st.plotly_chart(fig_bar, use_container_width=True, theme="streamlit")
    
    # Searchable list of banks in each cluster
    st.subheader("Danh Sách Thành Viên Phân Theo Nhóm")
    cluster_select = st.selectbox("Chọn Mã Nhóm Cần Xem", sorted(df_clean["cluster_id"].unique()))
    
    display_cols = ["bank_code", "bank_name", "bank_type"] + feature_cols
    cluster_banks = df_clean[df_clean["cluster_id"] == cluster_select][display_cols].copy()
    
    column_renames = {
        "bank_code": "Mã Ngân Hàng",
        "bank_name": "Tên Ngân Hàng",
        "bank_type": "Loại Hình",
        "npl_ratio": "NPL Ratio",
        "roa": "ROA",
        "roe": "ROE",
        "nim": "NIM",
        "cir": "CIR",
        "eta": "ETA",
        "etd": "ETD",
        "lta": "LTA",
        "ltd": "LTD",
        "gta": "GTA"
    }
    cluster_banks = cluster_banks.rename(columns=column_renames)
    st.dataframe(cluster_banks, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Phân hệ 3: Phân loại rủi ro tín dụng (Random Forest)
# ─────────────────────────────────────────────────────────────
def show_credit_risk_section():
    st.header("🛡️ Phân Loại & Giám Sát Rủi Ro Tín Dụng (Random Forest)")
    st.write("Nhận diện các ngân hàng có rủi ro tín dụng cao (tỷ lệ nợ xấu NPL thực tế hoặc dự báo vượt ngưỡng kiểm soát 3%).")
    
    # Load prediction results
    pred_df = fetch_credit_risk_predictions()
    if pred_df.empty:
        st.error("Không tìm thấy dữ liệu dự báo rủi ro tín dụng.")
        return
        
    # Get the latest predictions
    latest_date_key = pred_df["date_key"].max()
    latest_preds = pred_df[pred_df["date_key"] == latest_date_key].copy()
    
    # Create layout 1:1
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Tỷ Lệ Phân Phối Trạng Thái Rủi Ro")
        risk_counts = latest_preds["risk_label"].value_counts().reset_index()
        risk_counts["Trạng Thái"] = risk_counts["risk_label"].map({0: "An Toàn (NPL < 3%)", 1: "Rủi Ro Cao (NPL ≥ 3%)"})
        
        fig = px.pie(
            risk_counts,
            values="count",
            names="Trạng Thái",
            color="Trạng Thái",
            color_discrete_map={"An Toàn (NPL < 3%)": "#10b981", "Rủi Ro Cao (NPL ≥ 3%)": "#ef4444"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        
    with col2:
        st.subheader("Độ Quan Trọng Của Các Chỉ Số (Feature Importance)")
        feat_imp_data = pd.DataFrame({
            "Chỉ Số Tài Chính": [
                "Tỷ lệ trích lập dự phòng (llp_ratio)", 
                "Tỷ suất sinh lời/Vốn CSH (roe)", 
                "Tỷ lệ chi phí/Thu nhập (cir)", 
                "Tỷ suất sinh lời/Tài sản (roa)", 
                "Dư nợ cho vay (total_loans)", 
                "Vốn CSH/Tổng tài sản (eta)", 
                "Tổng tài sản (total_assets)", 
                "Tổng Vốn CSH (total_equity)"
            ],
            "Độ Quan Trọng": [0.2045, 0.1156, 0.1054, 0.0943, 0.0528, 0.0496, 0.0496, 0.0492]
        }).sort_values("Độ Quan Trọng", ascending=True)
        
        fig_imp = px.bar(
            feat_imp_data,
            x="Độ Quan Trọng",
            y="Chỉ Số Tài Chính",
            orientation="h",
            color="Độ Quan Trọng",
            color_continuous_scale=px.colors.sequential.Bluered_r
        )
        fig_imp.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig_imp, use_container_width=True, theme="streamlit")
        
    st.markdown("---")
    st.subheader(f"Bảng Giám Sát Rủi Ro Các Ngân Hàng Thương Mại (Năm: {str(latest_date_key)[:4]})")
    
    latest_preds["Phân Loại Rủi Ro"] = latest_preds["risk_label"].map({0: "An Toàn", 1: "🚨 Nguy Cơ Cao"})
    latest_preds["Xác Suất Rủi Ro"] = (latest_preds["risk_probability"] * 100).map("{:.2f}%".format)
    latest_preds["Tỷ Lệ Nợ Xấu (NPL)"] = (latest_preds["actual_npl_ratio"] * 100).map("{:.2f}%".format)
    
    display_df = latest_preds[["bank_code", "Phân Loại Rủi Ro", "Xác Suất Rủi Ro", "Tỷ Lệ Nợ Xấu (NPL)"]].sort_values("Phân Loại Rủi Ro", ascending=False)
    
    display_df = display_df.rename(columns={
        "bank_code": "Mã Ngân Hàng",
        "Phân Loại Rủi Ro": "Trạng Thái Hệ Thống",
        "Xác Suất Rủi Ro": "Xác Suất Dự Báo Nợ Xấu",
        "Tỷ Lệ Nợ Xấu (NPL)": "Tỷ Lệ Nợ Xấu Thực Tế"
    })
    st.dataframe(display_df, use_container_width=True, height=500)


# ─────────────────────────────────────────────────────────────
# Phân hệ 4: Trạng thái hệ thống DWH
# ─────────────────────────────────────────────────────────────
def show_dwh_status_section():
    st.header("⚙️ Trạng Thái Tích Hợp Kho Dữ Liệu BigQuery DWH")
    st.write("Hệ thống kiểm tra số lượng bản ghi và dung lượng lưu trữ thực tế của các bảng thuộc mô hình Star Schema trên Cloud.")
    
    client = get_bigquery_client()
    dataset_id = os.getenv("BQ_DATASET_ID", "financial_dwh")
    
    st.subheader("Tổng Quan Số Liệu Các Bảng DWH")
    
    query = f"""
        SELECT
            table_id as `Tên Bảng (Table ID)`,
            row_count as `Số Bản Ghi (Row Count)`,
            ROUND(size_bytes / 1024, 2) as `Dung Lượng (KB)`
        FROM `{os.getenv("GCP_PROJECT_ID")}.{dataset_id}.__TABLES__`
        ORDER BY row_count DESC
    """
    
    try:
        meta_df = client.query(query).to_dataframe(create_bqstorage_client=False)
        st.table(meta_df)
        
        st.success("Tất cả 10 bảng DWH đang hoạt động ổn định và kết nối thành công!")
    except Exception as e:
        st.error(f"Lỗi khi lấy thông tin siêu dữ liệu DWH: {str(e)}")


if __name__ == "__main__":
    main()
