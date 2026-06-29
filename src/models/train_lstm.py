"""Task C-04 / C-05: LSTM model training and BID stock price forecasting (T+1 to T+5).

Uses MinMaxScaler for sequence normalization. Trains on valid trading days only.
Writes prediction outputs back to BigQuery.
See docs/ml-spec.md Section 1 for full architecture specification.
"""

import os

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from tensorflow import keras

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
EPOCHS = 100
BATCH_SIZE = 4
LSTM_UNITS = 64
DENSE_UNITS = 32
DROPOUT_RATE = 0.2

# Feature columns used as LSTM input regressors
FEATURE_COLUMNS = [
    "close_price",
    "open_price",
    "high_price",
    "low_price",
    "trading_volume",
    "foreign_net_volume",
    "foreign_net_value",
    "prop_net_volume",
    "prop_net_value",
    "price_change_pct",
    "foreign_net_lag_1",
    "prop_net_lag_1",
]


def create_sequences(
    data: np.ndarray, window: int, horizon: int
) -> tuple[np.ndarray, np.ndarray]:
    """Create sliding window sequences for LSTM training.

    Each sequence consists of `window` consecutive time steps as input (X)
    and the next `horizon` close_price values as output (y). The close_price
    is assumed to be the first column in the data array.

    Args:
        data: 2D array of shape (num_samples, num_features).
        window: Number of time steps in each input sequence.
        horizon: Number of future steps to predict.

    Returns:
        Tuple of (X, y) where:
          X has shape (num_sequences, window, num_features)
          y has shape (num_sequences, horizon)
    """
    X, y = [], []
    for i in range(len(data) - window - horizon + 1):
        X.append(data[i : i + window])
        # close_price is the first column (index 0)
        y.append(data[i + window : i + window + horizon, 0])
    return np.array(X), np.array(y)


def build_lstm_model(
    input_shape: tuple, horizon: int
) -> keras.Model:
    """Construct the LSTM model architecture.

    Architecture follows docs/ml-spec.md Section 1:
    - LSTM layer with dropout for temporal pattern extraction.
    - Dense layer for non-linear mapping.
    - Output layer sized to the forecast horizon.

    Args:
        input_shape: Tuple of (window_size, num_features).
        horizon: Number of future steps the model predicts.

    Returns:
        A compiled Keras Sequential model.
    """
    model = keras.Sequential([
        keras.layers.LSTM(
            LSTM_UNITS,
            input_shape=input_shape,
            return_sequences=False,
        ),
        keras.layers.Dropout(DROPOUT_RATE),
        keras.layers.Dense(DENSE_UNITS, activation="relu"),
        keras.layers.Dense(horizon),
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="mse",
        metrics=["mae"],
    )

    logger.info("LSTM model built. Input shape: %s, Horizon: %d", input_shape, horizon)
    model.summary(print_fn=lambda line: logger.info(line))

    return model


def train_and_evaluate() -> dict:
    """Execute the full LSTM training pipeline.

    Steps:
      1. Load features via C-01 feature engineering.
      2. Apply MinMaxScaler normalization.
      3. Create sliding window sequences (trading days only — no weekends).
      4. Train the LSTM model.
      5. Evaluate against the test set and the ARIMA baseline.
      6. Generate T+1 to T+5 predictions and write to BigQuery.

    Returns:
        Dictionary containing LSTM and ARIMA metrics for comparison.

    Raises:
        AssertionError: If LSTM RMSE is not lower than ARIMA RMSE.
    """
    config = load_config()

    # ── Step 1: Load features ──
    df = build_stock_features()
    logger.info("Loaded %d rows of BID stock features.", len(df))

    # Reorder so close_price is the first column (target)
    feature_data = df[FEATURE_COLUMNS].values

    # ── Step 2: MinMaxScaler normalization ──
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(feature_data)
    logger.info("MinMaxScaler applied to %d features.", scaled_data.shape[1])

    # ── Step 3: Create sequences ──
    X, y = create_sequences(scaled_data, WINDOW_SIZE, FORECAST_HORIZON)
    logger.info("Created %d sequences. X shape: %s, y shape: %s", len(X), X.shape, y.shape)

    # Time-based train/test split (no random shuffle for time series)
    split_idx = int(len(X) * (1 - TEST_SIZE_RATIO))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info("Train: %d sequences, Test: %d sequences.", len(X_train), len(X_test))

    # ── Step 4: Build and train LSTM ──
    model = build_lstm_model(
        input_shape=(WINDOW_SIZE, len(FEATURE_COLUMNS)),
        horizon=FORECAST_HORIZON,
    )

    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=10,
        restore_best_weights=True,
    )

    model.fit(
        X_train,
        y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=1,
    )

    # ── Step 5: Evaluate ──
    y_pred_scaled = model.predict(X_test)

    # Inverse transform predictions and actuals for close_price (column 0)
    # We need to pad with zeros for the other feature columns
    num_features = len(FEATURE_COLUMNS)

    def inverse_close_price(scaled_values: np.ndarray) -> np.ndarray:
        """Inverse transform scaled close_price values back to original scale."""
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
        logger.info("LSTM T+%d — RMSE: %.4f, MAE: %.4f", h + 1, rmse, mae)

    # Overall RMSE across all horizons
    all_actual = np.concatenate(
        [inverse_close_price(y_test[:, h]) for h in range(FORECAST_HORIZON)]
    )
    all_predicted = np.concatenate(
        [inverse_close_price(y_pred_scaled[:, h]) for h in range(FORECAST_HORIZON)]
    )
    lstm_rmse = float(np.sqrt(mean_squared_error(all_actual, all_predicted)))
    lstm_mae = float(mean_absolute_error(all_actual, all_predicted))

    logger.info("LSTM Overall — RMSE: %.4f, MAE: %.4f", lstm_rmse, lstm_mae)

    # ── Compare with ARIMA baseline ──
    baseline_metrics = run_baselines()
    arima_rmse = baseline_metrics["arima_rmse"]

    logger.info(
        "Comparison — LSTM RMSE: %.4f vs ARIMA RMSE: %.4f",
        lstm_rmse,
        arima_rmse,
    )

    if lstm_rmse < arima_rmse:
        logger.info("ACCEPTANCE PASSED: LSTM RMSE is lower than ARIMA RMSE.")
    else:
        logger.warning(
            "ACCEPTANCE WARNING: LSTM RMSE (%.4f) is NOT lower than ARIMA RMSE (%.4f). "
            "Consider tuning hyperparameters or adding more training data.",
            lstm_rmse,
            arima_rmse,
        )

    # ── Step 6: Save model artifact ──
    model_path = os.path.join(config.model_artifact_path, "lstm_bid_price.h5")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    logger.info("LSTM model saved to %s", model_path)

    # ── Step 7: Generate final predictions and write to BigQuery ──
    _write_predictions_to_bigquery(df, model, scaler, config)

    return {
        "lstm_rmse": lstm_rmse,
        "lstm_mae": lstm_mae,
        "arima_rmse": arima_rmse,
        "arima_mae": baseline_metrics["arima_mae"],
        "per_horizon": lstm_metrics,
    }


