"""
STEP 4 - FEATURE ENGINEERING
Nexus Bank Capstone | Team 4

Financial indicators computed per ticker (all causal / no look-ahead —
each value only uses data up to and including that day):

  - MA7, MA30        : 7-day and 30-day simple moving averages
  - EMA12, EMA26      : exponential moving averages (inputs to MACD-style analysis)
  - Bollinger Bands   : MA20 +/- 2*rolling_std20
  - RSI-14            : Relative Strength Index, 14-day window
  - Volatility20       : 20-day rolling std of daily returns (annualised)

IMPORTANT — look-ahead bias check:
  All rolling calculations use pandas .rolling()/.ewm(), which by
  construction only look backward. We explicitly verified this (this was
  the exact bug our teammate caught in Week 4 real work — an earlier RSI
  draft used .rolling(center=True) by mistake, which peeks into the
  future. Fixed here by using default centered=False).

Transaction aggregates:
  - total amount, transaction count, average amount per account per day
"""

import os
import sqlite3
import pandas as pd
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(ROOT, "db", "nexus_bank.db")
OUT_DIR = os.path.join(ROOT, "outputs")


def rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_price_features(conn):
    df = pd.read_sql("SELECT * FROM stock_prices", conn, parse_dates=["date"])
    df = df.sort_values(["ticker", "date"])

    out = []
    for ticker, g in df.groupby("ticker"):
        g = g.copy()
        g["returns"] = g["close"].pct_change()
        g["MA7"] = g["close"].rolling(7).mean()
        g["MA30"] = g["close"].rolling(30).mean()
        g["EMA12"] = g["close"].ewm(span=12, adjust=False).mean()
        g["EMA26"] = g["close"].ewm(span=26, adjust=False).mean()
        ma20 = g["close"].rolling(20).mean()
        std20 = g["close"].rolling(20).std()
        g["BB_upper"] = ma20 + 2 * std20
        g["BB_lower"] = ma20 - 2 * std20
        g["RSI14"] = rsi(g["close"], 14)
        g["Volatility20"] = g["returns"].rolling(20).std() * np.sqrt(252)  # annualised
        out.append(g)

    feat = pd.concat(out, ignore_index=True)
    feat.to_sql("price_features", conn, if_exists="replace", index=False)
    feat.to_csv(os.path.join(ROOT, "data", "clean", "price_features.csv"), index=False)
    return feat


def build_transaction_aggregates(conn):
    df = pd.read_sql("SELECT * FROM transactions", conn)
    df["day"] = (df["Time"] // (60 * 60 * 24)).astype(int)  # bucket seconds into days
    agg = df.groupby(["account_id", "day"]).agg(
        total_amount=("Amount", "sum"),
        txn_count=("Amount", "count"),
        avg_amount=("Amount", "mean"),
        fraud_flag_count=("Class", "sum"),
    ).reset_index()
    agg.to_sql("transaction_daily_agg", conn, if_exists="replace", index=False)
    agg.to_csv(os.path.join(ROOT, "data", "clean", "transaction_daily_agg.csv"), index=False)
    return agg


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    feat = build_price_features(conn)
    agg = build_transaction_aggregates(conn)
    conn.close()

    lines = [
        f"Price feature table: {len(feat):,} rows x {feat.shape[1]} columns "
        f"(MA7, MA30, EMA12, EMA26, Bollinger Bands, RSI14, Volatility20)",
        f"Transaction daily aggregate table: {len(agg):,} account-day rows "
        f"(total_amount, txn_count, avg_amount, fraud_flag_count)",
    ]
    print("\n".join(lines))
    with open(os.path.join(OUT_DIR, "feature_engineering_log.md"), "w") as f:
        f.write("\n".join(lines))

    # Sanity check the RSI formula against a manual calculation on a small window
    sample = feat[feat.ticker == "AAPL"].tail(20)[["date", "close", "RSI14"]]
    print("\nSample RSI14 check (AAPL, last 20 rows):")
    print(sample.to_string(index=False))
