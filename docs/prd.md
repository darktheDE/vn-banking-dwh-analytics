# Product Requirements Document

## 1. Product Overview

**Product Name**: Financial Data Analytics Platform
**Team**: Group 2 with 4 Members
**Status**: Final Draft

### 1.1 Objective

To develop an end-to-end, automated data pipeline and analytics platform that standardizes fragmented Vietnamese financial data. The platform leverages Google BigQuery for robust centralized storage and Machine Learning algorithms to provide predictive insights regarding short-term stock price trends and long-term bank credit risks.

### 1.2 Problem Statement

Financial analysts and risk managers currently lack a centralized system to cross-analyze micro-level stock movements and macro-level bank health over a 20-year period. Manual aggregation of unstructured Excel and Word files is highly inefficient and prone to errors. Consequently, decisions regarding short-term investments and long-term risk management heavily rely on intuition rather than quantitative, data-driven metrics.

---

## 2. Target Audience and User Personas

1. **Risk Manager Persona A**: Monitors systemic risks within the banking sector. Needs early warning indicators and classification models for banks likely to exceed a 3% Non-Performing Loan ratio.
2. **Financial Analyst and Investor Persona B**: Looks for short-term trading signals for specific stocks like BID based on the historical impact of proprietary trading and foreign cash flow data.
3. **Data Engineer and Data Scientist Persona C**: Requires a clean, scalable Data Warehouse as a “single source of truth” for executing ad-hoc queries and deploying future analytics models.

---

## 3. Scope

### 3.1 In Scope

- Development of an automated ETL pipeline using Python Pandas to process existing historical raw datasets.
- Design and deployment of a Star Schema Data Warehouse on Google BigQuery.
- Development and optimization of three core ML models: LSTM for Time Series Forecasting, K-Means with PCA for Clustering, and Random Forest for Risk Classification.
- Creation of an interactive visualization dashboard via Looker Studio directly connected to BigQuery.

### 3.2 Out of Scope

- Real-time or milli-second automated algorithmic trading execution systems.
- Natural Language Processing for sentiment analysis from financial news or social media.
- Expansion to all stock tickers across the VN-Index. Focus is strictly limited to selected banking assets: BID, TCB, VCB, CTG, and the 46 commercial banks.


---

## 4. Functional Requirements

### FR1: Data Extraction and Transformation

- **FR1.1**: The system must successfully extract data from the 7 provided Excel files containing stock history, intraday ticks, and 20-year bank performance.
- **FR1.2**: The system must handle missing values in the 2002-2022 bank dataset using statistically appropriate imputation techniques.
- **FR1.3**: The system must standardize currency formats, date-time fields, and normalize numerical variables using StandardScaler before loading them into the DWH.

### FR2: Data Warehousing

- **FR2.1**: The system must store data in a centralized Star Schema architecture on Google BigQuery.
- **FR2.2**: The schema must include 5 Dimension tables: `dim_date`, `dim_stock`, `dim_bank`, `dim_trading_session`, and `dim_audit`.
- **FR2.3**: The schema must include 5 Fact tables: `fact_foreign_trading`, `fact_proprietary_trading`, `fact_price_history`, `fact_order_stats`, and `fact_bank_performance`.
- **FR2.4**: The schema must support 3 Machine Learning output tables for model predictions: `bank_cluster_assignments`, `bank_risk_predictions`, and `fact_model_predictions`.

### FR3: Machine Learning Analytics

- **FR3.1**: The system must predict the short-term from T+1 to T+5 closing price of the BID stock using an LSTM deep learning network.
- **FR3.2**: The system must segment the 46 banks into distinct financial behavior clusters using K-Means clustering combined with PCA for dimensionality reduction.
- **FR3.3**: The system must classify banks into ‘Healthy’ or ‘High Risk’ with NPL greater than or equal to 3% categories using a Random Forest algorithm based on CAMELS indicators.

### FR4: Visualization and Reporting

- **FR4.1**: The Looker Studio dashboard must connect directly to BigQuery via the native Google Cloud connector without manual CSV exports.
- **FR4.2**: The dashboard must display clustering results clearly using scatter plots or radar charts.
- **FR4.3**: The dashboard must visualize historical actual prices versus predicted stock prices from LSTM output using line charts.
- **FR4.4**: The dashboard must present a clear risk classification matrix and table for all analyzed banks.

---

## 5. Non-Functional Requirements

### NFR1: Accuracy and Performance

- **Forecasting Model**: The LSTM model should minimize Mean Absolute Error and Root Mean Square Error against the test dataset. LSTM must outperform the ARIMA baseline model in RMSE. Note: ARIMA is used **as a comparison baseline only** and is not deployed in production.
- **Classification Model**: The Random Forest model must achieve AUC-ROC > 0.80 and a high F1-Score. Critically, the **Recall for the 'High Risk' (NPL ≥ 3%) class must be ≥ 85%**. In financial risk management, false negatives (failing to identify a high-risk bank) carry severe consequences and must be minimized above all other metrics.
- **Clustering**: K-Means clustering must yield a Silhouette Score indicating distinct, well-separated clusters and a low Davies-Bouldin Index.

### NFR2: Usability

- The Looker Studio dashboard must be highly intuitive, allowing non-technical users like Persona A and Persona B to interactively filter data by Date, Bank Name, or Stock Ticker without writing SQL queries.

### NFR3: Efficiency

- The automated ETL Python pipeline must reduce manual data preparation and aggregation time by at least 80% compared to previous ad-hoc spreadsheet methods.

---

## 6. Data Requirements

| Data Entity | Source Format | Key Variables and Fields | Volume Constraints |
| --- | --- | --- | --- |
| **Foreign and Prop Trading BID** | Excel | Date, Net Volume, Value | 22 Trading Sessions |
| **Price History and Order Stats BID** | Excel | OHLCV, Buy and Sell Orders, Matched Vol | 22 Trading Sessions |
| **Bank Financials for 46 Banks** | Excel | ROA, ROE, NPL, ETA, NIM, CIR | 20 Years from 2002 to 2022 |

---

## 7. Assumptions and Dependencies

- **Data Completeness**: It is assumed that the provided 20-year bank dataset contains sufficient correlated variables to predict bad debts accurately without requiring external macroeconomic data such as GDP and inflation.
- **Cloud Infrastructure**: Requires stable access to the Google Cloud Platform BigQuery API and properly configured IAM permissions via JSON Service Accounts.
- **Integration**: Assumes Looker Studio can seamlessly handle the visualization of the defined BigQuery views without query timeout issues.