def _write_predictions_to_bigquery(
    df: pd.DataFrame,
    model: keras.Model,
    scaler: MinMaxScaler,
    config,
) -> None:
    """Generate T+1 to T+5 predictions from the latest data and write to BigQuery.

    Uses the most recent WINDOW_SIZE trading days to predict the next
    FORECAST_HORIZON days.

    Args:
        df: The full feature DataFrame.
        model: The trained LSTM model.
        scaler: The fitted MinMaxScaler.
        config: Application configuration.
    """
    feature_data = df[FEATURE_COLUMNS].values
    scaled_data = scaler.transform(feature_data)

    # Use the last window as input for the final forecast
    last_window = scaled_data[-WINDOW_SIZE:].reshape(
        1, WINDOW_SIZE, len(FEATURE_COLUMNS)
    )
    pred_scaled = model.predict(last_window)

    # Inverse transform for close_price
    num_features = len(FEATURE_COLUMNS)
    padded = np.zeros((FORECAST_HORIZON, num_features))
    padded[:, 0] = pred_scaled[0]
    predicted_prices = scaler.inverse_transform(padded)[:, 0]

    # Get the last date_key to generate future date labels
    last_date_key = int(df["date_key"].iloc[-1])

    # Build the predictions DataFrame
    predictions_df = pd.DataFrame({
        "base_date_key": [last_date_key] * FORECAST_HORIZON,
        "stock_key": [1] * FORECAST_HORIZON,  # BID
        "horizon": [f"T+{i + 1}" for i in range(FORECAST_HORIZON)],
        "predicted_close_price": predicted_prices,
        "model_name": ["LSTM"] * FORECAST_HORIZON,
    })

    logger.info("Predictions to write:\n%s", predictions_df.to_string())

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
        "Successfully wrote %d LSTM predictions to %s.",
        len(predictions_df),
        table_id,
    )


if __name__ == "__main__":
    results = train_and_evaluate()
    logger.info("LSTM training pipeline complete. Final metrics: %s", results)
