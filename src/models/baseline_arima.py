"""Task C-03: ARIMA and Moving Average baseline for banking stock price forecasting.

Used as a performance comparison baseline against LSTM. NOT a production
deployment. ARIMA is never deployed — it exists solely as a benchmark
(AGENTS.md Rule 6).

See docs/ml-spec.md Section 4.1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

from src.models.feature_engineering_stock import build_stock_features
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Train/test split ratio — use the last portion for testing
TEST_SIZE_RATIO = 0.2


def moving_average_baseline(
    series: pd.Series, window: int = 5
) -> tuple[np.ndarray, float, float]:
    """Compute Moving Average predictions and evaluation metrics.

    Args:
        series: Time-ordered close_price series.
        window: Rolling window size for the moving average.

    Returns:
        Tuple of (predictions, rmse, mae).
    """
    # Use rolling mean as the prediction for the next value
    ma_predictions = series.rolling(window=window).mean().shift(1)

    # Evaluate only on the portion where MA is available
    valid_mask = ~ma_predictions.isna()
    actual = series[valid_mask].values
    predicted = ma_predictions[valid_mask].values

    rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
    mae = float(mean_absolute_error(actual, predicted))

    logger.info(
        "Moving Average (window=%d) baseline — RMSE: %.4f, MAE: %.4f",
        window,
        rmse,
        mae,
    )
    return predicted, rmse, mae


def arima_baseline(
    train: pd.Series, test: pd.Series, order: tuple = (5, 1, 0)
) -> tuple[np.ndarray, float, float]:
    """Fit an ARIMA model and generate predictions on the test set.

    Args:
        train: Training portion of the close_price series.
        test: Test portion of the close_price series.
        order: ARIMA(p, d, q) order.

    Returns:
        Tuple of (predictions, rmse, mae).
    """
    logger.info(
        "Fitting ARIMA%s on %d training samples...", order, len(train)
    )

    try:
        model = ARIMA(train, order=order)
        fitted = model.fit()
        # Forecast the length of the test set
        predictions = fitted.forecast(steps=len(test))
        rmse = float(np.sqrt(mean_squared_error(test.values, predictions.values)))
        mae = float(mean_absolute_error(test.values, predictions.values))
    except Exception as e:
        logger.error("ARIMA baseline fitting failed: %s. Using mean fallback.", str(e))
        # Fallback to mean prediction
        mean_pred = train.mean()
        predictions = pd.Series([mean_pred] * len(test))
        rmse = float(np.sqrt(mean_squared_error(test.values, predictions.values)))
        mae = float(mean_absolute_error(test.values, predictions.values))

    logger.info("ARIMA%s baseline — RMSE: %.4f, MAE: %.4f", order, rmse, mae)
    return predictions.values, rmse, mae


def run_baselines(stock_key: int = 1) -> dict:
    """Execute both baseline models and return their metrics.

    Args:
        stock_key: Stock key (1: BID, 2: TCB, 3: VCB, 4: CTG)

    Returns:
        Dictionary with keys 'arima_rmse', 'arima_mae', 'ma_rmse', 'ma_mae'.
    """
    # Load features (only need close_price for baselines)
    df = build_stock_features(stock_key)
    if df.empty:
        logger.error("No features found to run baselines for stock_key %d.", stock_key)
        return {"arima_rmse": 999.0, "arima_mae": 999.0, "ma_rmse": 999.0, "ma_mae": 999.0}

    close_prices = df["close_price"].reset_index(drop=True)

    logger.info(
        "Running baselines for stock_key %d on %d trading day records.", stock_key, len(close_prices)
    )

    # Train/test split — strictly sequential for time series
    split_idx = int(len(close_prices) * (1 - TEST_SIZE_RATIO))
    train = close_prices.iloc[:split_idx]
    test = close_prices.iloc[split_idx:]

    logger.info(
        "Train/test split: %d train, %d test samples.", len(train), len(test)
    )

    # Moving Average baseline
    _, ma_rmse, ma_mae = moving_average_baseline(close_prices, window=5)

    # ARIMA baseline
    _, arima_rmse, arima_mae = arima_baseline(train, test, order=(5, 1, 0))

    results = {
        "arima_rmse": arima_rmse,
        "arima_mae": arima_mae,
        "ma_rmse": ma_rmse,
        "ma_mae": ma_mae,
    }

    logger.info("Baseline results for stock_key %d: %s", stock_key, results)
    return results


if __name__ == "__main__":
    for sk in [1, 2, 3, 4]:
        baseline_metrics = run_baselines(sk)
        logger.info("Baseline evaluation complete for stock_key %d.", sk)
