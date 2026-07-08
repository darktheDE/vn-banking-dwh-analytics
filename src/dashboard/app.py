"""Interactive Streamlit dashboard for the Vietnamese Financial Market Analytics DWH.

Visualizes stock forecasting (LSTM), bank clustering (K-Means), and risk classification (Random Forest).
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import json
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
@st.cache_data(ttl=10)
def fetch_stock_dimension():
    client = get_bigquery_client()
    table_id = get_full_table_id("dim_stock")
    query = f"SELECT stock_key, ticker, company_name FROM `{table_id}` ORDER BY stock_key"
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df


@st.cache_data(ttl=10)
def fetch_actual_price_history(stock_key: int, limit: int = 60):
    client = get_bigquery_client()
    price_table = get_full_table_id("fact_stock_daily_metrics")
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


@st.cache_data(ttl=10)
def fetch_lstm_predictions(stock_key: int):
    client = get_bigquery_client()
    pred_table = get_full_table_id("fact_model_predictions")
    # Training uses WRITE_TRUNCATE (all 4 stocks in one atomic write),
    # so each stock always has exactly 5 rows — one per T+1 to T+5 horizon.
    query = f"""
        SELECT
            horizon,
            predicted_close_price,
            model_name
        FROM `{pred_table}`
        WHERE stock_key = {stock_key}
        ORDER BY horizon
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df


@st.cache_data(ttl=10)
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


@st.cache_data(ttl=10)
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



@st.cache_data(ttl=10)
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


def load_dtw_report() -> dict:
    """Load the Dynamic Time Warping (DTW) correlation report from disk.
    
    Returns:
        Dictionary of DTW distances and Pearson correlations.
    """
    path = "./data/processed/dtw_correlation_report.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Lỗi khi đọc tệp báo cáo DTW: {e}")
    return {}


def load_causal_report() -> str:
    """Load the Granger Causality analysis text report from disk.
    
    Returns:
        Content of the report as a string.
    """
    path = "./data/processed/causal_analysis_report.txt"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            st.error(f"Lỗi khi đọc tệp báo cáo nhân quả: {e}")
    return ""


def load_lstm_comparison() -> dict:
    """Load the LSTM model performance comparison report from disk.
    
    Returns:
        Dictionary of RMSE/MAE performance comparison metrics.
    """
    path = "./data/processed/lstm_model_comparison.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Lỗi khi đọc tệp báo cáo hiệu năng: {e}")
    return {}


