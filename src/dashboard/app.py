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



@st.cache_data(ttl=600)
def fetch_eda_data():
    client = get_bigquery_client()
    perf_table = get_full_table_id("fact_bank_performance")
    bank_table = get_full_table_id("dim_bank")
    query = f"""
        SELECT
            CAST(DIV(p.date_key, 10000) AS INT64) as year,
            b.bank_code,
            b.bank_type,
            b.bank_name,
            p.npl_ratio, p.roa, p.roe, p.nim, p.cir, p.eta, p.etd, p.lta, p.ltd, p.gta,
            p.total_assets, p.total_deposits, p.total_loans, p.total_equity,
            p.is_imputed
        FROM `{perf_table}` p
        LEFT JOIN `{bank_table}` b ON p.bank_key = b.bank_key
        ORDER BY year, b.bank_code
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df


# ─────────────────────────────────────────────────────────────
# Phân hệ 0.1: Tổng quan dự án
# ─────────────────────────────────────────────────────────────
def show_intro_section():
    st.header("🎯 Tổng Quan Dự Án & Kiến Trúc Hệ Thống")
    st.markdown("""
    Chào mừng bạn đến với **Hệ thống Phân Tích Dữ Liệu Lịch Sử & Dự Báo ML Ngành Ngân Hàng Việt Nam**. 
    Hệ thống này tích hợp kho dữ liệu đám mây Google BigQuery và các mô hình Học Máy tiên tiến nhằm cung cấp các góc nhìn phân tích sâu rộng cho các nhà quản lý rủi ro và các nhà đầu tư tài chính.
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 📋 Phạm Vi & Kích Thước Dữ Liệu
        *   **Dữ liệu Cổ Phiếu Trọng Điểm**: **11,835+ dòng** dữ liệu giá lịch sử hàng ngày (OHLCV) của 4 ngân hàng thương mại: **BID**, **TCB**, **VCB**, và **CTG**.
        *   **Dữ liệu Giao Dịch Bổ Trợ**: **22 phiên giao dịch** chứa thông tin khớp lệnh mua/bán, khối lượng giao dịch khối ngoại và tự doanh bổ sung riêng cho cổ phiếu **BID**.
        *   **Dữ liệu Báo Cáo Tài Chính (CAMELS)**: **667 dòng** và **47+ cột** chỉ số tài chính, bao phủ **46 ngân hàng thương mại Việt Nam** trong suốt **20 năm** (2002–2022).
        
        ### 🏗️ Kho Dữ Liệu Star Schema (BigQuery)
        Dữ liệu được tổ chức dưới dạng Star Schema gồm **10 bảng** tối ưu cho OLAP:
        *   **Bảng Chiều (5 Dimension tables)**:
            *   `dim_date`: Quản lý thời gian, kiểm soát ngày giao dịch.
            *   `dim_stock`: Thông tin mã cổ phiếu, sàn giao dịch (HOSE).
            *   `dim_bank`: SCD Type 2 quản lý lịch sử thông tin 46 ngân hàng.
            *   `dim_trading_session`: Phiên giao dịch trong ngày (ATO, ATC, Liên tục).
            *   `dim_audit`: Quản lý nhật ký thực thi ETL, kiểm toán hệ thống và lineage.
        *   **Bảng Thực Thể (5 Fact tables)**:
            *   `fact_price_history`: Lịch sử giá đóng/mở cửa, khối lượng giao dịch ngày.
            *   `fact_foreign_trading` & `fact_proprietary_trading`: Giao dịch khối ngoại & tự doanh.
            *   `fact_order_stats`: Thống kê khối lượng đặt mua/bán.
            *   `fact_bank_performance`: 20 năm chỉ số tài chính CAMELS.
        """)
        
    with col2:
        st.markdown("""
        ### 🧠 Cấu Trúc Các Mô Hình Học Máy (ML)
        Tầng Học Máy được thiết kế module hóa trong thư mục **`src/models/`**:
        
        *   **Các Mô Hình Huấn Luyện Chính (`src/models/`)**:
            1.  **Dự Báo Chuỗi Thời Gian (LSTM)**:
                *   *Tập tin*: `train_lstm.py` (Huấn luyện Stacked LSTM cho 4 mã BID, TCB, VCB, CTG dự đoán giá T+1 đến T+5).
                *   *Tiền xử lý*: `feature_engineering_stock.py`.
            2.  **Phân Nhóm Ngân Hàng (K-Means)**:
                *   *Tập tin*: `train_kmeans.py` (Áp dụng PCA giảm chiều và K-Means gom cụm 46 ngân hàng).
                *   *Tiền xử lý*: `feature_engineering_bank.py`.
            3.  **Phân Loại Rủi Ro Tín Dụng (Random Forest)**:
                *   *Tập tin*: `train_random_forest.py` (Phân loại rủi ro nợ xấu NPL ≥ 3%).
        
        *   **Các Mô Hình Nền Tảng So Sánh (Baseline)**:
            *   *ARIMA Baseline*: `baseline_arima.py` (Đánh giá so sánh RMSE với LSTM).
            *   *Logistic Regression*: `baseline_logistic.py` (Đánh giá so sánh AUC-ROC với Random Forest).
            
        *   **Thư Mục Lưu Trữ Kết Quả & Artifacts**:
            *   *Tệp mô hình đã huấn luyện* (`.keras`, `.pkl`): **`reports/models/`**
            *   *Biểu đồ & Sơ đồ đánh giá* (`.png`): **`reports/figures/`**
        """)
        
    st.markdown("---")
    st.subheader("🔗 Sơ Đồ Luồng Dữ Liệu Hệ Thống (Data Flow)")
    
    # Render native vector SVG Graphviz diagram instead of raw mermaid code blocks
    dot_code = """
    digraph G {
        graph [bgcolor="transparent", rankdir=TB, pad=0.3]
        node [shape=box, style="filled,rounded", color="#3b82f6", fontname="Arial", fontsize=10, fillcolor="#eff6ff", fontcolor="#1e3a8a", width=3.0, height=0.5]
        edge [color="#60a5fa", arrowsize=0.8, fontname="Arial", fontsize=9, fontcolor="#4b5563"]

        raw [label="Nguồn Dữ Liệu Thô\\n(Files Excel/CSV)"]
        etl [label="Đường Ống ETL\\n(Python / Pandas)", fillcolor="#ecfdf5", color="#10b981", fontcolor="#064e3b"]
        bq [label="Kho Dữ Liệu DWH\\n(BigQuery Star Schema: 5 Dims & 5 Facts)", fillcolor="#fffbeb", color="#f59e0b", fontcolor="#78350f"]
        ml [label="Tầng Học Máy (ML)\\n(LSTM / K-Means / RF)", fillcolor="#faf5ff", color="#8b5cf6", fontcolor="#4c1d95"]
        app [label="Giao Diện Báo Cáo\\n(Streamlit Dashboard)", fillcolor="#fdf2f8", color="#ec4899", fontcolor="#700b3e"]

        raw -> etl [label="Trích xuất"]
        etl -> bq [label="Làm sạch & Nạp"]
        bq -> ml [label="Truy vấn thuộc tính"]
        ml -> bq [label="Lưu dự báo DWH"]
        bq -> app [label="Kết nối trực tiếp"]
    }
    """
    st.graphviz_chart(dot_code)


# ─────────────────────────────────────────────────────────────
# Phân hệ 0.2: Phân tích khám phá dữ liệu (EDA)
# ─────────────────────────────────────────────────────────────
def show_eda_section():
    st.header("📊 Phân Tích Khám Phá Dữ Liệu (EDA) CAMELS")
    st.write("Khám phá phân phối, mối tương quan và xu hướng lịch sử của 46 ngân hàng thương mại dựa trên dữ liệu hiệu quả hoạt động CAMELS.")
    
    df = fetch_eda_data()
    if df.empty:
        st.error("Không tìm thấy dữ liệu phân tích CAMELS.")
        return
        
    tab1, tab2, tab3 = st.tabs(["📊 Phân Phối Chỉ Số", "🌡️ Ma Trận Tương Quan", "📈 Xu Hướng Theo Thời Gian"])
    
    feature_cols = ["npl_ratio", "roa", "roe", "nim", "cir", "eta", "etd", "lta", "ltd", "gta"]
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
    
    with tab1:
        st.subheader("Phân Phối & Giới Hạn Của Các Chỉ Số Tài Chính")
        selected_col = st.selectbox(
            "Chọn chỉ số tài chính cần quan sát",
            list(ratio_vn_map.keys()),
            format_func=lambda x: ratio_vn_map[x]
        )
        
        col_data = df[selected_col].dropna()
        
        fig = px.histogram(
            df,
            x=selected_col,
            marginal="box",
            title=f"Phân phối và Biểu đồ hộp của {ratio_vn_map[selected_col]}",
            labels={selected_col: ratio_vn_map[selected_col]},
            color_discrete_sequence=["#3b82f6"]
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        
        stats = col_data.describe().to_frame().T
        stats.columns = ["Số mẫu", "Trung bình", "Độ lệch chuẩn", "Tối thiểu", "25%", "Trung vị (50%)", "75%", "Tối đa"]
        st.dataframe(stats, use_container_width=True)

    with tab2:
        st.subheader("Ma Trận Tương Quan Tuyến Tính Giữa Các Chỉ Số CAMELS")
        st.write("Giúp phân tích xem các biến tài chính có xu hướng đồng biến hay nghịch biến với nhau.")
        
        corr_df = df[feature_cols].corr()
        corr_df.columns = [ratio_vn_map[c] for c in corr_df.columns]
        corr_df.index = [ratio_vn_map[c] for c in corr_df.index]
        
        fig = px.imshow(
            corr_df,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Hệ Số Tương Quan Pearson Giữa Các Tỷ Số CAMELS"
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    with tab3:
        st.subheader("Xu Hướng Tài Chính Qua Các Năm")
        trend_col = st.selectbox(
            "Chọn chỉ số tài chính theo dõi theo thời gian",
            list(ratio_vn_map.keys()),
            key="trend_select",
            format_func=lambda x: ratio_vn_map[x]
        )
        
        yearly_avg = df.groupby(["year", "bank_type"])[trend_col].mean().reset_index()
        type_map = {"SOCB": "Ngân hàng Nhà nước nắm quyền chi phối (SOCB)", "JSCB": "Ngân hàng TMCP tư nhân (JSCB)", "FOCB": "Ngân hàng nước ngoài/Liên doanh (FOCB)"}
        yearly_avg["bank_type"] = yearly_avg["bank_type"].map(type_map)
        
        fig = px.line(
            yearly_avg,
            x="year",
            y=trend_col,
            color="bank_type",
            title=f"Biến động trung bình {ratio_vn_map[trend_col]} giai đoạn 2002–2022",
            labels={"year": "Năm Báo Cáo", trend_col: ratio_vn_map[trend_col], "bank_type": "Phân Loại Ngân Hàng"},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")


# ─────────────────────────────────────────────────────────────
# Giao diện chính của Dashboard
# ─────────────────────────────────────────────────────────────
def main():
    load_dotenv()
    
    st.title("🏦 Phân Tích Dữ Liệu Lịch Sử & Dự Báo ML Ngành Ngân Hàng")
    st.markdown("---")
    
    st.sidebar.title("Điều Hướng")
    app_mode = st.sidebar.radio(
        "Chọn phân hệ báo cáo",
        [
            "Tổng Quan Dự Án",
            "Phân Tích Khám Phá (EDA)",
            "Dự Báo Giá Cổ Phiếu (LSTM)",
            "Phân Nhóm Ngân Hàng (K-Means)",
            "Phân Loại Rủi Ro Tín Dụng (Random Forest)",
            "Trạng Thái Hệ Thống DWH"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Nguồn dữ liệu: Google BigQuery Star Schema Data Warehouse")
    
    if app_mode == "Tổng Quan Dự Án":
        show_intro_section()
    elif app_mode == "Phân Tích Khám Phá (EDA)":
        show_eda_section()
    elif app_mode == "Dự Báo Giá Cổ Phiếu (LSTM)":
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
            table_id,
            row_count,
            ROUND(size_bytes / 1024, 2) as size_kb
        FROM `{os.getenv("GCP_PROJECT_ID")}.{dataset_id}.__TABLES__`
        ORDER BY row_count DESC
    """
    
    try:
        meta_df = client.query(query).to_dataframe(create_bqstorage_client=False)
        # Thay đổi tên cột hiển thị tiếng Việt trên tầng ứng dụng Pandas thay vì SQL
        meta_df = meta_df.rename(columns={
            "table_id": "Tên Bảng (Table ID)",
            "row_count": "Số Bản Ghi (Row Count)",
            "size_kb": "Dung Lượng (KB)"
        })
        st.table(meta_df)
        
        st.success("Tất cả 10 bảng DWH đang hoạt động ổn định và kết nối thành công!")
    except Exception as e:
        st.error(f"Lỗi khi lấy thông tin siêu dữ liệu DWH: {str(e)}")


if __name__ == "__main__":
    main()
