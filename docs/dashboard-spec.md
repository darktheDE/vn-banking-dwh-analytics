# Dashboard Specification — Looker Studio

## 1. Overview

This document defines the acceptance criteria for the Looker Studio interactive dashboard. It serves as the authoritative implementation contract for the Business Intelligence role (Đỗ Kiến Hưng & Phạm Minh Quân). Every chart, filter, and metric listed here is a verifiable deliverable.

**Data Connection**: Native BigQuery connector. No CSV exports are permitted.

**Primary Audience**: Risk Managers (Persona A) and Financial Analysts and Investors (Persona B), as defined in `docs/prd.md` Section 2.

**Dashboard Structure**: Three dedicated pages, each focused on a specific analytical domain.

---

## 2. Page 1 — Market Movement (Stock Price Forecasting & Similarity)

**Purpose**: Allow users to monitor actual stock price movements, evaluate LSTM model predictions (comparing Univariate vs Multivariate vs ARIMA), and analyze the co-movement and similarity between the 4 focus bank stocks using Dynamic Time Warping (DTW) and rolling correlations.

### 2.1 Required Charts and Components

| Component ID | Chart Type | Data Source | Metrics and Dimensions | Notes |
|-------------|------------|-------------|----------------------|-------|
| MM-01 | Line Chart | `fact_stock_daily_metrics` + prediction table | X-axis: Date. Y-axis: `close_price` (actual, blue) vs. predicted price (orange dashed) | Show actual prices and LSTM predictions for the selected bank |
| MM-02 | Heatmap | DTW correlation report | Pairwise Dynamic Time Warping (DTW) distance matrix between BID, TCB, VCB, CTG | Displays price co-movement and time-shifting similarity |
| MM-03 | Line Chart | DTW correlation report | 60-day rolling correlation between stock pairs over time | Shows how stock correlations evolve |
| MM-04 | Scorecard | `fact_stock_daily_metrics` | Latest `close_price`. Percentage change from previous trading session | Prominent position at top of page |
| MM-05 | Data Table | Prediction table | Date, Predicted T+1 to T+5 prices, Model configurations (Uni vs Multi), baseline ARIMA RMSE | Allows comparison of model metrics |

### 2.2 Filters

| Filter ID | Control Type | Field | Scope |
|-----------|-------------|-------|-------|
| F-MM-01 | Date Range Picker | `dim_date.full_date` | Applies to all components on the page |
| F-MM-02 | Dropdown | `dim_stock.ticker` | Fixed to BID for this page; visible for future extensibility |

### 2.3 Acceptance Criteria

- All charts render without SQL timeout errors.
- The line chart MM-01 displays both actual and predicted price series clearly distinguishable by color and label.
- A non-technical user can change the date range and all charts update accordingly without manual refresh.

---

## 3. Page 2 — Bank Profiling (K-Means Clustering)

**Purpose**: Allow both Persona A and Persona B to understand the behavioral segmentation of the 45 Vietnamese commercial banks based on 20 years of financial performance data.

### 3.1 Required Charts and Components

| Component ID | Chart Type | Data Source | Metrics and Dimensions | Notes |
|-------------|------------|-------------|----------------------|-------|
| BP-01 | Scatter Plot | Clustering output table + `dim_bank` | X-axis: PCA Component 1. Y-axis: PCA Component 2. Color: Cluster ID. Tooltip: Bank Name, Bank Type | This is the primary cluster visualization |
| BP-02 | Radar Chart | `fact_bank_performance` grouped by Cluster | Axes: `roa`, `roe`, `nim`, `cir`, `eta`, `npl_ratio`. Series: One per cluster | Shows the financial profile of each cluster |
| BP-03 | Data Table | `dim_bank` + clustering output | Bank Name, Bank Code, Bank Type, Cluster ID, Avg ROA, Avg ROE, Avg NPL Ratio | Allows sorting and filtering by column |
| BP-04 | Pie Chart | `dim_bank` grouped by `bank_type` within each cluster | Count of SOCB, JSCB, FOCB per cluster | Shows the composition of each cluster |

### 3.2 Filters

| Filter ID | Control Type | Field | Scope |
|-----------|-------------|-------|-------|
| F-BP-01 | Dropdown | `dim_bank.bank_type` | SOCB / JSCB / FOCB — Applies to all components |
| F-BP-02 | Dropdown | Cluster ID | Allows viewing a single cluster in detail |
| F-BP-03 | Date Range (Year) | `dim_date.year` | Allows analyzing a specific year or range |

### 3.3 Acceptance Criteria

- The scatter plot BP-01 clearly shows distinct visual separation between clusters.
- The radar chart BP-02 renders all 6 CAMELS axes correctly with one polygon per cluster.
- The data table BP-03 is sortable by NPL Ratio to quickly identify highest-risk banks.
- Filtering by `bank_type` in F-BP-01 immediately updates all 4 components.

