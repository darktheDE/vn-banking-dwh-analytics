# Machine Learning Models Implementation Plan

The objective of this plan is to design and implement all preprocessing and Machine Learning model training scripts in the `src/models/` directory, strictly adhering to the specifications from `docs/ml-spec.md` and `docs/tasks.md` (Track C).

## ⚠️ User Review Required

- **Verify BigQuery Connection**: The ML scripts require querying data from BigQuery and writing prediction results back to BigQuery. You must ensure `.env` and `GOOGLE_APPLICATION_CREDENTIALS` are configured before running.
- **Acceptance Criteria**: The models (like Random Forest) have extremely strict thresholds (Recall for high-risk class >= 85%). If the baseline training doesn't meet this, we will need to add techniques to handle class imbalance (such as SMOTE or Class Weights). Do you agree to apply Class Weights if necessary?

## Proposed Changes

We will build and finalize 7 Python scripts in the `src/models/` directory.

---

### 1. Feature Engineering (Extraction and Standardization)

#### [MODIFY] `feature_engineering_stock.py`
- **Goal**: Extract data from fact tables (`fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading`) for BID stock.
- **Key Features**: Connect to BigQuery, query, merge data based on `date_key`, and ensure only valid trading days are fetched.
- **Output**: A features DataFrame for the stock.

#### [MODIFY] `feature_engineering_bank.py`
- **Goal**: Extract bank performance data from `fact_bank_performance`.
- **Key Features**: Scale all CAMELS ratios using `StandardScaler` (mandatory requirement before running PCA and K-Means).
- **Output**: A scaled features DataFrame for banks.

---

### 2. Time Series Forecasting (BID stock price prediction using LSTM)

#### [MODIFY] `baseline_arima.py`
- **Goal**: Build a Baseline model (ARIMA / Moving Average) for comparison.
- **Key Features**: Calculate RMSE and MAE.
- **Constraint**: Do NOT deploy ARIMA, it is only used for benchmarking (Rule 6).

#### [MODIFY] `train_lstm.py`
- **Goal**: Predict `close_price` (T+1 to T+5).
- **Key Features**: 
  - Use `MinMaxScaler` on sliding windows.
  - Train strictly on **valid trading days** (no forward-filling to create weekend data).
  - Compare RMSE against the ARIMA baseline.
  - Write predictions to BigQuery (target table specified via `BQ_PREDICTIONS_TABLE`).

---

### 3. Bank Clustering (K-Means & PCA)

#### [MODIFY] `train_kmeans.py`
- **Goal**: Cluster the 45 banks.
- **Key Features**:
  - Accept `StandardScaler` processed input.
  - Run PCA to retain components explaining >= 80% variance.
  - Apply K-Means, select optimal `k` based on the Elbow Method and Silhouette Analysis.
  - Evaluate using Log Silhouette Score and Davies-Bouldin Index.
  - Push the cluster assignment table to BigQuery.

---

### 4. Credit Risk Classification (Random Forest)

#### [MODIFY] `baseline_logistic.py`
- **Goal**: Baseline Logistic Regression model.
- **Key Features**: Calculate AUC-ROC to establish a baseline for Random Forest.

#### [MODIFY] `train_random_forest.py`
- **Goal**: Risk classification (Label `1` if `npl_ratio` >= 0.03, else `0`).
- **Key Features**:
  - Do not use random split; a **time-based split** is mandatory to prevent data leakage.
  - Log **Feature Importance** and save the bar chart to `reports/figures/`.
  - Strict thresholds: AUC-ROC > 0.80, Recall for class 1 >= 0.85.
  - Write predicted risk labels to BigQuery.

---

## Verification Plan

### Automated Tests
- Scripts will include built-in checks for null/empty values using `assert`.
- Errors will be caught and logged using the standard `src/utils/logger.py`.

### Manual Verification
- You (the User) will need to check the output metrics printed in the terminal (Logs): 
  - Check if the Recall for the high-risk class exceeds 85%.
  - Check if the LSTM RMSE is lower than ARIMA.
  - Check if the Feature Importance and Silhouette charts are correctly saved in `reports/figures/`.
  - Check the BigQuery Console to verify the prediction tables are successfully created.
