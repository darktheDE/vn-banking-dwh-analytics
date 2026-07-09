@echo off
echo =======================================================================
echo  Financial Data Analytics Platform - Initialization Setup (Windows)
echo =======================================================================
echo.

REM 1. Activate Virtual Environment
if exist venv\Scripts\activate.bat (
    echo [*] Activating Python virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] virtual environment (venv) not found. Running with global python.
)

REM 2. Extract Data (Raw stock ohlcv and transposing BCTC sheets)
echo [*] Step 1: Extracting raw data from VCI and VN banks Excel sheet...
python -m src.etl.extract_data
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Data extraction failed.
    exit /b %ERRORLEVEL%
)

REM 3. Provision DWH Schema
echo [*] Step 2: Provisioning BigQuery Data Warehouse schema...
python -m src.etl.provision_schema
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] DWH Schema provisioning failed.
    exit /b %ERRORLEVEL%
)

REM 4. Populate Dimensions
echo [*] Step 3: Populating Dimension tables...
python -m src.etl.populate_dim_date
python -m src.etl.populate_dim_stock
python -m src.etl.populate_dim_bank
python -m src.etl.populate_dim_trading_session
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dimension population failed.
    exit /b %ERRORLEVEL%
)

REM 5. Transform and Load Fact Tables
echo [*] Step 4: Transforming stock and bank metrics locally...
python -m src.etl.consolidate_stock_metrics
python -m src.etl.load_bank_performance
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Data transformation failed.
    exit /b %ERRORLEVEL%
)

echo [*] Step 5: Loading data to BigQuery DWH...
python -m src.etl.load_to_bigquery
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Loading to BigQuery failed.
    exit /b %ERRORLEVEL%
)

REM 6. Validate Integrity
echo [*] Step 6: Validating DWH data integrity and quality rules...
python -m src.etl.validate_integrity
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Integrity validation failed.
    exit /b %ERRORLEVEL%
)

REM 7. Train Models
echo [*] Step 7: Training Machine Learning models (LSTM, K-Means, Random Forest)...
python -m src.models.feature_engineering_stock
python -m src.models.feature_engineering_bank
python -m src.models.baseline_arima
python -m src.models.train_lstm
python -m src.models.train_kmeans
python -m src.models.baseline_logistic
python -m src.models.train_random_forest
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Model training failed.
    exit /b %ERRORLEVEL%
)

echo.
echo =======================================================================
echo  [SUCCESS] All pipeline stages initialized and loaded successfully!
echo  To run the dashboard, execute: streamlit run src/dashboard/app.py
echo =======================================================================
echo.
pause