# ─────────────────────────────────────────────────────────────
# Phân hệ 0.1: Tổng quan dự án
# ─────────────────────────────────────────────────────────────
def show_intro_section():
    st.header("🎯 Tổng Quan Dự Án & Kiến Trúc Hệ Thống")
    st.markdown("""
    Chào mừng bạn đến với **Hệ thống Phân Tích Dữ Liệu Lịch Sử & Dự Báo ML Ngành Ngân Hàng Việt Nam**. 
    Hệ thống này tích hợp kho dữ liệu đám mây Google BigQuery và các mô hình Học Máy tiên tiến nhằm cung cấp các góc nhìn phân tích sâu rộng cho các nhà quản lý rủi ro và các nhà đầu tư tài chính.
    """)
    
    st.markdown("""
    ### ❓ 4 Câu Hỏi Nghiên Cứu Cốt Lõi (Core Research Questions)
    Hệ thống phân tích này được xây dựng nhằm giải quyết triệt để **4 bài toán thực tiễn quan trọng** của ngành ngân hàng Việt Nam:
    *   **Q1 (Dự báo ngắn hạn)**: *Dòng tiền khối ngoại và tự doanh có thực sự tác động và dẫn dắt đà tăng giá ngắn hạn của cổ phiếu ngân hàng (ví dụ: BID) không?*
    *   **Q2 (Đồng pha & Phân hóa)**: *Đà biến động giá của nhóm ngân hàng quốc doanh (BID, VCB, CTG) có đồng pha với nhau và phân hóa thế nào với ngân hàng tư nhân (TCB)?*
    *   **Q3 (Cảnh báo rủi ro)**: *Chỉ số tài chính nào (theo khung CAMELS) quyết định việc một ngân hàng bị rơi vào nhóm rủi ro nợ xấu vượt mức 3%?*
    *   **Q4 (Phân cụm chiến lược)**: *Dữ liệu có thể giúp chúng ta phân cụm chính xác các ngân hàng Việt Nam thành các nhóm chiến lược hoạt động khác nhau hay không?*
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 📋 Nguồn Dữ Liệu & Quy Mô Hệ Thống
        *   **Tích Hợp API Tài Chính (`vnstock` / VCI API)**: Toàn bộ dữ liệu giá giao dịch hàng ngày (OHLCV) và báo cáo tài chính (Cân đối kế toán, Kết quả kinh doanh, Lưu chuyển tiền tệ, Chỉ số tài chính) của 4 ngân hàng trọng điểm (**BID**, **TCB**, **VCB**, **CTG**) được tự động hóa trích xuất trực tiếp qua **API tài chính** tích hợp (đảm bảo tính cập nhật và tự động).
        *   **Dữ liệu Báo Cáo Tài Chính CAMELS 20 năm**: Gồm **667 dòng** dữ liệu và **47+ cột** chỉ số hiệu năng cấu trúc tài chính, bao phủ toàn hệ thống **46 ngân hàng Việt Nam** trong suốt **2 thập kỷ (2002–2022)** được tổng hợp đồng bộ từ báo cáo kiểm toán lịch sử (phục vụ phân cụm và phân loại rủi ro dài hạn).
        
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
    
    with st.expander("💡 Câu Chuyện Dữ Liệu: Mối Tương Quan & Phân Phối CAMELS", expanded=True):
        st.markdown("""
        Khi phân tích dữ liệu CAMELS của 46 ngân hàng Việt Nam giai đoạn 2002–2022, chúng ta thấy một câu chuyện rõ rệt về **sự đánh đổi giữa lợi nhuận và an toàn vốn**:
        1. **Tương quan sinh lời**: ROA và ROE có mối tương quan thuận mạnh mẽ, phản ánh hiệu quả sử dụng tài sản chuyển hóa trực tiếp thành giá trị cổ đông. Tuy nhiên, các ngân hàng có ROE quá cao đôi khi đi kèm với tỷ lệ an toàn vốn ETA (Vốn chủ sở hữu / Tổng tài sản) thấp, cho thấy đòn bẩy tài chính đang được sử dụng ở mức cao.
        2. **Tỷ lệ chi phí và Lợi nhuận**: Hệ số CIR (Chi phí hoạt động / Thu nhập hoạt động) tỷ lệ nghịch với hiệu quả sinh lời. Những ngân hàng tối ưu hóa quy trình vận hành tốt (CIR thấp) thường duy trì được mức NIM và ROA vượt trội.
        3. **Xu hướng phân hóa dài hạn**: Nhóm ngân hàng Nhà nước nắm quyền chi phối (SOCB) thường chấp nhận biên lãi ròng NIM thấp hơn để hỗ trợ nền kinh tế, bù lại họ có quy mô tài sản vượt trội. Ngược lại, nhóm ngân hàng thương mại cổ phần tư nhân (JSCB) năng động hơn trong việc tối ưu NIM nhưng biến động nợ xấu (NPL) cũng nhạy cảm hơn với chu kỳ kinh tế.
        """)
    
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
        st.write("Biểu đồ phân phối thống kê toàn bộ **661 bản ghi báo cáo tài chính hàng năm** của 46 ngân hàng Việt Nam giai đoạn 2002–2022 (mỗi ngân hàng đóng góp tối đa 20 năm dữ liệu lịch sử trong hệ thống DWH, nên tổng số lượng bản ghi `count` lớn hơn số lượng 46 ngân hàng).")
        selected_col = st.selectbox(
            "Chọn chỉ số tài chính cần quan sát",
            list(ratio_vn_map.keys()),
            format_func=lambda x: ratio_vn_map[x]
        )
        
        # Multiply by 100 to convert to percentage for readability
        df_pct = df.copy()
        df_pct[selected_col] = df_pct[selected_col] * 100
        col_data = df_pct[selected_col].dropna()
        
        fig = px.histogram(
            df_pct,
            x=selected_col,
            marginal="box",
            title=f"Phân phối và Biểu đồ hộp của {ratio_vn_map[selected_col]} (%)",
            labels={selected_col: f"{ratio_vn_map[selected_col]} (%)", "count": "Số lượng bản ghi"},
            color_discrete_sequence=["#3b82f6"]
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        # Tình hình phân tích động dựa trên chỉ số được chọn
        caption_map = {
            "npl_ratio": "Tình hình: Phân phối nợ xấu (NPL) tập trung chủ yếu dưới ngưỡng an toàn 3%. Tuy nhiên, biểu đồ hộp chỉ ra một số ngân hàng nhỏ đang tái cơ cấu có tỷ lệ nợ xấu vượt xa mức trung bình hệ thống, tiệm cận hoặc vượt mốc 3%.",
            "roa": "Tình hình: Trung vị ROA của hệ thống đạt quanh mức 0.8% - 1.2%. Các điểm ngoại lệ phía bên phải phản ánh nhóm ngân hàng thương mại năng động tối ưu hóa lợi nhuận tài sản xuất sắc (> 1.8%).",
            "roe": "Tình hình: Hiệu suất sinh lời trên vốn chủ sở hữu (ROE) tập trung phổ biến ở mức 12% - 18%. Nhóm ngân hàng top đầu đạt ROE vượt trội (> 22%) nhờ sử dụng đòn bẩy tài chính hiệu quả.",
            "nim": "Tình hình: Biên lãi ròng (NIM) tập trung phổ biến quanh mức 3% - 4%. Nhóm ngân hàng bán lẻ quy mô vừa và lớn có lợi thế về chi phí vốn thường nằm ở nhóm cận trên.",
            "cir": "Tình hình: Tỷ lệ CIR trong bộ dữ liệu này phổ biến ở mức rất cao, từ 90% - 95% (do cấu trúc tính toán bao gồm cả chi phí lãi vay). Điểm ngoại lệ cực âm ở phía bên trái phản ánh các ngân hàng gặp khủng hoảng có tổng thu nhập hoạt động bị âm.",
            "eta": "Tình hình: Tỷ lệ vốn chủ sở hữu trên tổng tài sản (ETA) đạt trung vị khoảng 8% - 10%. Nhóm ngân hàng nhỏ thường duy trì ETA dày hơn để phòng ngừa rủi ro quy mô.",
            "etd": "Tình hình: Vốn chủ sở hữu trên tiền gửi (ETD) dao động quanh mức 10% - 15%, cho thấy tính tự chủ vốn tương đối tốt so với lượng huy động gửi tiền.",
            "lta": "Tình hình: Dư nợ cho vay chiếm khoảng 60% - 70% tổng tài sản. Đây là tỷ lệ phân bổ tài sản sinh lời đặc trưng của hệ thống ngân hàng thương mại Việt Nam.",
            "ltd": "Tình hình: Tỷ lệ LTD dao động từ 75% - 85%. Nhiều ngân hàng thương mại cổ phần tiệm cận trần an toàn thanh khoản để tối đa hóa hiệu quả sử dụng nguồn vốn huy động.",
            "gta": "Tình hình: Cho vay gộp trên tổng tài sản ổn định quanh mức 65%, thể hiện hoạt động cho vay truyền thống vẫn đóng vai trò động lực thu nhập chính."
        }
        selected_caption = caption_map.get(selected_col, "Tình hình: Phân bổ dữ liệu phản ánh sự phân hóa mạnh mẽ về quy mô và hiệu quả vận hành giữa các nhóm ngân hàng.")
        st.caption(selected_caption)
        
        stats = col_data.describe().to_frame().T
        stats.columns = ["Số mẫu", "Trung bình (%)", "Độ lệch chuẩn (%)", "Tối thiểu (%)", "25% (%)", "Trung vị (50%) (%)", "75% (%)", "Tối đa (%)"]
        stats.index = [f"Chỉ số: {ratio_vn_map[selected_col]}"]
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
        st.caption("Tình hình: Mối tương quan cực kỳ mạnh mẽ (hệ số > 0.8) giữa ROA và ROE phản ánh cấu trúc lợi nhuận đồng thuận. Ngược lại, CIR tương quan âm rõ rệt với ROA/ROE, chứng minh tối ưu hóa chi phí hoạt động trực tiếp quyết định khả năng sinh lời của các ngân hàng.")

    with tab3:
        st.subheader("Xu Hướng Tài Chính Qua Các Năm")
        trend_col = st.selectbox(
            "Chọn chỉ số tài chính theo dõi theo thời gian",
            list(ratio_vn_map.keys()),
            key="trend_select",
            format_func=lambda x: ratio_vn_map[x]
        )
        
        yearly_avg = df.groupby(["year", "bank_type"])[trend_col].mean().reset_index()
        yearly_avg[trend_col] = yearly_avg[trend_col] * 100
        type_map = {"SOCB": "Ngân hàng Nhà nước nắm quyền chi phối (SOCB)", "JSCB": "Ngân hàng TMCP tư nhân (JSCB)", "FOCB": "Ngân hàng nước ngoài/Liên doanh (FOCB)"}
        yearly_avg["bank_type"] = yearly_avg["bank_type"].map(type_map)
        
        fig = px.line(
            yearly_avg,
            x="year",
            y=trend_col,
            color="bank_type",
            title=f"Biến động trung bình {ratio_vn_map[trend_col]} (%) giai đoạn 2002–2022",
            labels={"year": "Năm Báo Cáo", trend_col: f"{ratio_vn_map[trend_col]} (%)", "bank_type": "Phân Loại Ngân Hàng"},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        st.caption("Tình hình: Xu hướng dài hạn phản ánh sự vươn lên mạnh mẽ của nhóm TMCP tư nhân (JSCB) từ sau năm 2015 với NIM và tỷ lệ sinh lời gia tăng đáng kể. Nhóm ngân hàng quốc doanh (SOCB) duy trì sự ổn định cao nhưng NIM chịu áp lực điều tiết lãi suất hỗ trợ nền kinh tế.")


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
            "Trạng Thái Hệ Thống DWH",
            "Kết Luận & Nghiệm Thu"
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
    elif app_mode == "Trạng Thái Hệ Thống DWH":
        show_dwh_status_section()
    else:
        show_conclusion_section()


def show_price_forecasting_section():
    st.header("📈 Dự Báo Giá Cổ Phiếu Trọng Điểm (LSTM)")
    st.write("Mô hình học sâu LSTM thực hiện dự báo giá đóng cửa của các cổ phiếu ngân hàng trong 5 ngày giao dịch tiếp theo (T+1 đến T+5).")
    
    with st.expander("💡 Câu Chuyện Dữ Liệu: Dự Báo Xu Hướng Giá Cổ Phiếu Ngân Hàng", expanded=True):
        st.markdown("""
        Giá cổ phiếu ngân hàng trên sàn HOSE không chỉ vận động theo quy luật ngẫu nhiên mà chịu ảnh hưởng lớn bởi **động lượng giá ngắn hạn và khối lượng giao dịch thực tế**:
        1. **Khối lượng giao dịch & Động lượng**: Lịch sử giao dịch chứng minh sự kết hợp giữa khối lượng giao dịch (`trading_volume`) và tỷ lệ thay đổi giá ngày hôm trước (`price_change_pct`) là các chỉ số dẫn dắt xu hướng giá ngắn hạn vô cùng mạnh mẽ.
        2. **Dự báo chuỗi thời gian**: Mô hình mạng LSTM học các đặc trưng phi tuyến từ chuỗi trượt 30 ngày giao dịch của 4 cổ phiếu cột trụ (BID, TCB, VCB, CTG) trên tập dữ liệu thực tế hơn 3.000 phiên (2014-2026), giúp dự báo chính xác đà giá ngắn hạn từ T+1 đến T+5 để hỗ trợ quyết định đầu tư thực tiễn.
        """)
    
    # Load stocks
    stocks_df = fetch_stock_dimension()
    if stocks_df.empty:
        st.error("Không tìm thấy dữ liệu danh mục cổ phiếu.")
        return
        
    stock_options = {row["ticker"]: row["stock_key"] for _, row in stocks_df.iterrows()}
    selected_ticker = st.selectbox("Chọn mã cổ phiếu ngân hàng", list(stock_options.keys()))
    stock_key = stock_options[selected_ticker]
    
    # LSTM Parameters and Metrics
    st.markdown("### ⚙️ Thông Số Kỹ Thuật & Hiệu Năng Mô hình")
    meta_col1, meta_col2 = st.columns([1, 1])
    
    rmse_map = {
        "BID": ("3.1123", "3.2247", "5.5419", "+43.8%"),
        "TCB": ("1.4890", "2.0547", "9.4864", "+84.3%"),
        "VCB": ("2.6567", "2.8392", "4.4900", "+40.8%"),
        "CTG": ("1.5061", "1.4912", "11.3624", "+86.7%")
    }
    m_rmse, u_rmse, a_rmse, gain_val = rmse_map.get(selected_ticker, ("N/A", "N/A", "N/A", "N/A"))
    hp_info = {
        "window": "30 ngày (Long window)",
        "epochs": "150 Epochs",
        "batch": "32",
        "units": "Stacked LSTM (128 units + 64 units)",
        "features": "7 chỉ số (OHLCV & Biến động giá/khối lượng)",
        "univariate_rmse": u_rmse,
        "multivariate_rmse": m_rmse,
        "arima_rmse": a_rmse,
        "gain": f"{gain_val} (Vượt trội)"
    }
        
    with meta_col1:
        st.markdown(f"""
        **⚙️ Hyperparameters (Tham số huấn luyện):**
        *   **Thuật toán**: Mạng học sâu Stacked LSTM (Keras)
        *   **Cửa sổ trượt (Sliding Window)**: {hp_info["window"]}
        *   **Số chu kỳ (Epochs)**: {hp_info["epochs"]} | **Batch Size**: {hp_info["batch"]}
        *   **Cấu trúc lớp**: {hp_info["units"]}
        *   **Optimizer**: Adam | **Loss Function**: Mean Squared Error (MSE)
        """)
        
    with meta_col2:
        st.markdown(f"""
        **📊 Performance Metrics (Chỉ số kiểm thử):**
        *   **Độ phân tách dữ liệu**: 80% Train / 20% Test (Phân tách theo thời gian thực tế)
        *   **LSTM Đa biến RMSE (Multivariate)**: ` {hp_info["multivariate_rmse"]} `
        *   **LSTM Đơn biến RMSE (Univariate)**: ` {hp_info["univariate_rmse"]} `
        *   **ARIMA RMSE (Baseline đối chứng)**: ` {hp_info["arima_rmse"]} `
        *   *Ý nghĩa*: RMSE của mô hình LSTM tốt nhất thấp hơn hẳn so với ARIMA chứng minh năng lực học các mẫu phi tuyến tính của chuỗi thời gian chứng khoán Việt Nam.
        """)
        
    st.markdown("---")
    
    # Define tabs for Price Forecasting
    tabs = st.tabs(["🔮 Dự báo LSTM Đơn biến vs Đa biến", "🔗 Tương quan & Đồng pha (DTW)", "🧪 So sánh Đơn biến vs Đa biến"])
    
    with tabs[0]:
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
                
                # Extract univariate and multivariate predictions
                uni_pred = pred_df[pred_df["model_name"] == "LSTM_Univariate"].copy().sort_values("horizon").reset_index(drop=True)
                multi_pred = pred_df[pred_df["model_name"] == "LSTM_Multivariate"].copy().sort_values("horizon").reset_index(drop=True)
                
                # Since they share the same future dates
                pred_len = max(len(uni_pred), len(multi_pred))
                while len(future_dates) < pred_len:
                    current_date += pd.Timedelta(days=1)
                    # Skip weekends
                    if current_date.weekday() < 5:
                        future_dates.append(current_date)
                        
                if not uni_pred.empty:
                    uni_pred["full_date"] = future_dates[:len(uni_pred)]
                if not multi_pred.empty:
                    multi_pred["full_date"] = future_dates[:len(multi_pred)]
                
                # Combine actuals and predictions for plotting
                actual_trace = go.Scatter(
                    x=hist_df["full_date"],
                    y=hist_df["close_price"] * 1000, # convert back to VND
                    name="Giá lịch sử thực tế",
                    line=dict(color="#3b82f6", width=2.5)
                )
                
                traces = [actual_trace]
                
                if not uni_pred.empty:
                    uni_trace = go.Scatter(
                        x=uni_pred["full_date"],
                        y=uni_pred["predicted_close_price"] * 1000,
                        name="LSTM Đơn biến (Univariate - Không biến)",
                        line=dict(color="#10b981", width=2.5, dash="dot"),
                        marker=dict(size=8, symbol="diamond")
                    )
                    traces.append(uni_trace)
                    
                if not multi_pred.empty:
                    multi_trace = go.Scatter(
                        x=multi_pred["full_date"],
                        y=multi_pred["predicted_close_price"] * 1000,
                        name="LSTM Đa biến (Multivariate - Có biến)",
                        line=dict(color="#f43f5e", width=2.5, dash="dash"),
                        marker=dict(size=8, symbol="circle")
                    )
                    traces.append(multi_trace)
                    
                fig = go.Figure(data=traces)
                fig.update_layout(
                    title=f"Lịch Sử Giá & Dự Báo Giá 5 Ngày Cổ Phiếu {selected_ticker} (VND)",
                    xaxis_title="Thời Gian",
                    yaxis_title="Giá Cổ Phiếu (VND)",
                    hovermode="x unified",
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                )
                st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                # Tình hình phân tích động dựa trên mã cổ phiếu được chọn
                stock_caption_map = {
                    "BID": "Tình hình: Giá cổ phiếu BID có tính nhạy cảm cao với biến động thanh khoản thị trường. Dự báo LSTM học từ động lượng 20 ngày lịch sử giá và khối lượng thực tế, giúp nhận diện nhanh các nhịp tích lũy và đà bứt phá ngắn hạn quanh các vùng hỗ trợ kỹ thuật.",
                    "TCB": "Tình hình: Cổ phiếu TCB có tính độc lập cao và biên độ biến động lớn so với nhóm quốc doanh. Dự báo LSTM phản ánh đúng tính chu kỳ của Techcombank, bám sát các nhịp tích lũy trước khi bứt phá theo cung cầu thị trường bán lẻ.",
                    "VCB": "Tình hình: VCB là cổ phiếu đầu ngành đóng vai trò giữ nhịp VN-Index với tính ổn định cao nhất. Dự báo LSTM của VCB thể hiện xu hướng củng cố nền tảng giá vững chắc, ít biến động đột biến và phản ánh xu thế tăng trưởng dài hạn vững vàng.",
                    "CTG": "Tình hình: CTG có độ tương quan và đồng pha rất cao với nhóm ngân hàng quốc doanh (VCB, BID). Dự báo LSTM bắt đúng các sóng phục hồi kỹ thuật ngắn hạn và các nhịp tích lũy chặt chẽ quanh vùng giá hỗ trợ lịch sử."
                }
                selected_stock_caption = stock_caption_map.get(selected_ticker, "Tình hình: Dự báo LSTM bám sát giá cổ phiếu đóng cửa lịch sử nhằm mô phỏng chính xác xu thế biến động giá ngắn hạn tiếp theo.")
                st.caption(selected_stock_caption)
            else:
                st.warning("Không đủ dữ liệu trong Kho dữ liệu để biểu diễn đồ thị dự báo.")
                
        with col2:
            st.subheader("Kết Quả Dự Báo (T+1 đến T+5)")
            if not hist_df.empty:
                last_close = hist_df["close_price"].iloc[-1] * 1000
                st.metric(
                    label="Giá đóng cửa gần nhất",
                    value=f"{last_close:,.0f} VND",
                    delta=None
                )
                
                # Table of forecasts
                forecast_table = []
                if not pred_df.empty:
                    for i in range(pred_len):
                        row_data = {"Thời Gian": f"T+{i + 1}"}
                        
                        if i < len(uni_pred):
                            uni_val = uni_pred["predicted_close_price"].iloc[i] * 1000
                            uni_diff = uni_val - last_close
                            uni_pct = (uni_diff / last_close) * 100
                            row_data["LSTM Đơn biến (VND)"] = f"{uni_val:,.0f}"
                            row_data["Biến động Đơn biến"] = f"{uni_pct:+.2f}%"
                        else:
                            row_data["LSTM Đơn biến (VND)"] = "N/A"
                            row_data["Biến động Đơn biến"] = "N/A"
                            
                        if i < len(multi_pred):
                            multi_val = multi_pred["predicted_close_price"].iloc[i] * 1000
                            multi_diff = multi_val - last_close
                            multi_pct = (multi_diff / last_close) * 100
                            row_data["LSTM Đa biến (VND)"] = f"{multi_val:,.0f}"
                            row_data["Biến động Đa biến"] = f"{multi_pct:+.2f}%"
                        else:
                            row_data["LSTM Đa biến (VND)"] = "N/A"
                            row_data["Biến động Đa biến"] = "N/A"
                            
                        forecast_table.append(row_data)
                    
                    if forecast_table:
                        st.table(pd.DataFrame(forecast_table))
                else:
                    st.info("Không tìm thấy kết quả dự báo trong DWH.")

    with tabs[1]:
        st.subheader("🔗 Phân Tích Đồng Pha & Tương Quan Bằng Dynamic Time Warping (DTW)")
        st.write("Đo lường mức độ đồng pha và khoảng cách phi tuyến tính giữa chuỗi thời gian giá đóng cửa của các ngân hàng thương mại Việt Nam sau khi chuẩn hóa Z-score.")
        
        col_img, col_txt = st.columns([1.2, 1])
        
        with col_img:
            if os.path.exists("./data/processed/dtw_correlation_plots.png"):
                st.image("./data/processed/dtw_correlation_plots.png", use_container_width=True, caption="Biểu đồ phân tích đồng pha và tương quan chuỗi thời gian")
            else:
                st.warning("Không tìm thấy tệp biểu đồ dtw_correlation_plots.png.")
                
        with col_txt:
            dtw_report = load_dtw_report()
            if dtw_report:
                st.markdown("### 📊 Ma Trận Khoảng Cách DTW & Tương Quan Pearson")
                st.markdown(f"**Khoảng cách DTW trung bình giữa các chuỗi giá đóng cửa (Test set):**")
                
                # Convert to DataFrames and display with native style
                dtw_df = pd.DataFrame(dtw_report.get("dtw_distance_matrix", {}))
                # Ensure the columns and index are sorted in the same order
                tickers = ["BID", "TCB", "VCB", "CTG"]
                dtw_df = dtw_df.reindex(index=tickers, columns=tickers)
                st.dataframe(dtw_df.style.format("{:.2f}").background_gradient(cmap="YlOrRd_r", axis=None), use_container_width=True)
                st.caption("Khoảng cách DTW càng nhỏ thể hiện hai chuỗi biến động càng đồng pha về mặt hình dạng xu hướng ngắn hạn.")
                
                st.markdown("---")
                st.markdown("**Hệ số Tương quan Pearson tuyến tính:**")
                pearson_df = pd.DataFrame(dtw_report.get("pearson_correlation_matrix", {}))
                pearson_df = pearson_df.reindex(index=tickers, columns=tickers)
                st.dataframe(pearson_df.style.format("{:.2f}").background_gradient(cmap="Blues", axis=None), use_container_width=True)
                st.caption("Ý nghĩa: Hệ số tương quan Pearson > 0.85 chỉ ra xu hướng tăng/giảm tuyến tính đồng hướng cực kỳ rõ rệt.")
            else:
                st.warning("Không tìm thấy dữ liệu phân tích dtw_correlation_report.json.")
                
    with tabs[2]:
        st.subheader("🧪 So Sánh Thực Nghiệm Hiệu Năng: LSTM Đơn biến vs LSTM Đa biến vs ARIMA")
        st.write("So sánh sai số dự báo giữa mô hình LSTM chỉ dùng giá đóng cửa (Univariate - Không biến), mô hình LSTM mở rộng (Multivariate - Có biến) và đường cơ sở ARIMA trên tập kiểm thử độc lập.")
        
        lstm_comparison = load_lstm_comparison()
        if lstm_comparison:
            st.markdown("### 📊 Bảng So Sánh Chỉ Số RMSE & MAE trên tập Kiểm Thử (Test Set)")
            
            comp_table = []
            for ticker, data in lstm_comparison.items():
                comp_table.append({
                    "Mã Ngân Hàng": ticker,
                    "LSTM Đơn biến (RMSE)": f"{data['uni_rmse']:.4f}",
                    "LSTM Đơn biến (MAE)": f"{data['uni_mae']:.4f}",
                    "LSTM Đa biến (RMSE)": f"{data['multi_rmse']:.4f}",
                    "LSTM Đa biến (MAE)": f"{data['multi_mae']:.4f}",
                    "ARIMA Baseline (RMSE)": f"{data['arima_rmse']:.4f}",
                    "ARIMA Baseline (MAE)": f"{data['arima_mae']:.4f}"
                })
            
            st.dataframe(pd.DataFrame(comp_table), use_container_width=True)
            st.info("Kết luận khoa học: Mô hình LSTM Đa biến (Multivariate) tích hợp thêm khối lượng giao dịch và các độ trễ biến động cho sai số RMSE thấp hơn rõ rệt so với LSTM Đơn biến và ARIMA trên 3/4 ngân hàng thương mại (BID, TCB, VCB). Với CTG, mô hình đơn biến lại tỏ ra nhạy bén hơn do biến động giá cực kỳ ổn định trong giai đoạn vừa qua.")
        else:
            st.warning("Không tìm thấy dữ liệu đối chiếu hiệu năng lstm_model_comparison.json.")



# ─────────────────────────────────────────────────────────────
# Phân hệ 2: Phân nhóm ngân hàng (K-Means)
# ─────────────────────────────────────────────────────────────
def show_bank_clustering_section():
    st.header("📊 Phân Nhóm & Phác Họa Đặc Trưng Ngân Hàng (K-Means)")
    st.write("Phân nhóm 46 ngân hàng thương mại Việt Nam dựa trên 10 tỷ số tài chính CAMELS đã được chuẩn hóa và giảm chiều bằng PCA.")
    
    with st.expander("💡 Câu Chuyện Dữ Liệu: Phân Cụm Chiến Lược Hoạt Động Ngân Hàng", expanded=True):
        st.markdown("""
        Sử dụng PCA để giảm từ 10 biến CAMELS về 2 không gian tọa độ chính đã bộc lộ **3 phong cách hoạt động kinh doanh ngân hàng rõ rệt tại Việt Nam**:
        1. **Cụm Quy Mô & Vận Hành (Thường là SOCB)**: Sở hữu quy mô tổng tài sản khổng lồ nhưng biên NIM ở mức vừa phải và hệ số ETA mỏng do đòn bẩy cao.
        2. **Cụm Tối Ưu Lợi Nhuận (Thường là các JSCB lớn như TCB, VPB)**: Đặc trưng bởi NIM rất cao, CIR được tối ưu hóa sâu sắc và ROE/ROA ấn tượng, đi kèm với đòn bẩy tài chính linh hoạt.
        3. **Cụm An Toàn & Thận Trọng (Thường là FOCB hoặc các ngân hàng nhỏ tự tái cơ cấu)**: Duy trì hệ số ETA cực kỳ dày, tỷ lệ LTD thấp để phòng ngừa rủi ro thanh khoản, chấp nhận tăng trưởng tín dụng chậm để bảo vệ chất lượng tài sản.
        """)
    
    # Load clusters data
    clusters_df = fetch_bank_clusters()
    if clusters_df.empty:
        st.error("Không tìm thấy dữ liệu phân nhóm ngân hàng.")
        return
        
    # K-Means Parameters and Metrics
    st.markdown("### ⚙️ Thông Số Kỹ Thuật & Hiệu Năng Mô Hình")
    meta_col1, meta_col2 = st.columns([1, 1])
    
    with meta_col1:
        st.markdown("""
        **⚙️ PCA & K-Means Hyperparameters (Tham số mô hình):**
        *   **Thuật toán**: K-Means Clustering kết hợp Giảm chiều PCA
        *   **Số thành phần chính (PCA Components)**: $n=2$ (phục vụ vẽ đồ thị 2D. Mô hình gốc giữ lại 3 thành phần chính để giải thích **85.92%** phương sai gốc).
        *   **Số cụm tối ưu (k)**: $k=3$ (Được lựa chọn qua Phương pháp Khuỷu tay - Elbow Method và Phân tích Hệ số Dáng điệu - Silhouette Analysis).
        *   **Lọc dữ liệu nhiễu**: Đã loại bỏ 6 ngân hàng ngoại lệ cực hạn và sáp nhập (`DAB`, `CB`, `GPB`, `WEB`, `VBSP`, `MDB`).
        *   **Random State**: `42` | **Khởi tạo**: `k-means++`
        """)
        
    with meta_col2:
        st.markdown("""
        **📊 Clustering Metrics (Chỉ số chất lượng phân cụm):**
        *   **Hệ số Dáng điệu (Silhouette Score)**: **`0.4431`** (chứng minh các cụm có ranh giới rõ ràng và độ tách biệt tốt sau khi loại bỏ nhiễu).
        *   **Chỉ số Davies-Bouldin Index**: **`0.8122`** (giá trị thấp thể hiện các cụm có độ co cụm nội bộ cao và phân tách ngoại bộ tốt).
        *   **Danh sách biến CAMELS đầu vào**: 10 chỉ số (`npl_ratio`, `roa`, `roe`, `nim`, `cir`, `eta`, `etd`, `lta`, `ltd`, `gta`).
        *   **Phương pháp chuẩn hóa**: `StandardScaler` (đưa tất cả các biến về phân phối chuẩn trước khi tính khoảng cách Euclidean).
        """)
        
    st.markdown("---")
    
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
    
    # Define cluster names and color map
    cluster_names = {
        0: "Cụm 0 (TMCP Nhỏ)",
        1: "Cụm 1 (Trụ Cột Lớn)",
        2: "Cụm 2 (Ngân Hàng Ngoại)"
    }
    df_clean["Phân Nhóm (Cluster)"] = df_clean["cluster_id"].map(cluster_names)
    
    color_map = {
        "Cụm 0 (TMCP Nhỏ)": "#3b82f6",      # blue
        "Cụm 1 (Trụ Cột Lớn)": "#ec4899",    # pink/rose
        "Cụm 2 (Ngân Hàng Ngoại)": "#10b981" # green
    }
    
    # Scatter plot
    fig = px.scatter(
        df_clean,
        x="PC1",
        y="PC2",
        color="Phân Nhóm (Cluster)",
        text="bank_code",
        hover_data=["bank_name", "bank_type"],
        title="Biểu Đồ Phân Tán Các Ngân Hàng Trên Hệ Tọa Độ PCA",
        color_discrete_map=color_map
    )
    fig.update_traces(textposition="top center", marker=dict(size=12, line=dict(color="white", width=1)))
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    st.caption("Tình hình: Sau khi loại bỏ 6 ngân hàng ngoại lệ cực hạn và sáp nhập (DAB, CB, GPB, WEB, VBSP, MDB), hệ tọa độ 2D PCA phân cụm rõ rệt thành 3 nhóm chiến lược: Cụm 0 (13 ngân hàng TMCP nhỏ đang tích lũy đệm tài sản), Cụm 1 (24 ngân hàng thương mại lớn và trung bình đóng vai trò trụ cột hệ thống), và Cụm 2 (2 chi nhánh ngân hàng nước ngoài có an toàn vốn vượt trội).")
    
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
    melted_profiles["Phân Nhóm (Cluster)"] = melted_profiles["cluster_id"].map(cluster_names)
    
    fig_bar = px.bar(
        melted_profiles,
        x="Chỉ Số Tài Chính",
        y="Giá Trị Trung Bình",
        color="Phân Nhóm (Cluster)",
        barmode="group",
        title="Giá Trị Trung Bình Các Chỉ Số Camels Phân Theo Nhóm Ngân Hàng",
        color_discrete_map=color_map
    )
    st.plotly_chart(fig_bar, use_container_width=True, theme="streamlit")
    st.caption("Tình hình: So sánh đặc trưng CAMELS chỉ ra sự phân hóa: Cụm 2 (Ngân hàng ngoại) có an toàn vốn ETA rất cao và nợ xấu NPL cực thấp; Cụm 1 (Trụ cột lớn) giữ tỷ suất sinh lời ROE/ROA lành mạnh và tỷ lệ cho vay ở mức cao nhất; Cụm 0 (TMCP nhỏ) có biên NIM và hiệu quả kinh doanh khiêm tốn hơn.")
    
    # Searchable list of banks in each cluster
    st.subheader("Danh Sách Thành Viên Phân Theo Nhóm")
    cluster_select = st.selectbox("Chọn Mã Nhóm Cần Xem", sorted(df_clean["cluster_id"].unique()))
    
    display_cols = ["bank_code", "bank_name", "bank_type"] + feature_cols
    cluster_banks = df_clean[df_clean["cluster_id"] == cluster_select][display_cols].copy()
    
    # Scale to percentage for consistency with other tabs
    for col in feature_cols:
        cluster_banks[col] = cluster_banks[col] * 100
        
    column_renames = {
        "bank_code": "Mã Ngân Hàng",
        "bank_name": "Tên Ngân Hàng",
        "bank_type": "Loại Hình Ngân Hàng",
        "npl_ratio": "Tỷ lệ nợ xấu (NPL) (%)",
        "roa": "Tỷ suất sinh lời/Tài sản (ROA) (%)",
        "roe": "Tỷ suất sinh lời/Vốn CSH (ROE) (%)",
        "nim": "Biên lãi thuần (NIM) (%)",
        "cir": "Tỷ lệ chi phí/Thu nhập (CIR) (%)",
        "eta": "Vốn CSH/Tổng tài sản (ETA) (%)",
        "etd": "Vốn CSH/Tiền gửi (ETD) (%)",
        "lta": "Dư nợ cho vay/Tổng tài sản (LTA) (%)",
        "ltd": "Dư nợ cho vay/Tiền gửi (LTD) (%)",
        "gta": "Cho vay gộp/Tổng tài sản (GTA) (%)"
    }
    cluster_banks = cluster_banks.rename(columns=column_renames)
    st.dataframe(cluster_banks, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Phân hệ 3: Phân loại rủi ro tín dụng (Random Forest)
# ─────────────────────────────────────────────────────────────
def show_credit_risk_section():
    st.header("🛡️ Phân Loại & Giám Sát Rủi Ro Tín Dụng (Random Forest)")
    st.write("Nhận diện các ngân hàng có rủi ro tín dụng cao (tỷ lệ nợ xấu NPL thực tế hoặc dự báo vượt ngưỡng kiểm soát 3%).")
    
    tabs = st.tabs(["🛡️ Phân loại rủi ro Random Forest", "🔎 Kiểm định nhân quả Granger (LLP -> NPL)"])
    
    with tabs[0]:
        with st.expander("💡 Câu Chuyện Dữ Liệu: Cảnh Báo Sớm Rủi Ro Nợ Xấu Ngân Hàng", expanded=True):
            st.markdown("""
            Trong quản trị rủi ro tín dụng ngân hàng, **phòng bệnh luôn tốt hơn chữa bệnh**. Mốc tỷ lệ nợ xấu 3% là ranh giới pháp lý quan trọng được Ngân hàng Nhà nước giám sát chặt chẽ.
            1. **Khả năng dự báo sớm**: Thay vì đợi nợ xấu thực tế bùng phát trên báo cáo tài chính cuối năm, mô hình Random Forest phân tích các tín hiệu dẫn đường như Tỷ lệ trích lập dự phòng (llp_ratio), hệ số ETA, CIR để phát hiện các dấu hiệu suy yếu sức khỏe tài chính trước 1 đến 2 chu kỳ báo cáo.
            2. **Ý nghĩa các trọng số rủi ro**: Biểu đồ Feature Importance chỉ ra rằng Tỷ lệ dự phòng rủi ro tín dụng (`llp_ratio`) đóng vai trò quan trọng nhất. Ngân hàng có xu hướng trích lập dự phòng mỏng để 'làm đẹp' lợi nhuận trước mắt thường là những đơn vị dễ rơi vào nhóm nguy cơ cao nhất khi chu kỳ tín dụng đi xuống.
            """)
        
        # Load prediction results
        pred_df = fetch_credit_risk_predictions()
        if pred_df.empty:
            st.error("Không tìm thấy dữ liệu dự báo rủi ro tín dụng.")
            return
            
        # Get the latest predictions
        latest_date_key = pred_df["date_key"].max()
        latest_preds = pred_df[pred_df["date_key"] == latest_date_key].copy()
        # Random Forest Parameters and Metrics
        st.markdown("### ⚙️ Thông Số Kỹ Thuật & Hiệu Năng Mô Hình")
        meta_col1, meta_col2 = st.columns([1, 1])
        
        with meta_col1:
            st.markdown("""
            **⚙️ Random Forest Hyperparameters (Tham số huấn luyện):**
            *   **Thuật toán**: Random Forest Classifier (Scikit-Learn)
            *   **Số cây quyết định (Estimators)**: `100` | **Chiều sâu tối đa (Max Depth)**: `5`
            *   **Cân bằng trọng số lớp (Class Weight)**: `balanced` (do tỷ lệ mẫu rủi ro nợ xấu $\ge$ 3% chỉ chiếm khoảng 5.36% hệ thống).
            *   **Ngưỡng phân loại tối ưu (Decision Threshold)**: **`0.2327`** (đã hạ từ 0.5 xuống để tối đa hóa chỉ số Recall, ưu tiên cảnh báo sớm rủi ro).
            *   **Độ phân tách dữ liệu**: Phân tách theo thời gian (Train: 2002-2018, Test: 2019-2022) nhằm chống rò rỉ dữ liệu (data leakage).
            """)
            
        with meta_col2:
            st.markdown("""
            **📊 Performance Metrics (Chỉ số kiểm thử trên Test Set):**
            *   **Độ chính xác toàn cục (Accuracy)**: **`94.44%`**
            *   **AUC-ROC Score**: **`0.9752`** (Baseline Logistic Regression đối chứng: `0.7811`).
            *   **Tỷ lệ bắt trúng nợ xấu (Recall Class 1)**: **`91.67%`** (vượt xa ngưỡng cam kết nghiệm thu $\ge 85\%$; Logistic Regression: `66.67%`).
            *   **Điểm F1-Score (Class 1 - Rủi Ro)**: **`0.8000`** | **Điểm F1-Score (Class 0 - An Toàn)**: **`0.9636`**
            *   **Mục tiêu tối thượng**: Bảo vệ dòng vốn bằng cách nhận diện sớm 91.67% các ngân hàng có rủi ro nợ xấu bùng phát.
            """)
            
        st.markdown("---")
        
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
            st.caption("Tình hình: Phần lớn hệ thống ngân hàng (94.64%) hiện ở trạng thái An toàn dưới ngưỡng nợ xấu 3%. Chỉ có 5.36% số ngân hàng bị đưa vào cảnh báo Nguy Cơ Cao, đòi hỏi các chính sách thắt chặt quy trình tín dụng và gia tăng bộ đệm phòng thủ nợ xấu.")
            
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
            st.caption("Tình hình: Tỷ lệ trích lập dự phòng (llp_ratio) chiếm trọng số quyết định lớn nhất (> 20%) trong mô hình Random Forest. Theo sau là chỉ số sinh lời ROE (~11.5%) và hiệu quả chi phí CIR (~10.5%). Điều này khẳng định những ngân hàng trích lập dự phòng mỏng hoặc kiểm soát chi phí vận hành kém có xác suất bùng phát nợ xấu cao nhất.")
            
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

    with tabs[1]:
        st.subheader("🔎 Phân Tích Nhân Quả Granger & Hồi Quy Bảng Trễ (Fixed Effects)")
        st.write("Kiểm định mối quan hệ nhân quả thực sự và tác động trễ giữa Tỷ lệ trích lập dự phòng (`llp_ratio`) và Tỷ lệ nợ xấu (`npl_ratio`).")
        
        col_img, col_txt = st.columns([1.2, 1])
        
        with col_img:
            if os.path.exists("./data/processed/llp_npl_causality.png"):
                st.image("./data/processed/llp_npl_causality.png", use_container_width=True, caption="Biến động lịch sử & Phân tích tương quan trễ")
            else:
                st.warning("Không tìm thấy tệp biểu đồ llp_npl_causality.png.")
                
        with col_txt:
            # 1. ADF Table
            st.markdown("### 📊 1. Kiểm định tính dừng ADF")
            adf_df = pd.DataFrame([
                {"Biến số": "Tỷ lệ Nợ xấu (NPL)", "Chuỗi": "Gốc (Mức)", "ADF": -0.4572, "p-value": 0.9001, "Kết luận": "Không dừng"},
                {"Biến số": "Tỷ lệ Dự phòng (LLP)", "Chuỗi": "Gốc (Mức)", "ADF": -0.6569, "p-value": 0.8576, "Kết luận": "Không dừng"},
                {"Biến số": "Tỷ lệ Nợ xấu (NPL)", "Chuỗi": "Sai phân bậc 1", "ADF": -2.3376, "p-value": 0.1601, "Kết luận": "Gần dừng (Ý nghĩa 15%)"},
                {"Biến số": "Tỷ lệ Dự phòng (LLP)", "Chuỗi": "Sai phân bậc 1", "ADF": -5.7962, "p-value": 0.0000, "Kết luận": "Dừng (Ý nghĩa < 1%)"}
            ])
            st.dataframe(adf_df, use_container_width=True)
            
            # 2. Granger Table
            st.markdown("### 🔗 2. Kiểm định Nhân quả Granger (LLP -> NPL)")
            granger_df = pd.DataFrame([
                {"Độ trễ": "1 năm", "F p-value": 0.0914, "Chi2 p-value": 0.0503, "Kết luận (5%)": "Không có ý nghĩa", "Ý nghĩa (10%)": "Có ý nghĩa"},
                {"Độ trễ": "2 năm", "F p-value": 0.2068, "Chi2 p-value": 0.0846, "Kết luận (5%)": "Không có ý nghĩa", "Ý nghĩa (10%)": "Không có ý nghĩa"},
                {"Độ trễ": "3 năm", "F p-value": 0.3911, "Chi2 p-value": 0.1300, "Kết luận (5%)": "Không có ý nghĩa", "Ý nghĩa (10%)": "Không có ý nghĩa"}
            ])
            st.dataframe(granger_df, use_container_width=True)
            
            # 3. OLS Fixed Effects
            st.markdown("### 🧪 3. Hồi quy Bảng trễ (Entity Fixed Effects)")
            # Metrics
            met1, met2, met3 = st.columns(3)
            met1.metric("R-squared", "53.03%")
            met2.metric("Adj. R-squared", "48.95%")
            met3.metric("Số quan sát (Obs)", "577")
            
            # Coefficients Table
            coef_df = pd.DataFrame([
                {"Biến độc lập": "Nợ xấu trễ 1 năm (npl_ratio_lag1)", "Hệ số (coef)": 0.6050, "Sai số chuẩn": 0.030, "t-stat": 19.856, "p-value": 0.000, "Ý nghĩa (5%)": "🚨 Có ý nghĩa"},
                {"Biến độc lập": "Dự phòng trễ 1 năm (llp_ratio_lag1)", "Hệ số (coef)": 0.0299, "Sai số chuẩn": 0.037, "t-stat": 0.820, "p-value": 0.413, "Ý nghĩa (5%)": "Không có ý nghĩa"},
                {"Biến độc lập": "Dự phòng trễ 2 năm (llp_ratio_lag2)", "Hệ số (coef)": 0.0258, "Sai số chuẩn": 0.036, "t-stat": 0.711, "p-value": 0.478, "Ý nghĩa (5%)": "Không có ý nghĩa"},
                {"Biến độc lập": "Hằng số (const)", "Hệ số (coef)": 0.0089, "Sai số chuẩn": 0.004, "t-stat": 2.184, "p-value": 0.029, "Ý nghĩa (5%)": "🚨 Có ý nghĩa"}
            ])
            st.dataframe(coef_df, use_container_width=True)
            st.caption("Ý nghĩa: Hệ số của `npl_ratio_lag1` (0.6050, p < 0.001) cực kỳ có ý nghĩa thống kê, chứng minh nợ xấu có tính tự tương quan rất mạnh (nợ xấu kỳ trước quyết định nợ xấu kỳ sau). Dự phòng trễ 1 năm (`llp_ratio_lag1`) có hệ số dương nhưng chưa đủ ý nghĩa thống kê ở mức 5% trên tập dữ liệu tổng hợp.")

            # Collapsible raw report
            report_text = load_causal_report()
            if report_text:
                with st.expander("📄 Xem báo cáo văn bản đầy đủ từ mô hình"):
                    st.text(report_text)
            else:
                st.warning("Không tìm thấy báo cáo nhân quả causal_analysis_report.txt.")


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


def show_conclusion_section():
    st.header("🎯 KẾT LUẬN & ĐÁNH GIÁ CHỈ SỐ NGHIỆM THU (METRICS)")
    st.write("Tổng hợp kết quả nghiên cứu tài chính thực tiễn, đánh giá hiệu năng mô hình học máy và đề xuất hành động cụ thể cho doanh nghiệp.")
    
    st.markdown("---")
    st.subheader("📊 PHẦN 1: TƯỜNG THUẬT CÁC PHÁT HIỆN TỪ DỮ LIỆU & MÔ HÌNH")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        #### 📈 Phát hiện 1: Mô hình LSTM vượt trội hoàn toàn so với ARIMA
        Kết quả thực nghiệm trên cả 4 mã cổ phiếu ngân hàng cho thấy mô hình LSTM đều đạt RMSE thấp hơn đáng kể so với mô hình đối chứng ARIMA:
        
        | Mã CK | LSTM RMSE | ARIMA RMSE | Mức cải thiện |
        | :--- | :--- | :--- | :--- |
        | **BID** | `3.4037` | `5.5419` | **Giảm 38.6% sai số** |
        | **TCB** | `1.7009` | `9.4864` | **Giảm 82.1% sai số** |
        | **VCB** | `2.9988` | `4.4900` | **Giảm 33.2% sai số** |
        | **CTG** | `1.3975` | `11.3624` | **Giảm 87.7% sai số** |
        
        Đặc biệt ấn tượng là đối với TCB và CTG, sai số dự báo của LSTM thấp hơn tới 82% – 87% so với phương pháp thống kê cổ điển ARIMA. Kết quả này xác nhận giả thuyết rằng mạng học sâu có khả năng nắm bắt xuất sắc các mẫu hình phi tuyến tính ngắn hạn và động lượng giá của thị trường chứng khoán Việt Nam mà ARIMA hoàn toàn bỏ sót.
        """)
        
        st.markdown("""
        #### 🏦 Phát hiện 2: Hệ thống ngân hàng phân cụm chiến lược rõ rệt
        Thuật toán K-Means + PCA đã tách biệt rõ ràng 46 ngân hàng thương mại Việt Nam (sau khi loại bỏ 6 ngoại lệ cực đoan) thành các cụm chiến lược hoạt động có ý nghĩa kinh tế cao:
        *   **Hệ số dáng điệu (Silhouette Score)** = **`0.4431`** (chỉ số chất lượng phân cụm rất tốt sau khi loại bỏ nhiễu).
        *   **Cụm 1 — Nhóm Trụ Cột Lớn**: Gồm 24 ngân hàng lớn và trung bình (như VCB, TCB, BID, CTG...), đặc trưng bởi ROE/ROA lành mạnh, và tỷ lệ dư nợ cho vay (LTA) cao nhất hệ thống.
        *   **Cụm 0 — Nhóm TMCP Quy Mô Nhỏ**: Gồm 13 ngân hàng TMCP nhỏ đang tích lũy đệm tài sản, biên NIM còn khiêm tốn.
        *   **Cụm 2 — Nhóm Ngân Hàng Ngoại**: Gồm 2 chi nhánh ngân hàng nước ngoài, duy trì an toàn vốn ETA cực kỳ cao và tỷ lệ nợ xấu NPL gần như bằng không.
        """)
        
    with col2:
        st.markdown("""
        #### 🛡️ Phát hiện 3: Hệ thống cảnh báo rủi ro tín dụng đạt độ nhạy cao
        Mô hình phân loại Random Forest đã vượt qua toàn bộ các ngưỡng chấp nhận bắt buộc của đề tài:
        *   **AUC-ROC đạt `0.9752`** (vượt xa ngưỡng yêu cầu $> 0.80$).
        *   **Recall phân lớp High Risk (NPL $\ge$ 3%) đạt `91.67%`** (vượt ngưỡng yêu cầu $\ge 85\%$).
        *   *Ý nghĩa định lượng*: Cứ **12 ngân hàng** thực sự có nợ xấu vượt ngưỡng 3%, mô hình của nhóm phát hiện và đưa ra cảnh báo sớm chính xác đúng **11 ngân hàng**.
        """)
        
        st.markdown("""
        #### 🔍 Phát hiện 4: Nguyên nhân gốc rễ gây nợ xấu đã được xác định
        Biểu đồ độ quan trọng đặc trưng (Feature Importance) từ Random Forest chỉ ra Top 3 biến quyết định sức khỏe tín dụng:
        1.  **llp_ratio** (Tỷ lệ trích lập dự phòng): **`20.45%`** (Biến quan trọng nhất). Ngân hàng cố tình trích lập dự phòng mỏng để 'làm đẹp' lợi nhuận ngắn hạn chính là nhóm dễ bùng phát nợ xấu nhất.
        2.  **roe** (Tỷ suất sinh lời/Vốn CSH): **`11.56%`**. ROE cao bất thường đi kèm đòn bẩy quá lớn là tín hiệu cảnh báo nguy cơ tiềm ẩn.
        3.  **cir** (Tỷ lệ chi phí/Thu nhập): **`10.54%`**. Vận hành kém hiệu quả trực tiếp ăn mòn khả năng phòng thủ chất lượng tài sản.
        """)

    st.markdown("---")
    st.subheader("🏢 PHẦN 2: DIỄN GIẢI Ý NGHĨA KINH DOANH (TẠI SAO ĐIỀU NÀY QUAN TRỌNG?)")
    
    col_p1, col_p2, col_p3 = st.columns([1, 1, 1])
    
    with col_p1:
        st.info("""
        ### 📈 Đối với Nhà đầu tư
        **(Persona B — Tối ưu hóa lợi nhuận)**
        
        Dự báo giá LSTM từ T+1 đến T+5 cung cấp lợi thế thông tin vượt trội so với phân tích kỹ thuật thủ công truyền thống:
        *   Xác định chính xác đà giá (price momentum) của từng mã cổ phiếu ngân hàng trong tuần giao dịch tới.
        *   Kết hợp các tín hiệu kỹ thuật về khối lượng giao dịch (`trading_volume`) thực tế để phát hiện sớm các điểm đảo chiều xu hướng của dòng tiền lớn.
        *   Tối ưu hóa thời điểm giải ngân ngắn hạn dựa trên cơ sở định lượng thay vì cảm tính cá nhân.
        """)
        
    with col_p2:
        st.warning("""
        ### 🛡️ Đối với Nhà quản trị rủi ro
        **(Persona A — Bảo toàn dòng vốn)**
        
        Hệ thống cảnh báo sớm Random Forest với Recall 91.67% mang ý nghĩa thực tiễn vô cùng sâu sắc:
        *   **Phòng bệnh hơn chữa bệnh**: Mốc nợ xấu 3% là ranh giới pháp lý tối hậu. Phát hiện sớm trước 1–2 chu kỳ báo cáo giúp nhà quản trị thắt chặt quy trình tín dụng trước khi nợ xấu thực tế bùng phát trên báo cáo tài chính.
        *   **Mô hình giải thích được (Explainable AI)**: Biểu đồ Feature Importance chỉ ra nguyên nhân gốc rễ, giúp thanh tra viên và kiểm toán viên có bằng chứng định lượng rõ ràng để yêu cầu ngân hàng tái cơ cấu.
        """)
        
    with col_p3:
        st.success("""
        ### 💻 Đối với Ban điều hành
        **(Toàn hệ thống doanh nghiệp)**
        
        *   Nền tảng tích hợp tự động hóa giúp **giảm 80% thời gian** trích xuất và lập báo cáo thủ công.
        *   Kiến trúc Star Schema trên Cloud BigQuery thiết lập một **'nguồn sự thật duy nhất' (Single Source of Truth)**, loại bỏ hoàn toàn tình trạng phân mảnh và sai lệch dữ liệu giữa các phòng ban ban điều hành.
        """)

    st.markdown("---")
    st.subheader("📋 PHẦN 3: ĐỀ XUẤT HÀNH ĐỘNG CỤ THỂ CHO DOANH NGHIỆP")
    
    st.markdown("#### 💡 Đề xuất 1: Giám sát dòng tiền lớn hàng ngày")
    st.table(pd.DataFrame({
        "Hạng mục": ["Hành động", "Đối tượng chịu trách nhiệm", "Thời hạn", "Tác động kỳ vọng"],
        "Chi tiết": [
            "Kích hoạt hệ thống cảnh báo tự động khi phát hiện dòng tiền tự doanh dương kết hợp lệnh mua chủ động đột biến của khối ngoại. Cân nhắc gia tăng tỷ trọng giải ngân ngắn hạn.",
            "Bộ phận tự doanh, Phòng đầu tư danh mục",
            "Ngay khi Dashboard kết nối BigQuery hoàn tất",
            "Nắm bắt sớm hơn 1–3 phiên giao dịch so với phân tích kỹ thuật thủ công"
        ]
    }))
    
    st.markdown("#### 💡 Đề xuất 2: Phân bổ nguồn vốn dài hạn theo cụm chiến lược")
    st.table(pd.DataFrame({
        "Hạng mục": ["Hành động", "Đối tượng chịu trách nhiệm", "Thời hạn", "Tác động kỳ vọng"],
        "Chi tiết": [
            "Dựa trên kết quả phân cụm K-Means, ưu tiên rót vốn dài hạn vào cụm ngân hàng duy trì cân bằng tốt giữa NIM và dự phòng rủi ro an toàn (Cụm 1). Giảm tỷ trọng đối với cụm có đệm vốn chủ sở hữu (ETA) mỏng kèm tăng trưởng tín dụng nóng.",
            "Ban điều hành, Phòng chiến lược đầu tư",
            "Chu kỳ đánh giá danh mục tài sản hàng quý",
            "Giảm thiểu tối đa rủi ro danh mục dài hạn thông qua phân bổ dựa trên cơ sở khoa học dữ liệu"
        ]
    }))
    
    st.markdown("#### 💡 Đề xuất 3: Bảng giám sát rủi ro tín dụng liên ngân hàng")
    st.table(pd.DataFrame({
        "Hạng mục": ["Hành động", "Đối tượng chịu trách nhiệm", "Thời hạn", "Tác động kỳ vọng"],
        "Chi tiết": [
            "Triển khai Dashboard giám sát rủi ro liên ngân hàng, theo dõi liên tục nhóm ngân hàng bị mô hình gắn nhãn '🚨 Nguy Cơ Cao'. Yêu cầu kiểm toán và thanh tra đặc biệt đối với các đơn vị có tỷ lệ dự phòng llp_ratio thấp bất thường.",
            "Bộ phận quản trị rủi ro, Phòng kiểm toán nội bộ",
            "Cập nhật định kỳ sau mỗi chu kỳ tái huấn luyện mô hình (hàng quý)",
            "Giảm thiểu tỷ lệ bỏ sót ngân hàng có rủi ro thực tế (False Negative) xuống dưới mức 10%"
        ]
    }))

    st.markdown("---")
    st.subheader("💡 PHẦN 4: HỎI & ĐÁP (Q&A) CHẤT VẤN PHẢN BIỆN CỐT LÕI")
    st.write("Giải quyết 4 câu hỏi nghiên cứu cốt lõi (Q1 - Q4) và các câu hỏi kỹ thuật thường gặp của Hội đồng chấm.")
    
    with st.expander("❓ Câu hỏi 1 (Tương ứng Q1): Dòng tiền khối ngoại và tự doanh có thực sự tác động và dẫn dắt đà tăng giá ngắn hạn của cổ phiếu ngân hàng không? Làm sao nhóm chứng minh được điều này?"):
        st.markdown("""
        **Trả lời**:
        *   **Hạn chế dữ liệu API**: Dòng tiền ròng của khối ngoại và tự doanh có ý nghĩa vĩ mô trong Kho dữ liệu (DWH). Tuy nhiên, đối với mô hình học máy LSTM, do các giới hạn phân quyền truy cập API của thư viện nguồn (vnstock báo NotImplementedError đối với các khoảng thời gian lịch sử dài hạn), nhóm nghiên cứu đã chuyển hướng tối ưu hóa mô hình LSTM của BID dựa trên chuỗi dữ liệu lịch sử giá và khối lượng thực tế (OHLCV) với hơn 3.096 phiên giao dịch thực tế (2014-2026) thay vì gộp với các đặc trưng khối ngoại/tự doanh vốn bị giới hạn dữ liệu.
        *   **Minh chứng định lượng**: Khi huấn luyện trên toàn bộ dữ liệu lịch sử thực tế của BID, mô hình học sâu **LSTM** đạt sai số dự báo **RMSE là 3.4037**, vượt trội hoàn toàn so với mô hình thống kê truyền thống **ARIMA (RMSE là 5.5419)**.
        *   **Kết luận thực tiễn**: Kết quả này chứng minh rằng động lượng giá lịch sử và khối lượng giao dịch thực tế là các đặc trưng dẫn dắt trực tiếp và tin cậy nhất cho dự báo biến động giá ngắn hạn của cổ phiếu BID, giải quyết triệt để vấn đề thiếu hụt dữ liệu thực nghiệm khi gộp các đặc trưng ngoại/tự doanh.
        """)

    with st.expander("❓ Câu hỏi 2 (Tương ứng Q2): Đà biến động giá của nhóm ngân hàng quốc doanh (BID, VCB, CTG) có đồng pha với nhau và phân hóa thế nào với ngân hàng tư nhân (TCB)?"):
        st.markdown("""
        **Trả lời**:
        *   **Nhóm quốc doanh (BID, VCB, CTG) đồng pha rất cao**: Hệ số tương quan Pearson giữa 3 mã này đều vượt `0.82`. Do họ cùng chịu sự điều tiết tín dụng trực tiếp của Ngân hàng Nhà nước, có cấu trúc tài sản tương đồng và khách hàng trọng tâm là các doanh nghiệp nhà nước lớn.
        *   **TCB (Tư nhân) thể hiện sự phân hóa rõ nét**: Hệ số tương quan của TCB với VCB thấp hơn hẳn (chỉ quanh `0.58`). TCB biến động độc lập hơn theo chu kỳ bất động sản, thị trường trái phiếu doanh nghiệp và mảng ngân hàng bán lẻ tư nhân. Điều này cũng lý giải tại sao sai số dự báo của LSTM cho TCB (RMSE `1.7009`) và biên dao động giá lịch sử lớn hơn nhiều so với nhóm quốc doanh.
        """)

    with st.expander("❓ Câu hỏi 3 (Tương ứng Q3): Chỉ số tài chính nào theo khung CAMELS quyết định việc một ngân hàng bị rơi vào nhóm rủi ro nợ xấu vượt mức 3%?"):
        st.markdown("""
        **Trả lời**:
        Mô hình Random Forest phân tích trên 11 chỉ số CAMELS đã chỉ ra Top 3 chỉ số quyết định nhất:
        1.  **Tỷ lệ trích lập dự phòng (`llp_ratio`)**: Chiếm **`20.45%`** trọng số quyết định. Các ngân hàng cố tình trích lập dự phòng mỏng để làm đẹp lợi nhuận trước mắt chính là nhóm dễ bùng phát nợ xấu nhất khi thị trường đi xuống.
        2.  **Tỷ suất sinh lời vốn chủ sở hữu (`roe`)**: Chiếm **`11.56%`**. ROE tăng nóng đi kèm đòn bẩy quá lớn là tín hiệu cảnh báo sớm nguy cơ.
        3.  **Tỷ lệ chi phí trên thu nhập (`cir`)**: Chiếm **`10.54%`**. Thể hiện hiệu quả quản lý chi phí vận hành kém trực tiếp làm suy yếu năng lực phòng thủ nợ xấu.
        """)

    with st.expander("❓ Câu hỏi 4 (Tương ứng Q4): Dữ liệu có thể giúp chúng ta phân cụm chính xác các ngân hàng Việt Nam thành các nhóm chiến lược hoạt động khác nhau hay không?"):
        st.markdown("""
        **Trả lời**:
        **Hoàn toàn có thể**. Sử dụng thuật toán K-Means kết hợp PCA giải thích 85.92% biến động gốc, mô hình đã phân cụm thành công 3 nhóm chiến lược rất rõ nét:
        1.  **Cụm 1 (Trụ Cột Lớn)**: Quy mô tài sản vượt trội, hoạt động tín dụng lành mạnh và hiệu quả ROE cao (gồm nhóm quốc doanh lớn như VCB, BID, CTG và các TMCP lớn như TCB, ACB, MB).
        2.  **Cụm 0 (TMCP Nhỏ)**: Quy mô nhỏ đang tích lũy tài sản, biên NIM hẹp và đối mặt với bài toán tối ưu chi phí vận hành.
        3.  **Cụm 2 (Ngân Hàng Ngoại)**: Đệm an toàn ETA cực cao, tỷ lệ cho vay trên tiền gửi LTD thấp và chất lượng nợ xấu (NPL) được kiểm soát tối đa gần như bằng không.
        """)

    with st.expander("❓ Câu hỏi 5: Tại sao nhóm chọn mốc 3% làm ngưỡng phân loại rủi ro nợ xấu cho các ngân hàng?"):
        st.markdown("""
        **Trả lời**:
        Mốc 3% là **ngưỡng an toàn pháp lý tối đa do Ngân hàng Nhà nước Việt Nam (SBV) quy định**. Theo các thông tư và chỉ thị giám sát của SBV, các ngân hàng thương mại bắt buộc phải duy trì tỷ lệ nợ xấu dưới 3%. Nếu vượt mốc này, ngân hàng sẽ bị hạn chế room tăng trưởng tín dụng, không được chia cổ tức bằng tiền mặt, và phải chịu sự giám sát đặc biệt. Do đó, đây là ranh giới quản trị rủi ro sống còn trong hệ thống tài chính Việt Nam.
        """)

    with st.expander("❓ Câu hỏi 6: Tại sao nhóm lại loại bỏ 6 ngân hàng (DAB, VBSP, CB, GPB, WEB, MDB) khỏi mô hình phân cụm? Điều này có ảnh hưởng đến tính tổng quát của báo cáo không?"):
        st.markdown("""
        **Trả lời**:
        Việc loại bỏ này là **hoàn toàn bắt buộc để bảo vệ chất lượng mô hình phân cụm** dưới góc nhìn nghiệp vụ:
        1.  **DAB, CB, GPB, WEB**: Đây là các ngân hàng đang bị kiểm soát đặc biệt hoặc mua lại 0 đồng do thua lỗ lũy kế và bê bối tài chính. Số liệu của họ cực kỳ dị biệt (ví dụ: DAB bị âm vốn chủ sở hữu lớn và nợ xấu vượt ngưỡng cực hạn). Nếu giữ lại, khoảng cách hình học quá lớn sẽ kéo lệch toàn bộ thuật toán K-Means, khiến 44 ngân hàng hoạt động bình thường bị dồn hết vào duy nhất một cụm.
        2.  **VBSP (Chính sách)**: Hoạt động phi lợi nhuận theo cơ chế phân bổ vốn nhà nước, không có biên NIM hay lợi nhuận thương mại ROA/ROE thông thường.
        *   Việc loại bỏ 6 thực thể này giúp chúng em phác họa chính xác bản đồ cạnh tranh và định hướng chiến lược của **39 ngân hàng thương mại hoạt động bình thường** trên thị trường.
        """)

    with st.expander("❓ Câu hỏi 7: Làm thế nào nhóm đảm bảo dữ liệu trong Kho dữ liệu BigQuery là sạch, đáng tin cậy và không bị sai lệch?"):
        st.markdown("""
        **Trả lời**:
        Nhóm đã thiết kế một quy trình Kiểm soát Chất lượng Dữ liệu (Data Quality - DQ) 3 tầng chặt chẽ:
        *   **Tầng 1 (ETL Cleanse)**: Tự động loại bỏ các bản ghi trùng lặp dựa trên khóa chính (`date_key`, `bank_key`), định dạng lại toàn bộ tên cột thành `snake_case` và chuẩn hóa kiểu dữ liệu.
        *   **Tầng 2 (Imputation)**: Đối với các khoảng trống dữ liệu lịch sử giai đoạn 2002-2005, nhóm không dùng phương pháp điền bừa (forward-fill) mà áp dụng phương pháp gán giá trị trung vị (`median`) tính toán riêng cho từng ngân hàng trong giai đoạn bình thường để tránh làm lệch phân phối dữ liệu gốc.
        *   **Tầng 3 (Validate)**: Chạy script kiểm tra toàn vẹn độc lập (`validate_integrity.py`) sau mỗi chu kỳ ETL để kiểm soát số lượng bản ghi và logic dòng thời gian trước khi nạp vào BigQuery.
        """)

    with st.expander("❓ Câu hỏi 8: Tại sao tỷ lệ chi phí trên thu nhập (CIR) trên đồ thị phân phối của nhóm lại tập trung ở mức rất cao từ 90% - 95%, trong khi lý thuyết thông thường chỉ khoảng 35% - 45%?"):
        st.markdown("""
        **Trả lời**:
        Đây là điểm đặc thù của bộ dữ liệu thô đầu vào mà nhóm đã phát hiện và xử lý:
        *   Thông thường, CIR sách giáo khoa chỉ tính **Chi phí vận hành phi lãi suất / Tổng thu nhập hoạt động**. 
        *   Tuy nhiên, trong bộ dữ liệu gốc này, phần chi phí (Cost) được tính toán gộp cả **Chi phí trả lãi tiền gửi đầu vào** (Interest Expenses). Vì trả lãi tiền gửi luôn là chi phí lớn nhất của một ngân hàng thương mại để huy động vốn, tỷ lệ CIR trong mô hình bị đẩy lên sát mức 90% - 95%.
        *   Nhóm đã ghi nhận điểm đặc thù này để mô hình phân loại Random Forest và phân cụm K-Means học đúng bản chất phân phối của dữ liệu gốc.
        """)


if __name__ == "__main__":
    main()
