# Project Master Plan

## 1. Project Overview

The **Financial Data Analytics Platform** aims to process, store, and analyze 20 years of banking performance data and stock market price history. The system provides actionable insights through interactive Looker Studio dashboards and predictive Machine Learning models.

## 2. Team Structure and Roles

To maximize efficiency, the project executes under a concurrent, role-based strategy rather than waiting for strict sequential milestones.

### Role 1: Data Engineering

**Focus**: Data Collection, Processing, and Cleaning.
- Set up the Python environment using Pandas and Openpyxl.
- Extract raw data from the 7 provided Excel sources.
- Handle missing values using Forward-fill for stock data and Statistical Imputation for missing 2002-2005 bank data.
- Standardize data formats and normalize numerical features using StandardScaler and MinMaxScaler.

### Role 2: Data Warehousing

**Focus**: Google BigQuery Architecture and Maintenance.
- Design and deploy the Star Schema comprising 5 Dimension Tables and 5 Fact Tables.
- Configure Partitioning by date and Clustering by stock and bank keys to optimize query performance and reduce scanning costs.
- Securely manage Service Account JSON Keys and IAM permissions.

### Role 3: Machine Learning Engineering

**Focus**: Predictive Modeling and Optimization.
- **Time Series**: Train and optimize the LSTM deep learning network for short-term stock price forecasting (BID, TCB, VCB, CTG).
- **Clustering**: Apply PCA and K-Means to segment 45 banks based on CAMELS indicators.
- **Classification**: Train the Random Forest algorithm to classify banks into ‘High Risk’ versus ‘Healthy’ categories.
- Ensure the models meet the defined Acceptance Criteria, specifically achieving a Recall greater than or equal to 85% for risk classification.

### Role 4: Business Intelligence and Analytics

**Focus**: Visualization, Analysis, and Reporting.
- Connect Looker Studio natively to Google BigQuery.
- Design interactive dashboards to display market movements, bank profiles, and risk monitoring matrices.
- Translate Machine Learning outputs into actionable business intelligence for Risk Managers and Financial Analysts.

---

## 3. Concurrent Execution Tracks

The team will progress simultaneously across four parallel tracks.

### Track A: Foundation and Environment Setup

- All members configure their local development environments utilizing Python 3.9+ and virtual environments.
- Establish a secure workflow for sharing Google Cloud credentials using local environment variables, ensuring no keys are exposed to public repositories.
- Finalize the raw data inventory and structural mapping.

### Track B: ETL Pipeline and DWH Construction

- The Data Engineer writes Python scripts to clean and transform the raw Excel files.
- The DWH Engineer sets up the Google BigQuery datasets and provisions the Star Schema tables.
- The ETL pipeline is rigorously tested by loading the initial batch of cleaned data into BigQuery.

### Track C: Model Prototyping and Training

- The ML Engineer pulls cleaned data directly from BigQuery Fact and Dimension tables.
- Baseline models including ARIMA, Moving Average, and Logistic Regression are established.
- Core models including LSTM, K-Means, and Random Forest are trained, validated, and optimized against the baselines.
- Final predictions and clustering assignments are written back to BigQuery Fact tables via Python Batch Jobs.

### Track D: Dashboard Integration and Final Review

- The BI Analyst connects Looker Studio to the populated BigQuery schema using the Native Connector.
- Visualization components are built iteratively as new data and ML predictions become available in the DWH.
- The entire team conducts an end-to-end integration test to ensure 100% data consistency from the raw Excel files down to the Looker Studio visualizations.

---

## 4. System Architecture Summary

The system integrates across 5 distinct layers:
1. **Data Source Layer**: 7 raw structured and semi-structured Excel files.
2. **Data Ingestion Layer**: Python Pandas ETL pipeline executing as Batch Jobs.
3. **Data Storage Layer**: Google BigQuery Star Schema.
4. **Analytics Layer**: Scikit-Learn and TensorFlow ML models executing locally or via serverless containers.
5. **Presentation Layer**: Looker Studio interactive dashboards.

---

## 5. Definition of Done

The project is considered officially complete when:
- The automated ETL pipeline runs without errors and accurately populates BigQuery.
- The Star Schema handles analytical queries efficiently without requiring expensive full-table scans.
- The Random Forest model achieves an AUC-ROC > 0.80 and a Recall >= 85%.
- The Looker Studio dashboard successfully renders clustering results, risk matrices, and LSTM price predictions using a live BigQuery connection.