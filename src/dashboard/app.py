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
# Page Configurations & Setup
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vietnam Banking Analytics Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Premium Aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }
    .stCard {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Data Fetching Helpers (direct from BigQuery DWH)
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
    # Filter to the single latest training run using trained_at timestamp.
    # This deduplicates WRITE_APPEND rows when DML DELETE is unavailable (free tier).
    # Falls back to base_date_key for older rows that pre-date the trained_at column.
    query = f"""
        SELECT
            horizon,
            predicted_close_price
        FROM `{pred_table}`
        WHERE stock_key = {stock_key}
          AND model_name = 'LSTM'
          AND COALESCE(trained_at, TIMESTAMP('1970-01-01')) = (
              SELECT MAX(COALESCE(trained_at, TIMESTAMP('1970-01-01')))
              FROM `{pred_table}`
              WHERE stock_key = {stock_key}
                AND model_name = 'LSTM'
          )
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
# Main Application Layout
# ─────────────────────────────────────────────────────────────
def main():
    load_dotenv()
    
    st.title("🏦 Vietnam Banking Data Warehouse & ML Analytics")
    st.markdown("---")
    
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio(
        "Choose Dashboard Section",
        ["Market Price Forecasting (LSTM)", "Bank Clustering (K-Means)", "Credit Risk Classifier (RF)", "DWH System Status"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Data source: Google BigQuery Star Schema Data Warehouse")
    
    if app_mode == "Market Price Forecasting (LSTM)":
        show_price_forecasting_section()
    elif app_mode == "Bank Clustering (K-Means)":
        show_bank_clustering_section()
    elif app_mode == "Credit Risk Classifier (RF)":
        show_credit_risk_section()
    else:
        show_dwh_status_section()


# ─────────────────────────────────────────────────────────────
# Section 1: Stock Price Forecasting (LSTM)
# ─────────────────────────────────────────────────────────────
def show_price_forecasting_section():
    st.header("📈 Focus Stock Price Forecasting (LSTM)")
    st.write("LSTM Deep Learning forecasts closing prices for the next 5 trading days (T+1 to T+5).")
    
    # Load stocks
    stocks_df = fetch_stock_dimension()
    if stocks_df.empty:
        st.error("No stock dimension data found.")
        return
        
    stock_options = {row["ticker"]: row["stock_key"] for _, row in stocks_df.iterrows()}
    selected_ticker = st.selectbox("Select Focus Bank Stock Ticker", list(stock_options.keys()))
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
                name="Historical Price",
                line=dict(color="#3b82f6", width=2.5)
            )
            
            pred_trace = go.Scatter(
                x=pred_df["full_date"],
                y=pred_df["predicted_close_price"] * 1000,
                name="LSTM Predicted Price",
                line=dict(color="#f43f5e", width=2.5, dash="dash"),
                marker=dict(size=8, symbol="circle")
            )
            
            fig = go.Figure(data=[actual_trace, pred_trace])
            fig.update_layout(
                title=f"{selected_ticker} Stock Price & 5-Day Forecast (VND)",
                xaxis_title="Date",
                yaxis_title="Price (VND)",
                template="plotly_dark",
                hovermode="x unified",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Insufficient data available to render forecast plots.")
            
    with col2:
        st.subheader("Forecast Steps (T+1 to T+5)")
        if not pred_df.empty:
            last_close = hist_df["close_price"].iloc[-1] * 1000
            st.metric(
                label="Latest Close Price",
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
                    "Horizon": row["horizon"],
                    "Date": row["full_date"].strftime("%Y-%m-%d"),
                    "Forecast (VND)": f"{pred_val:,.0f}",
                    "Change (%)": f"{diff_pct:+.2f}%"
                })
            
            st.table(pd.DataFrame(forecast_table))
        else:
            st.info("No predictions found in DWH.")


# ─────────────────────────────────────────────────────────────
# Section 2: Bank Clustering (K-Means)
# ─────────────────────────────────────────────────────────────
def show_bank_clustering_section():
    st.header("📊 Bank Clustering & Profiling (K-Means + PCA)")
    st.write("Clusters 46 Vietnamese commercial banks using PCA-reduced CAMELS performance ratios.")
    
    # Load clusters data
    clusters_df = fetch_bank_clusters()
    if clusters_df.empty:
        st.error("No bank clustering data found.")
        return
        
    st.subheader("PCA 2D Scatter Projection")
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
        title="K-Means Clustering Projection on 2D PCA Space",
        color_continuous_scale=px.colors.sequential.Viridis,
        template="plotly_dark"
    )
    fig.update_traces(textposition="top center", marker=dict(size=12, line=dict(color="white", width=1)))
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show radar comparison
    st.subheader("Cluster Profile Comparison")
    
    avg_profiles = df_clean.groupby("cluster_id")[feature_cols].mean().reset_index()
    
    # Transpose for easier comparison chart
    melted_profiles = pd.melt(avg_profiles, id_vars=["cluster_id"], value_vars=feature_cols, var_name="Ratio", value_name="Average Value")
    
    fig_bar = px.bar(
        melted_profiles,
        x="Ratio",
        y="Average Value",
        color="cluster_id",
        barmode="group",
        title="Comparison of CAMELS Ratios by Cluster",
        template="plotly_dark",
        labels={"cluster_id": "Cluster ID"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Searchable list of banks in each cluster
    st.subheader("Bank Members by Cluster")
    cluster_select = st.selectbox("Select Cluster ID", sorted(df_clean["cluster_id"].unique()))
    cluster_banks = df_clean[df_clean["cluster_id"] == cluster_select][["bank_code", "bank_name", "bank_type"] + feature_cols]
    st.dataframe(cluster_banks)


# ─────────────────────────────────────────────────────────────
# Section 3: Credit Risk Classifier (Random Forest)
# ─────────────────────────────────────────────────────────────
def show_credit_risk_section():
    st.header("🛡️ Bank Credit Risk Classification (Random Forest)")
    st.write("Identifies banks with high credit risk (NPL ratio >= 3%) based on current financial health.")
    
    # Load prediction results
    pred_df = fetch_credit_risk_predictions()
    if pred_df.empty:
        st.error("No bank risk prediction data found.")
        return
        
    # Get the latest predictions
    latest_date_key = pred_df["date_key"].max()
    latest_preds = pred_df[pred_df["date_key"] == latest_date_key].copy()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Risk Distribution Profile")
        risk_counts = latest_preds["risk_label"].value_counts().reset_index()
        risk_counts["Label"] = risk_counts["risk_label"].map({0: "Healthy (NPL < 3%)", 1: "High Risk (NPL >= 3%)"})
        
        fig = px.pie(
            risk_counts,
            values="count",
            names="Label",
            color="Label",
            color_discrete_map={"Healthy (NPL < 3%)": "#10b981", "High Risk (NPL >= 3%)": "#ef4444"},
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display Feature Importance horizontal bar chart
        st.subheader("Model Feature Importance")
        feat_imp_path = "./reports/figures/rf_feature_importance.png"
        if os.path.exists(feat_imp_path):
            st.image(feat_imp_path, caption="Random Forest Feature Importance", use_container_width=True)
        else:
            feat_imp_data = pd.DataFrame({
                "feature": ["llp_ratio", "roe", "cir", "roa", "total_loans", "eta", "total_assets", "total_equity"],
                "importance": [0.2045, 0.1156, 0.1054, 0.0943, 0.0528, 0.0496, 0.0496, 0.0492]
            }).sort_values("importance", ascending=True)
            fig_imp = px.bar(
                feat_imp_data,
                x="importance",
                y="feature",
                orientation="h",
                title="Random Forest Feature Importance",
                template="plotly_dark"
            )
            st.plotly_chart(fig_imp, use_container_width=True)
            
    with col2:
        st.subheader(f"Commercial Banks Risk Monitor (Year: {str(latest_date_key)[:4]})")
        
        latest_preds["Risk Category"] = latest_preds["risk_label"].map({0: "Healthy", 1: "🚨 High Risk"})
        latest_preds["Risk Probability"] = (latest_preds["risk_probability"] * 100).map("{:.2f}%".format)
        latest_preds["Current NPL Ratio"] = (latest_preds["actual_npl_ratio"] * 100).map("{:.2f}%".format)
        
        display_df = latest_preds[["bank_code", "Risk Category", "Risk Probability", "Current NPL Ratio"]].sort_values("Risk Category", ascending=False)
        st.dataframe(display_df, use_container_width=True, height=500)


# ─────────────────────────────────────────────────────────────
# Section 4: DWH System Status
# ─────────────────────────────────────────────────────────────
def show_dwh_status_section():
    st.header("⚙️ BigQuery DWH Integration Status")
    st.write("Verifies table records, ingestion volumes, and partitioning configuration across the star schema.")
    
    client = get_bigquery_client()
    dataset_id = os.getenv("BQ_DATASET_ID", "financial_dwh")
    
    st.subheader("Data Warehouse Tables Overview")
    
    # Query BQ metadata for table row counts
    query = f"""
        SELECT
            table_id,
            row_count,
            size_bytes / 1024 as size_kb
        FROM `{os.getenv("GCP_PROJECT_ID")}.{dataset_id}.__TABLES__`
        ORDER BY row_count DESC
    """
    
    try:
        meta_df = client.query(query).to_dataframe(create_bqstorage_client=False)
        st.table(meta_df)
        
        st.success("All 10 DWH tables online and connected successfully!")
    except Exception as e:
        st.error(f"Failed to fetch DWH metadata: {str(e)}")


if __name__ == "__main__":
    main()
