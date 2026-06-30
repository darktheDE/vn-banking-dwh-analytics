"""Task C-04 / C-05: LSTM model training and stock price forecasting (T+1 to T+5) for focus banks.

Uses MinMaxScaler for sequence normalization. Trains on valid trading days only.
Saves model files as .keras and scalers as .pkl. Writes predictions back to BigQuery.
"""

from __future__ import annotations

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout

from src.models.baseline_arima import run_baselines
from src.models.feature_engineering_stock import build_stock_features
from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────
# Hyperparameters
# ──────────────────────────────────────────────
WINDOW_SIZE = 5          # Number of past trading days in each input sequence
FORECAST_HORIZON = 5     # Predict T+1 through T+5
TEST_SIZE_RATIO = 0.2    # Last 20% of data for testing
EPOCHS = 40
BATCH_SIZE = 16
LSTM_UNITS = 64
DENSE_UNITS = 32
DROPOUT_RATE = 0.2

# Ticker configs mapping key to symbol
STOCK_CONFIGS = {
    1: {"symbol": "BID", "features": [
        "close_price", "open_price", "high_price", "low_price", "trading_volume",
        "foreign_net_volume", "foreign_net_value", "prop_net_volume", "prop_net_value",
        "price_change_pct", "foreign_net_lag_1", "prop_net_lag_1"
    ]},
    2: {"symbol": "TCB", "features": [
        "close_price", "open_price", "high_price", "low_price", "trading_volume",
        "price_change_pct", "volume_change_pct"
    ]},
    3: {"symbol": "VCB", "features": [
        "close_price", "open_price", "high_price", "low_price", "trading_volume",
        "price_change_pct", "volume_change_pct"
    ]},
    4: {"symbol": "CTG", "features": [
        "close_price", "open_price", "high_price", "low_price", "trading_volume",
        "price_change_pct", "volume_change_pct"
    ]}
}


def create_sequences(
    data: np.ndarray, window: int, horizon: int
) -> tuple[np.ndarray, np.ndarray]:
    """Create sliding window sequences for LSTM training.

    Each sequence consists of `window` consecutive time steps as input (X)
    and the next `horizon` close_price values as output (y). The close_price
    is assumed to be the first column in the data array (index 0).
    """
    X, y = [], []
    for i in range(len(data) - window - horizon + 1):
        X.append(data[i : i + window])
        # close_price is index 0
        y.append(data[i + window : i + window + horizon, 0])
    return np.array(X), np.array(y)


def build_lstm_model(
    input_shape: tuple, horizon: int
) -> tf.keras.Model:
    """Construct the LSTM model architecture using Input layer to avoid warnings."""
    model = Sequential([
        Input(shape=input_shape),
        LSTM(LSTM_UNITS, return_sequences=False),
        Dropout(DROPOUT_RATE),
        Dense(DENSE_UNITS, activation="relu"),
        Dense(horizon),
    ])

    model.compile(
        optimizer="adam",
        loss="mse",
        metrics=["mae"],
    )

    logger.info("LSTM model built. Input shape: %s, Horizon: %d", input_shape, horizon)
    model.summary(print_fn=lambda line: logger.info(line))
    return model


