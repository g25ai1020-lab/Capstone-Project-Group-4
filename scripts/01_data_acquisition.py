import argparse
import os
import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

TICKERS = ["AAPL", "MSFT", "JPM", "XOM", "GOOGL"]
FX_PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]  

# LIVE MODE 

def fetch_live():
    import yfinance as yf
    import pandas_datareader.data as web
    from datetime import datetime

    start, end = "2018-01-01", "2025-06-30"

    # 1. Stock prices from Yahoo Finance
    all_prices = []
    for t in TICKERS:
        df = yf.download(t, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.reset_index(inplace=True)
        df.columns = [str(c).lower() for c in df.columns]
        df["ticker"] = t
        all_prices.append(df)
    prices = pd.concat(all_prices, ignore_index=True)
    prices.to_csv(os.path.join(RAW_DIR, "stock_prices_raw.csv"), index=False)
    # 1b. FX rates from Yahoo Finance (brief: "stock prices, FX rates")
    all_fx = []
    for pair in FX_PAIRS:
        df = yf.download(pair, start=start, end=end, progress=False)
        df["pair"] = pair.replace("=X", "")
        df.reset_index(inplace=True)
        df.rename(columns={"Date": "date"}, inplace=True)
        all_fx.append(df)
    fx = pd.concat(all_fx, ignore_index=True)
    fx.to_csv(os.path.join(RAW_DIR, "fx_rates_raw.csv"), index=False)
# 1b. FX rates from Yahoo Finance (brief: "stock prices, FX rates")
    all_fx = []
    for pair in FX_PAIRS:
        df = yf.download(pair, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.reset_index(inplace=True)
        df.columns = [str(c).lower() for c in df.columns]
        df["pair"] = pair.replace("=X", "")
        df.rename(columns={"close": "rate"}, inplace=True)
        all_fx.append(df)
    fx = pd.concat(all_fx, ignore_index=True)
    fx.to_csv(os.path.join(RAW_DIR, "fx_rates_raw.csv"), index=False)
    # 2. Macro indicators from FRED 
    macro = web.DataReader(["GDP", "CPIAUCSL", "FEDFUNDS"], "fred", start, end)
    macro.reset_index(inplace=True)
    macro.rename(columns={"DATE": "date"}, inplace=True)
    macro.to_csv(os.path.join(RAW_DIR, "macro_indicators_raw.csv"), index=False)

    # 3. Kaggle credit card fraud dataset
    fraud_path = os.path.join(RAW_DIR, "creditcard.csv")
    if not os.path.exists(fraud_path):
        print("Kaggle fraud CSV not found. Please download manually and re-run.")

    print("LIVE fetch complete.")

# SAMPLE MODE 
def fetch_sample():
    rng = np.random.default_rng(42)

    # 1. Stock prices (business days, with deliberate gaps for market holidays,
    #    a few duplicated timestamps, and a few obvious bad-tick outliers)
    dates = pd.bdate_range("2020-01-01", "2025-06-30")
    frames = []
    for i, t in enumerate(TICKERS):
        n = len(dates)
        drift = 0.00025 + i * 0.00003
        shocks = rng.normal(drift, 0.018, n)
        price = 100 * (1 + i * 0.6) * np.exp(np.cumsum(shocks))
        vol = rng.integers(1_000_000, 15_000_000, n)
        df = pd.DataFrame({
            "date": dates,
            "ticker": t,
            "open": price * (1 - rng.uniform(0, 0.004, n)),
            "high": price * (1 + rng.uniform(0, 0.01, n)),
            "low": price * (1 - rng.uniform(0, 0.01, n)),
            "close": price,
            "volume": vol,
        })
        # simulate market-holiday gaps (drop ~1.5% of rows at random)
        drop_idx = rng.choice(df.index, size=int(0.015 * n), replace=False)
        df = df.drop(index=drop_idx)
        # inject a handful of bad ticks (fat-finger trades / erroneous prints)
        bad_idx = rng.choice(df.index, size=5, replace=False)
        df.loc[bad_idx, "close"] = df.loc[bad_idx, "close"] * rng.choice([0.1, 5.0], 5)
        # mixed timestamp formatting to mimic real-world messiness
        df["date"] = df["date"].astype(str)
        frames.append(df)
    prices = pd.concat(frames, ignore_index=True)
    prices.to_csv(os.path.join(RAW_DIR, "stock_prices_raw.csv"), index=False)

    # 1b. FX rates (brief explicitly asks for "stock prices, FX rates")
    fx_frames = []
    fx_base = {"EURUSD": 1.08, "GBPUSD": 1.27, "USDJPY": 148.0}
    for pair, base in fx_base.items():
        n = len(dates)
        shocks = rng.normal(0, 0.004, n)
        rate = base * np.exp(np.cumsum(shocks))
        df = pd.DataFrame({"date": dates, "pair": pair, "rate": rate})
        drop_idx = rng.choice(df.index, size=int(0.01 * n), replace=False)
        df = df.drop(index=drop_idx)
        df["date"] = df["date"].astype(str)
        fx_frames.append(df)
    fx = pd.concat(fx_frames, ignore_index=True)
    fx.to_csv(os.path.join(RAW_DIR, "fx_rates_raw.csv"), index=False)

    # 2. Macro indicators (monthly frequency, like real FRED data)
    months = pd.date_range("2020-01-01", "2025-06-01", freq="MS")
    gdp = 21000 + np.cumsum(rng.normal(60, 40, len(months)))
    cpi = 258 + np.cumsum(rng.normal(0.5, 0.3, len(months)))
    fedfunds = np.clip(np.cumsum(rng.normal(0.02, 0.15, len(months))) + 0.25, 0, 6)
    macro = pd.DataFrame({"date": months, "GDP": gdp, "CPIAUCSL": cpi, "FEDFUNDS": fedfunds})
    macro.to_csv(os.path.join(RAW_DIR, "macro_indicators_raw.csv"), index=False)

    # 3. Credit-card-style transaction dataset 
    n_txn = 50_000
    fraud_rate = 0.0017  # matches real-world class imbalance (~0.17%)
    n_fraud = int(n_txn * fraud_rate)
    n_legit = n_txn - n_fraud

    def make_features(n, fraud=False):
        base = rng.normal(0, 1, (n, 10))
        if fraud:
            base += rng.normal(2.5, 1.2, (n, 10))  # fraud cases shifted in feature space
        return base

    legit_feats = make_features(n_legit, fraud=False)
    fraud_feats = make_features(n_fraud, fraud=True)
    amounts_legit = np.round(np.abs(rng.lognormal(3.0, 1.1, n_legit)), 2)
    amounts_fraud = np.round(np.abs(rng.lognormal(4.2, 1.5, n_fraud)), 2)

    txn = pd.DataFrame(
        np.vstack([legit_feats, fraud_feats]),
        columns=[f"V{i}" for i in range(1, 11)],
    )
    txn["Amount"] = np.concatenate([amounts_legit, amounts_fraud])
    txn["Class"] = np.concatenate([np.zeros(n_legit), np.ones(n_fraud)]).astype(int)
    txn["account_id"] = rng.integers(1000, 1200, n_txn)
    txn["Time"] = np.sort(rng.integers(0, 60 * 60 * 24 * 180, n_txn))  # seconds over ~180 days
    txn = txn.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
    txn.to_csv(os.path.join(RAW_DIR, "creditcard.csv"), index=False)

    print(f"SAMPLE data written to {RAW_DIR}")
    print(f"  stock_prices_raw.csv   : {len(prices):,} rows")
    print(f"  fx_rates_raw.csv       : {len(fx):,} rows")
    print(f"  macro_indicators_raw.csv: {len(macro):,} rows")
    print(f"  creditcard.csv         : {len(txn):,} rows ({n_fraud} fraud, {fraud_rate*100:.2f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["live", "sample"], default="live")
    args = parser.parse_args()
    fetch_live() if args.mode == "live" else fetch_sample()
