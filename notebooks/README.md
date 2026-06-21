# notebooks/

This directory contains Jupyter Notebooks for research, experimentation, and exploratory analysis. Each notebook corresponds to a specific phase of the CRISP-DM lifecycle.

> **Note**: Notebook files (`.ipynb`) must be created manually via JupyterLab or VS Code. The file names below are the required naming convention.

## Notebook Index

| File | Phase | Description | Owner |
|------|-------|-------------|-------|
| `01_EDA.ipynb` | Understand | Exploratory Data Analysis — distributions, correlations, missing values across all 7 source files | Member 1 |
| `02_ETL_BigQuery.ipynb` | Prepare | Prototype and validate the ETL pipeline before promoting to `src/etl/` production scripts | Member 2 |
| `03_ML_TimeSeries.ipynb` | Model | LSTM and ARIMA baseline experiments for BID stock price forecasting (T+1 to T+5) | Member 3 |
| `04_ML_Clustering.ipynb` | Model | PCA dimensionality reduction and K-Means clustering experiments for 46 banks | Member 3 |
| `05_ML_Classification.ipynb` | Model | Random Forest and Logistic Regression baseline for NPL ≥ 3% risk classification | Member 3 |
| `06_PCA_Visualization.ipynb` | Evaluate | Visualization of PCA components, cluster scatter plots, and feature importance charts | Member 4 |

## Usage

```bash
# Activate the virtual environment first
venv\Scripts\activate  # Windows

# Launch JupyterLab
jupyter lab
```

All notebooks must query data from BigQuery (not from local CSV files). Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set in your environment before running.

For environment setup instructions, see [`docs/env-config.md`](../docs/env-config.md).
