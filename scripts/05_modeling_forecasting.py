"""
STEP 5a - MODELING: TIME-SERIES PRICE FORECASTING
Nexus Bank Capstone | Team 4

Model: ARIMA(5,1,0) per ticker on closing price.
Validation: walk-forward backtest — train on all data up to a cutoff date,
forecast the next 30 trading days, compare to actual. This avoids
look-ahead bias (we never let the model see the future).

Metrics reported: MAE, RMSE, MAPE.
"""

import os
import sqlite3
import warnings
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(ROOT, "db", "nexus_bank.db")
OUT_DIR = os.path.join(ROOT, "outputs")

HORIZON = 30  # trading days to forecast


def backtest_ticker(series, ticker):
    train = series.iloc[:-HORIZON]
    test = series.iloc[-HORIZON:]

    model = ARIMA(train, order=(5, 1, 0))
    fit = model.fit()
    forecast = fit.forecast(steps=HORIZON)
    forecast.index = test.index

    mae = np.mean(np.abs(forecast - test))
    rmse = np.sqrt(np.mean((forecast - test) ** 2))
    mape = np.mean(np.abs((forecast - test) / test)) * 100

    return forecast, test, {"ticker": ticker, "MAE": mae, "RMSE": rmse, "MAPE": mape}


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT ticker, date, close FROM stock_prices", conn, parse_dates=["date"])
    conn.close()

    results = []
    forecasts = {}
    for ticker, g in df.groupby("ticker"):
        g = g.sort_values("date").set_index("date")["close"]
        fc, actual, metrics = backtest_ticker(g, ticker)
        results.append(metrics)
        forecasts[ticker] = (fc, actual)

    res_df = pd.DataFrame(results)
    res_df.to_csv(os.path.join(OUT_DIR, "forecasting_backtest_results.csv"), index=False)
    print(res_df.to_string(index=False))
    print(f"\nAverage MAPE across tickers: {res_df['MAPE'].mean():.2f}%")

    # save one combined forecast-vs-actual csv for charting
    combo = []
    for ticker, (fc, actual) in forecasts.items():
        combo.append(pd.DataFrame({
            "ticker": ticker, "date": actual.index, "actual": actual.values, "forecast": fc.values
        }))
    pd.concat(combo).to_csv(os.path.join(ROOT, "data", "clean", "forecast_vs_actual.csv"), index=False)