def train_and_evaluate_stock(stock_key: int, config) -> dict:
    """Execute the full LSTM training pipeline for a given stock key."""
    symbol = STOCK_CONFIGS[stock_key]["symbol"]
    features_list = STOCK_CONFIGS[stock_key]["features"]

    logger.info("=== Starting training pipeline for stock key %d (%s) ===", stock_key, symbol)

    # ── Step 1: Load features ──
    df = build_stock_features(stock_key)
    if df.empty:
        logger.error("No features found for stock key %d (%s). Skipping.", stock_key, symbol)
        return {}

    logger.info("Loaded %d rows of %s stock features.", len(df), symbol)

    # Reorder so close_price is the first column
    feature_data = df[features_list].values
    feature_data = np.nan_to_num(feature_data, nan=0.0, posinf=0.0, neginf=0.0)

    # ── Step 2: MinMaxScaler normalization ──
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(feature_data)

    # ── Step 3: Create sequences ──
    X, y = create_sequences(scaled_data, WINDOW_SIZE, FORECAST_HORIZON)
    logger.info("Created %d sequences. X shape: %s, y shape: %s", len(X), X.shape, y.shape)

    split_idx = int(len(X) * (1 - TEST_SIZE_RATIO))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info("Train: %d sequences, Test: %d sequences.", len(X_train), len(X_test))

    # ── Step 4: Build and train LSTM ──
    model = build_lstm_model(
        input_shape=(WINDOW_SIZE, len(features_list)),
        horizon=FORECAST_HORIZON,
    )

    model.fit(
        X_train,
        y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.1,
        verbose=0,  # Minimize log spam
    )

    # ── Step 5: Evaluate ──
    y_pred_scaled = model.predict(X_test, verbose=0)

    num_features = len(features_list)

    def inverse_close_price(scaled_values: np.ndarray) -> np.ndarray:
        padded = np.zeros((scaled_values.shape[0], num_features))
        padded[:, 0] = scaled_values
        return scaler.inverse_transform(padded)[:, 0]

    # Evaluate each horizon step
    lstm_metrics = {}
    for h in range(FORECAST_HORIZON):
        actual = inverse_close_price(y_test[:, h])
        predicted = inverse_close_price(y_pred_scaled[:, h])
        rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
        mae = float(mean_absolute_error(actual, predicted))
        lstm_metrics[f"T+{h + 1}"] = {"rmse": rmse, "mae": mae}

    # Overall RMSE across all horizons
    all_actual = np.concatenate(
        [inverse_close_price(y_test[:, h]) for h in range(FORECAST_HORIZON)]
    )
    all_predicted = np.concatenate(
        [inverse_close_price(y_pred_scaled[:, h]) for h in range(FORECAST_HORIZON)]
    )
    lstm_rmse = float(np.sqrt(mean_squared_error(all_actual, all_predicted)))
    lstm_mae = float(mean_absolute_error(all_actual, all_predicted))

    logger.info("%s LSTM Overall — RMSE: %.4f, MAE: %.4f", symbol, lstm_rmse, lstm_mae)

    # ── Compare with ARIMA baseline ──
    baseline_metrics = run_baselines(stock_key)
    arima_rmse = baseline_metrics["arima_rmse"]

    logger.info(
        "%s Comparison — LSTM RMSE: %.4f vs ARIMA RMSE: %.4f",
        symbol,
        lstm_rmse,
        arima_rmse,
    )

    if lstm_rmse < arima_rmse:
        logger.info("ACCEPTANCE PASSED: %s LSTM RMSE is lower than ARIMA RMSE.", symbol)
    else:
        logger.warning(
            "ACCEPTANCE WARNING: %s LSTM RMSE is NOT lower than ARIMA RMSE.",
            symbol
        )

    # ── Step 6: Save model and scaler artifacts ──
    os.makedirs(config.model_artifact_path, exist_ok=True)
    model_path = os.path.join(config.model_artifact_path, f"lstm_{symbol.lower()}_price.keras")
    model.save(model_path)
    logger.info("LSTM model saved to %s", model_path)

    scaler_path = os.path.join(config.model_artifact_path, f"scaler_{symbol.lower()}_price.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    logger.info("Scaler saved to %s", scaler_path)

    # ── Step 7: Generate final predictions and write to BigQuery ──
    _write_predictions_to_bigquery(df, model, scaler, stock_key, features_list, config)

    return {
        "symbol": symbol,
        "lstm_rmse": lstm_rmse,
        "lstm_mae": lstm_mae,
        "arima_rmse": arima_rmse,
        "arima_mae": baseline_metrics["arima_mae"],
        "per_horizon": lstm_metrics,
    }


def _write_predictions_to_bigquery(
    df: pd.DataFrame,
    model: tf.keras.Model,
    scaler: MinMaxScaler,
    stock_key: int,
    features_list: list,
    config,
) -> None:
    """Generate T+1 to T+5 predictions from the latest data and write to BigQuery."""
    feature_data = df[features_list].values
    scaled_data = scaler.transform(feature_data)

    # Use the last window as input for the final forecast
    last_window = scaled_data[-WINDOW_SIZE:].reshape(
        1, WINDOW_SIZE, len(features_list)
    )
    pred_scaled = model.predict(last_window, verbose=0)

    # Inverse transform for close_price
    num_features = len(features_list)
    padded = np.zeros((FORECAST_HORIZON, num_features))
    padded[:, 0] = pred_scaled[0]
    predicted_prices = scaler.inverse_transform(padded)[:, 0]

    # Get the last date_key to generate future date labels
    last_date_key = int(df["date_key"].iloc[-1])
    symbol = STOCK_CONFIGS[stock_key]["symbol"]

    # Build the predictions DataFrame
    predictions_df = pd.DataFrame({
        "base_date_key": [last_date_key] * FORECAST_HORIZON,
        "stock_key": [stock_key] * FORECAST_HORIZON,
        "horizon": [f"T+{i + 1}" for i in range(FORECAST_HORIZON)],
        "predicted_close_price": predicted_prices,
        "model_name": ["LSTM"] * FORECAST_HORIZON,
    })

    logger.info("%s Predictions to write:\n%s", symbol, predictions_df.to_string())

    # Write to BigQuery
    client = get_bigquery_client()
    table_id = get_full_table_id(config.bq_predictions_table)

    from google.cloud import bigquery as bq

    job_config = bq.LoadJobConfig(
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_dataframe(
        predictions_df, table_id, job_config=job_config
    )
    job.result()  # Wait for completion

    logger.info(
        "Successfully wrote %d LSTM predictions for %s to %s.",
        len(predictions_df),
        symbol,
        table_id,
    )


def train_all_lstm_models():
    """Train LSTM forecasting models for all focus banking stocks."""
    config = load_config()
    results = {}
    for sk in STOCK_CONFIGS.keys():
        res = train_and_evaluate_stock(sk, config)
        if res:
            results[res["symbol"]] = res
    logger.info("All LSTM training pipelines complete. Final metrics: %s", results)


if __name__ == "__main__":
    train_all_lstm_models()
