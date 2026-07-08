"""Task 2.3: LSTM model training and comparison (Univariate vs Multivariate) for banking stocks.

Trains and compares Univariate LSTM (close price only) against Multivariate LSTM
(close, open, high, low, volume, and changes) for BID, TCB, VCB, CTG.
Saves model files, outputs comparison metrics, and writes the best model's predictions to BigQuery.
"""

from __future__ import annotations

import os
import sys
import pickle
import json

# Đảm bảo console in ra tiếng Việt chuẩn UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
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

FORECAST_HORIZON = 5      # Predict T+1 through T+5
TEST_SIZE_RATIO = 0.2     # Last 20% of data for testing
RECENT_ROWS_LIMIT = 750   # Use the last 750 trading days (~3 years) for stability


def _get_hyperparams() -> dict:
    """Return unified hyperparameters optimized for execution speed and accuracy.
    """
    return {
        "window_size": 20,
        "epochs": 35,
        "batch_size": 32,
        "lstm_units": 64,
        "dense_units": 32,
        "dropout_rate": 0.2,
        "stacked": False,
    }

# Ticker configs mapping key to symbol
STOCK_CONFIGS = {
    1: {"symbol": "BID", "features": [
        "close_price", "open_price", "high_price", "low_price", "trading_volume",
        "price_change_pct", "volume_change_pct"
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
    """
    X, y = [], []
    for i in range(len(data) - window - horizon + 1):
        X.append(data[i : i + window])
        # close_price is assumed to be index 0
        y.append(data[i + window : i + window + horizon, 0])
    return np.array(X), np.array(y)


def build_lstm_model(
    input_shape: tuple, horizon: int, lstm_units: int = 64,
    dense_units: int = 32, dropout_rate: float = 0.2, stacked: bool = False
) -> tf.keras.Model:
    """Construct the LSTM model architecture.
    """
    layers = [
        Input(shape=input_shape),
        LSTM(lstm_units, return_sequences=False),
        Dropout(dropout_rate),
        Dense(dense_units, activation="relu"),
        Dense(horizon),
    ]

    model = Sequential(layers)
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def train_single_config(
    symbol: str,
    df: pd.DataFrame,
    features_list: list[str],
    hp: dict,
    model_type: str,
    config
) -> tuple[float, float, tf.keras.Model, MinMaxScaler, pd.DataFrame]:
    """Train a single LSTM configuration (univariate or multivariate).
    """
    # Reorder so close_price is the first column
    feature_data = df[features_list].values
    feature_data = np.nan_to_num(feature_data, nan=0.0, posinf=0.0, neginf=0.0)

    window_size = hp["window_size"]
    
    # Scale
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(feature_data)

    # Sequences
    X, y = create_sequences(scaled_data, window_size, FORECAST_HORIZON)
    
    split_idx = int(len(X) * (1 - TEST_SIZE_RATIO))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    model = build_lstm_model(
        input_shape=(window_size, len(features_list)),
        horizon=FORECAST_HORIZON,
        lstm_units=hp["lstm_units"],
        dense_units=hp["dense_units"],
        dropout_rate=hp["dropout_rate"],
        stacked=hp["stacked"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        )
    ]

    model.fit(
        X_train,
        y_train,
        epochs=hp["epochs"],
        batch_size=hp["batch_size"],
        validation_split=0.1,
        callbacks=callbacks,
        verbose=0,
    )

    # Evaluate
    y_pred_scaled = model.predict(X_test, verbose=0)
    num_features = len(features_list)

    def inverse_close_price(scaled_values: np.ndarray) -> np.ndarray:
        padded = np.zeros((scaled_values.shape[0], num_features))
        padded[:, 0] = scaled_values
        return scaler.inverse_transform(padded)[:, 0]

    all_actual = np.concatenate(
        [inverse_close_price(y_test[:, h]) for h in range(FORECAST_HORIZON)]
    )
    all_predicted = np.concatenate(
        [inverse_close_price(y_pred_scaled[:, h]) for h in range(FORECAST_HORIZON)]
    )
    rmse = float(np.sqrt(mean_squared_error(all_actual, all_predicted)))
    mae = float(mean_absolute_error(all_actual, all_predicted))

    return rmse, mae, model, scaler


def _generate_predictions_df(
    df: pd.DataFrame,
    model: tf.keras.Model,
    scaler: MinMaxScaler,
    stock_key: int,
    features_list: list[str],
    model_name: str,
    window_size: int = 20,
) -> pd.DataFrame:
    """Generate future predictions for BQ write-back.
    """
    feature_data = df[features_list].values
    scaled_data = scaler.transform(feature_data)

    last_window = scaled_data[-window_size:].reshape(
        1, window_size, len(features_list)
    )
    pred_scaled = model.predict(last_window, verbose=0)

    num_features = len(features_list)
    padded = np.zeros((FORECAST_HORIZON, num_features))
    padded[:, 0] = pred_scaled[0]
    predicted_prices = scaler.inverse_transform(padded)[:, 0]

    last_date_key = int(df["date_key"].iloc[-1])

    predictions_df = pd.DataFrame({
        "base_date_key": [last_date_key] * FORECAST_HORIZON,
        "stock_key": [stock_key] * FORECAST_HORIZON,
        "horizon": [f"T+{i + 1}" for i in range(FORECAST_HORIZON)],
        "predicted_close_price": predicted_prices,
        "model_name": [model_name] * FORECAST_HORIZON,
    })
    return predictions_df


def train_and_evaluate_stock(stock_key: int, symbol: str, config) -> dict:
    """Train both Univariate and Multivariate LSTM models and compare them.
    """
    logger.info("=== Bắt đầu huấn luyện và so sánh LSTM cho mã %s (stock_key %d) ===", symbol, stock_key)

    df = build_stock_features(stock_key)
    if df.empty:
        logger.error("Không tìm thấy dữ liệu đặc trưng cho mã %s.", symbol)
        return {}

    # Restrict to recent data for model stability
    if len(df) > RECENT_ROWS_LIMIT:
        df = df.iloc[-RECENT_ROWS_LIMIT:].reset_index(drop=True)

    hp = _get_hyperparams()
    
    # Feature configurations
    univariate_features = ["close_price"]
    multivariate_features = [
        "close_price", "open_price", "high_price", "low_price", "trading_volume",
        "price_change_pct", "volume_change_pct"
    ]

    # 1. Train Univariate Model
    uni_rmse, uni_mae, uni_model, uni_scaler = train_single_config(
        symbol, df, univariate_features, hp, "univariate", config
    )
    logger.info("%s [LSTM Univariate] - RMSE: %.4f, MAE: %.4f", symbol, uni_rmse, uni_mae)

    # 2. Train Multivariate Model
    multi_rmse, multi_mae, multi_model, multi_scaler = train_single_config(
        symbol, df, multivariate_features, hp, "multivariate", config
    )
    logger.info("%s [LSTM Multivariate] - RMSE: %.4f, MAE: %.4f", symbol, multi_rmse, multi_mae)

    # Select the best model
    is_multi_better = multi_rmse < uni_rmse
    best_rmse = multi_rmse if is_multi_better else uni_rmse
    best_mae = multi_mae if is_multi_better else uni_mae
    best_model_name = "LSTM_Multivariate" if is_multi_better else "LSTM_Univariate"
    best_model = multi_model if is_multi_better else uni_model
    best_scaler = multi_scaler if is_multi_better else uni_scaler
    best_features = multivariate_features if is_multi_better else univariate_features

    logger.info("%s Model Tốt Nhất: %s (RMSE: %.4f vs MAE: %.4f)", symbol, best_model_name, best_rmse, best_mae)

    # Compare with ARIMA baseline
    baseline_metrics = run_baselines(stock_key)
    arima_rmse = baseline_metrics["arima_rmse"]
    arima_mae = baseline_metrics["arima_mae"]
    logger.info("%s So sánh vs ARIMA Baseline - Best LSTM RMSE: %.4f vs ARIMA RMSE: %.4f", symbol, best_rmse, arima_rmse)

    # Save artifacts for the best model
    os.makedirs(config.model_artifact_path, exist_ok=True)
    best_model.save(os.path.join(config.model_artifact_path, f"lstm_{symbol.lower()}_best.keras"))
    with open(os.path.join(config.model_artifact_path, f"scaler_{symbol.lower()}_best.pkl"), "wb") as f:
        pickle.dump(best_scaler, f)

    # Generate predictions using the best model
    predictions_df = _generate_predictions_df(
        df, best_model, best_scaler, stock_key, best_features, best_model_name, hp["window_size"]
    )

    return {
        "symbol": symbol,
        "univariate": {"rmse": uni_rmse, "mae": uni_mae},
        "multivariate": {"rmse": multi_rmse, "mae": multi_mae},
        "best_model_name": best_model_name,
        "best_rmse": best_rmse,
        "best_mae": best_mae,
        "arima_rmse": arima_rmse,
        "arima_mae": arima_mae,
        "predictions_df": predictions_df,
    }


def _flush_all_predictions_to_bigquery(
    all_predictions: pd.DataFrame, config
) -> None:
    """Write predictions to BigQuery predictions table.
    """
    from google.cloud import bigquery as bq

    client = get_bigquery_client()
    table_id = get_full_table_id(config.bq_predictions_table)

    job_config = bq.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )

    job = client.load_table_from_dataframe(
        all_predictions, table_id, job_config=job_config
    )
    job.result()
    logger.info(
        "Đã lưu %d dự báo (của 4 mã cổ phiếu) lên BigQuery table %s.",
        len(all_predictions),
        table_id,
    )


def train_all_lstm_models():
    """Run the training and evaluation loop.
    """
    config = load_config()
    results = {}
    all_predictions = []
    
    stocks = {
        1: "BID",
        2: "TCB",
        3: "VCB",
        4: "CTG"
    }

    for sk, symbol in stocks.items():
        res = train_and_evaluate_stock(sk, symbol, config)
        if res:
            results[symbol] = {
                "uni_rmse": res["univariate"]["rmse"],
                "uni_mae": res["univariate"]["mae"],
                "multi_rmse": res["multivariate"]["rmse"],
                "multi_mae": res["multivariate"]["mae"],
                "best_model": res["best_model_name"],
                "best_rmse": res["best_rmse"],
                "arima_rmse": res["arima_rmse"],
                "arima_mae": res["arima_mae"]
            }
            all_predictions.append(res["predictions_df"])

    # Flush predictions to BQ
    if all_predictions:
        combined = pd.concat(all_predictions, ignore_index=True)
        _flush_all_predictions_to_bigquery(combined, config)
        
        # Save comparison results locally for Streamlit integration
        comp_path = "./data/processed/lstm_model_comparison.json"
        with open(comp_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        logger.info("Đã lưu bảng so sánh hiệu năng mô hình vào: %s", comp_path)
    else:
        logger.error("Không có dự báo nào được tạo.")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    train_all_lstm_models()
