# Machine Learning Specifications (ML_SPEC)

## Overview

This document outlines the technical specifications for the Machine Learning models deployed in the Financial Data Analytics Platform. Based on the finalized architecture, the project utilizes three core models tailored for specific financial analysis tasks: Time Series Forecasting, Clustering, and Classification.

---

## 1. Time Series Forecasting: LSTM (Long Short-Term Memory)

**Objective**: Predict the short-term closing price of BID stock (T+1 to T+5) by analyzing historical prices and trading volumes, factoring in the impact of foreign and proprietary cash flows.

### 1.1 Model Selection Rationale

LSTM, a specialized Recurrent Neural Network (RNN) architecture, is chosen because it excels at capturing long-term dependencies and non-linear patterns in volatile financial time series data, outperforming traditional statistical models like ARIMA when handling complex external regressors (like cash flow signals).

### 1.2 Data Inputs (Features)

- Historical OHLCV (Open, High, Low, Close, Volume) data.
- Foreign trading net volume and value.
- Proprietary trading net volume.
- *Transformation*: Sequence windowing (e.g., rolling windows of the past N days) normalized using `MinMaxScaler`.

### 1.3 Target Variable

- Stock Closing Price (Continuous numerical variable).

### 1.4 Evaluation Metrics

- **RMSE (Root Mean Square Error)**: To penalize larger prediction errors heavily.
- **MAE (Mean Absolute Error)**: To measure the average magnitude of prediction errors.

---

## 2. Clustering & Dimensionality Reduction: K-Means + PCA

**Objective**: Segment 46 Vietnamese commercial banks into distinct groups based on 20 years of financial performance data to identify behavioral patterns, risk profiles, and strategic groups.

### 2.1 Model Selection Rationale

- **PCA (Principal Component Analysis)**: With over 47 financial variables in the raw dataset, PCA is essential to reduce noise, prevent the “curse of dimensionality,” and extract the most significant variance components.
- **K-Means**: A highly efficient partitioning algorithm that cleanly divides data into non-overlapping subgroups, making the financial segmentation highly interpretable for business analysts and stakeholders.

### 2.2 Data Inputs (Features)

- CAMELS framework indicators: ROA, ROE, NIM, CIR, ETA, LTD, etc.
- *Transformation*: Data must be strictly standardized using `StandardScaler` prior to applying PCA to ensure equal weighting of all financial ratios.

### 2.3 Hyperparameter Tuning

- Optimal number of components for PCA determined via Cumulative Explained Variance (targeting >80% explained variance).
- Optimal number of clusters ($k$) for K-Means determined iteratively using the **Elbow Method** and **Silhouette Analysis**.

### 2.4 Evaluation Metrics

- **Silhouette Score**: To measure how similar an object is to its own cluster compared to other clusters (values closer to 1 indicate better clustering).
- **Davies-Bouldin Index**: To evaluate cluster separation and compactness.

---

## 3. Risk Classification: Random Forest

**Objective**: Classify the financial health of banks to provide early warnings for institutions with a high risk of bad debt, specifically identifying if a bank’s Non-Performing Loan (NPL) ratio will exceed the 3% threshold.

### 3.1 Model Selection Rationale

Random Forest, an ensemble learning method based on decision trees, is chosen because it handles tabular financial data exceptionally well, is robust to outliers, does not require extensive feature scaling, and most importantly, provides built-in **Feature Importance** metrics (crucial for financial interpretability and regulatory explanations).

### 3.2 Data Inputs (Features)

- Financial performance ratios (ROE, ROA, CIR, ETA, etc.) excluding the direct NPL ratio target.
- *Transformation*: Label encoding for categorical data if necessary.

### 3.3 Target Variable

- **Binary Classification**:
    - `0` (Healthy): NPL < 3%
    - `1` (High Risk): NPL $\ge$ 3%

### 3.4 Evaluation Metrics

- **AUC-ROC (Area Under the Receiver Operating Characteristic Curve)**: To evaluate the model’s ability to distinguish between classes.
- **F1-Score**: To balance Precision and Recall.
- **Feature Importance**: To interpret and explain which financial indicators drive the credit risk classification.

---

## 4. Baselines & Acceptance Criteria

To ensure the deployed models provide tangible business value, they must outperform simpler baseline models and meet strict performance thresholds before being promoted to Production.

### 4.1 Baseline Models

- **LSTM**: Must outperform the traditional Moving Average (MA) and ARIMA models in terms of RMSE.
- **Random Forest**: Must outperform a standard Logistic Regression baseline to justify its added computational complexity.

### 4.2 Acceptance Thresholds

- **Risk Classification (Random Forest)**: Must achieve an AUC-ROC > 0.80. More importantly, the **Recall for the ‘High Risk’ (1) class must be $\ge$ 85%**. In financial risk management, false negatives (missing a bad debt bank) carry severe consequences compared to false positives (false alarms).
- **Time Series (LSTM)**: MAPE (Mean Absolute Percentage Error) must be consistently lower than the established baseline on the validation set.

---

## 5. Data Pipeline & Financial Edge Cases

### 5.1 Handling Non-Trading Days

- **LSTM Modeling**: Weekends and public holidays lack trading data. The sequence windowing will strictly operate on **Trading Days only**. Forward-fill imputation will only be used for unexpected intraday missing values, avoiding the creation of artificial weekend data points.

### 5.2 Data Freshness

- **Batch Processing**: Data (OHLCV, foreign/proprietary cash flows) will be ingested via an **End-of-Day (EOD) Batch Process**. Real-time streaming is out of scope for this architecture.

---

## 6. MLOps & Retraining Strategy

Financial markets experience continuous Concept Drift. Models must be periodically retrained to remain accurate.

### 6.1 Retraining Schedule

- **LSTM (Stock Prices)**: Retrained **weekly** (every weekend) incorporating the latest trading week’s data to adjust to short-term market volatility.
- **Random Forest & K-Means (Bank Health)**: Retrained **quarterly**, aligning with the official release cycle of bank financial statements and macroeconomic indicators.

### 6.2 Model Serving

- Predictions will be generated via **Batch Jobs** immediately after the retraining or daily data ingestion cycle. Results will be saved directly to Google BigQuery Fact tables, serving the Looker Studio dashboard efficiently without requiring low-latency REST API endpoints.

---

## 7. Fallback & Risk Management

### 7.1 Black Swan Events

Extreme market volatility (e.g., macroeconomic shocks, global pandemics) can cause severe prediction deviations in time series models.
- **Confidence Scoring**: The system will monitor prediction variance. If prediction confidence drops below a set threshold, the Looker dashboard will display a “High Volatility Warning” and advise users to rely on qualitative analysis rather than strictly on model outputs.

### 7.2 Missing Features in Production

If external data sources (e.g., foreign cash flow API) fail to deliver data for a specific day:
- **Fallback Imputation**: The ETL pipeline will default to using the previous day’s value (Forward-fill) or a rolling 5-day moving average to prevent the pipeline and subsequent LSTM predictions from crashing.