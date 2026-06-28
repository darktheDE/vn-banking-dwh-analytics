"""
LSTM Local — Dự báo giá cổ phiếu BID (T+1 đến T+5).

Đọc dữ liệu từ data/ML_data/bid_lstm_data.csv (3091 ngày giao dịch).
Sử dụng MinMaxScaler + sliding window (5 ngày) để train mạng LSTM.
Xuất kết quả dự báo ra data/ML_data/lstm_predictions_local.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
ML_DATA_DIR = os.path.join(BASE_DIR, "data", "data_ml")

# Hyperparameters
WINDOW_SIZE = 5
FORECAST_HORIZON = 5
TEST_SIZE_RATIO = 0.2
EPOCHS = 50
BATCH_SIZE = 16
LSTM_UNITS = 64
DROPOUT_RATE = 0.2

FEATURE_COLUMNS = [
    "close_price", "open_price", "high_price", "low_price",
    "trading_volume", "price_change_pct", "volume_change_pct",
]


def create_sequences(data, window, horizon):
    """Tạo chuỗi trượt (sliding windows) cho LSTM.

    Args:
        data: Mảng 2D đã chuẩn hóa.
        window: Số ngày quá khứ làm input.
        horizon: Số ngày tương lai cần dự báo.

    Returns:
        Tuple (X, y) với X shape (N, window, features), y shape (N, horizon).
    """
    X, y = [], []
    for i in range(len(data) - window - horizon + 1):
        X.append(data[i : i + window])
        y.append(data[i + window : i + window + horizon, 0])  # close_price = col 0
    return np.array(X), np.array(y)


def inverse_close_price(scaler, scaled_values, num_features):
    """Chuyển đổi ngược giá trị close_price từ scale về thang gốc."""
    padded = np.zeros((len(scaled_values), num_features))
    padded[:, 0] = scaled_values
    return scaler.inverse_transform(padded)[:, 0]


def train_lstm():
    """Pipeline chính: Load data -> Train LSTM -> Evaluate -> Export predictions."""
    # Lazy import TensorFlow (tránh crash nếu chưa cài)
    from tensorflow import keras

    data_path = os.path.join(ML_DATA_DIR, "bid_lstm_data.csv")
    if not os.path.exists(data_path):
        logger.error("Data not found at %s. Run data_loader.py first.", data_path)
        return None

    df = pd.read_csv(data_path)
    logger.info("Loaded %d rows of BID stock data for LSTM.", len(df))

    # Chuẩn bị feature matrix (xử lý inf từ pct_change khi volume trước = 0)
    feature_data = df[FEATURE_COLUMNS].values.astype(float)
    feature_data = np.nan_to_num(feature_data, nan=0.0, posinf=0.0, neginf=0.0)

    # MinMaxScaler
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(feature_data)
    logger.info("MinMaxScaler applied to %d features.", len(FEATURE_COLUMNS))

    # Tạo sequences
    X, y = create_sequences(scaled_data, WINDOW_SIZE, FORECAST_HORIZON)
    logger.info("Created %d sequences. X: %s, y: %s", len(X), X.shape, y.shape)

    # Time-based split (không random shuffle cho time series)
    split_idx = int(len(X) * (1 - TEST_SIZE_RATIO))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    logger.info("Train: %d sequences, Test: %d sequences.", len(X_train), len(X_test))

    # Build LSTM model
    model = keras.Sequential([
        keras.layers.LSTM(LSTM_UNITS, input_shape=(WINDOW_SIZE, len(FEATURE_COLUMNS)),
                          return_sequences=False),
        keras.layers.Dropout(DROPOUT_RATE),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dense(FORECAST_HORIZON),
    ])
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001),
                  loss="mse", metrics=["mae"])

    # Train
    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True
    )
    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS, batch_size=BATCH_SIZE,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=1,
    )

    # Evaluate on test set
    y_pred_scaled = model.predict(X_test)
    num_features = len(FEATURE_COLUMNS)

    metrics = {}
    for h in range(FORECAST_HORIZON):
        actual = inverse_close_price(scaler, y_test[:, h], num_features)
        predicted = inverse_close_price(scaler, y_pred_scaled[:, h], num_features)
        rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
        mae = float(mean_absolute_error(actual, predicted))
        mape = float(np.mean(np.abs((actual - predicted) / (actual + 1e-8))) * 100)
        metrics[f"T+{h+1}"] = {"rmse": rmse, "mae": mae, "mape": mape}
        logger.info("LSTM T+%d — RMSE: %.4f, MAE: %.4f, MAPE: %.2f%%", h+1, rmse, mae, mape)

    # Overall RMSE
    all_actual = np.concatenate(
        [inverse_close_price(scaler, y_test[:, h], num_features) for h in range(FORECAST_HORIZON)]
    )
    all_predicted = np.concatenate(
        [inverse_close_price(scaler, y_pred_scaled[:, h], num_features) for h in range(FORECAST_HORIZON)]
    )
    overall_rmse = float(np.sqrt(mean_squared_error(all_actual, all_predicted)))
    overall_mae = float(mean_absolute_error(all_actual, all_predicted))
    logger.info("LSTM Overall — RMSE: %.4f, MAE: %.4f", overall_rmse, overall_mae)

    # Generate final T+1 to T+5 predictions
    last_window = scaled_data[-WINDOW_SIZE:].reshape(1, WINDOW_SIZE, num_features)
    pred_scaled = model.predict(last_window)
    predicted_prices = inverse_close_price(scaler, pred_scaled[0], num_features)

    last_date = df["date"].iloc[-1]
    predictions_df = pd.DataFrame({
        "base_date": [last_date] * FORECAST_HORIZON,
        "horizon": [f"T+{i+1}" for i in range(FORECAST_HORIZON)],
        "predicted_close_price": predicted_prices,
        "model": ["LSTM"] * FORECAST_HORIZON,
    })

    out_path = os.path.join(ML_DATA_DIR, "lstm_predictions_local.csv")
    predictions_df.to_csv(out_path, index=False)
    logger.info("Saved LSTM predictions to %s", out_path)
    logger.info("Predictions:\n%s", predictions_df.to_string(index=False))

    return {
        "overall_rmse": overall_rmse,
        "overall_mae": overall_mae,
        "per_horizon": metrics,
        "predictions": predictions_df,
        "train_loss_final": history.history["loss"][-1],
        "val_loss_final": history.history["val_loss"][-1],
    }


if __name__ == "__main__":
    results = train_lstm()
    if results:
        logger.info("LSTM pipeline complete. Overall RMSE: %.4f", results["overall_rmse"])