---

## 4. Page 3 — Risk Monitoring (Random Forest Classification & Causal Analysis)

**Purpose**: Provide Risk Managers with an early warning view of banks approaching or exceeding the 3% NPL threshold, based on Random Forest classification outputs, and demonstrate the causal statistical link between Loan Loss Provisions (`llp_ratio`) and NPL (`npl_ratio`) using Granger Causality and Panel Regression.

### 4.1 Required Charts and Components

| Component ID | Chart Type | Data Source | Metrics and Dimensions | Notes |
|-------------|------------|-------------|----------------------|-------|
| RM-01 | Data Table | Classification output + `dim_bank` | Bank Name, Bank Type, Year, `npl_ratio` (actual), Predicted Risk Label (Healthy / High Risk), Prediction Probability | Rows color-coded: red = High Risk, green = Healthy |
| RM-02 | Line Chart | `fact_bank_performance` filtered by High Risk banks | X-axis: Year. Y-axis: `npl_ratio`. Series: One per High-Risk bank | Shows NPL trend for flagged banks over time |
| RM-03 | Bar Chart | Feature importance output | X-axis: Feature Name. Y-axis: Importance Score | Static chart from the Random Forest model output |
| RM-04 | Scorecard (x3) | Classification output table | Total Banks Analyzed: 45 (39 in active clustering). High Risk Banks (Predicted): count. Recall Achieved: value | Top of page KPIs |
| RM-05 | Text / Table | Causal analysis report | Granger Causality p-values (Lag 1 to 3) + Lagged Panel Regression coefficients | Displays statistical evidence of credit risk causality |

### 4.2 Filters

| Filter ID | Control Type | Field | Scope |
|-----------|-------------|-------|-------|
| F-RM-01 | Dropdown | `dim_bank.bank_name` | Applies to RM-01 and RM-02 |
| F-RM-02 | Dropdown | `dim_date.year` | Year of prediction |
| F-RM-03 | Toggle | Predicted Risk Label | Show All / High Risk Only / Healthy Only |

### 4.3 Acceptance Criteria

- The data table RM-01 clearly distinguishes High Risk rows with red color coding.
- A user can filter by a specific bank name and immediately see its risk trend in RM-02.
- The feature importance bar chart RM-03 renders the top 10 features, sorted descending by importance.
- The statistical summary RM-05 displays clear p-values and regression coefficients for the causal link between LLP and NPL.
- All three KPI scorecards RM-04 are always visible at the top of the page regardless of filter state.

---

## 5. General Non-Functional Requirements for the Dashboard

| Requirement | Standard |
|-------------|----------|
| **Load Time** | Each page must render within 10 seconds on a standard HOSE-period dataset. |
| **No Manual Exports** | All data must be served directly from BigQuery. CSV uploads to Looker Studio are prohibited. |
| **Accessibility** | Chart colors must remain distinguishable for color-blind users (use shapes or patterns in addition to color where needed). |
| **Responsiveness** | Dashboard must be usable on both a standard 16:9 desktop screen and a compact 13" laptop screen. |

---

## 6. Streamlit Interactive Analytical Dashboard (Ad-hoc Analysis Add-on)

**Purpose**: Complement the Looker Studio dashboard with dynamic deep-learning price forecasts, DTW co-movement clustering, and statistical Granger Causality validation.

### 6.1 Interactive Components and Tab Layouts

#### 6.1.1 Section: Price Forecasting (LSTM)
*   **Tab 1: LSTM Đơn biến vs Đa biến**: Line charts displaying actual close prices vs. rolling predicted prices (T+1 to T+5) from both LSTM Univariate and LSTM Multivariate models.
*   **Tab 2: DTW & Rolling Correlation**: Displays the Dynamic Time Warping (DTW) distance matrix and Pearson correlation matrix for BID, TCB, VCB, CTG, accompanied by the aligned co-movement plots.
*   **Tab 3: Univariate vs. Multivariate Comparison**: Performance metrics table showing RMSE/MAE for LSTM Univariate vs. LSTM Multivariate against the ARIMA baseline.

#### 6.1.2 Section: Credit Risk Classification (Random Forest)
*   **Tab 1: Random Forest Classifier**: Scorecards of global metrics (Recall >= 85%, AUC-ROC > 0.80), Feature Importance bar chart, and the bank risk monitoring table.
*   **Tab 2: Granger Causality (LLP -> NPL)**: Displays Augmented Dickey-Fuller (ADF) unit root tests, Granger Causality p-values, and Entity Fixed Effects panel regression results with lag 1, showing the causality visualization.

### 6.2 Verification and Performance Standards
*   **Data Integrity**: Must read clean CSV data cached in `data/processed/` and forecast arrays stored in BigQuery.
*   **Load Time**: Streamlit caching (`@st.cache_data`) must keep load times under 3 seconds after the initial query.

