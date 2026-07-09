#!/bin/bash
set -e

echo "======================================================================="
echo "  Financial Data Analytics Platform - Initialization Setup (Unix/macOS)"
echo "======================================================================="
echo ""

# 1. Activate Virtual Environment
if [ -f "venv/bin/activate" ]; then
    echo "[*] Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "[WARNING] virtual environment (venv) not found. Running with global python."
fi

# 2. Extract Data (Raw stock ohlcv and transposing BCTC sheets)
echo "[*] Step 1: Extracting raw data from VCI and VN banks Excel sheet..."
python -m src.etl.extract_data

# 3. Provision DWH Schema
echo "[*] Step 2: Provisioning BigQuery Data Warehouse schema..."
python -m src.etl.provision_schema

# 4. Populate Dimensions
echo "[*] Step 3: Populating Dimension tables..."
python -m src.etl.populate_dim_date
python -m src.etl.populate_dim_stock
python -m src.etl.populate_dim_bank
python -m src.etl.populate_dim_trading_session

# 5. Transform and Load Fact Tables
echo "[*] Step 4: Transforming stock and bank metrics locally..."
python -m src.etl.consolidate_stock_metrics
python -m src.etl.load_bank_performance

echo "[*] Step 5: Loading data to BigQuery DWH..."
python -m src.etl.load_to_bigquery

# 6. Validate Integrity
echo "[*] Step 6: Validating DWH data integrity and quality rules..."
python -m src.etl.validate_integrity

# 7. Train Models
echo "[*] Step 7: Training Machine Learning models (LSTM, K-Means, Random Forest)..."
python -m src.models.feature_engineering_stock
python -m src.models.feature_engineering_bank
python -m src.models.baseline_arima
python -m src.models.train_lstm
python -m src.models.train_kmeans
python -m src.models.baseline_logistic
python -m src.models.train_random_forest

echo ""
echo "======================================================================="
echo "  [SUCCESS] All pipeline stages initialized and loaded successfully!"
echo "  To run the dashboard, execute: streamlit run src/dashboard/app.py"
echo "======================================================================="
echo ""
