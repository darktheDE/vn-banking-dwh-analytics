# src/models/

Machine Learning model scripts for the Financial Data Analytics Platform.

## Script Index

| Script | Task ID | Model | Description |
|--------|---------|-------|-------------|
| `feature_engineering_stock.py` | C-01 | — | Query and merge BID stock features from BigQuery |
| `feature_engineering_bank.py` | C-02 | — | Query bank CAMELS features and apply StandardScaler normalization |
| `baseline_arima.py` | C-03 | ARIMA | Establish ARIMA and Moving Average baseline RMSE for BID price forecasting |
| `train_lstm.py` | C-04/05 | LSTM | Train LSTM model and generate T+1 to T+5 predictions; write to BigQuery |
| `train_kmeans.py` | C-06/07/08 | K-Means + PCA | PCA dimensionality reduction and K-Means clustering; write cluster assignments to BigQuery |
| `baseline_logistic.py` | C-09 | Logistic Regression | Establish classification baseline AUC-ROC |
| `train_random_forest.py` | C-10/11/12 | Random Forest | Train classifier, log Feature Importance, write predictions to BigQuery |

## Acceptance Criteria

| Model | Metric | Threshold |
|-------|--------|-----------|
| LSTM | RMSE vs ARIMA baseline | LSTM RMSE < ARIMA RMSE |
| Random Forest | AUC-ROC | > 0.80 |
| Random Forest | Recall (High Risk class) | ≥ 85% |
| K-Means | Silhouette Score | Logged and interpreted |

See [`docs/ml-spec.md`](../../docs/ml-spec.md) for full specifications and [`docs/tasks.md`](../../docs/tasks.md) for verification steps.
