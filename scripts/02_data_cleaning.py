import os
import pandas as pd
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW_DIR = os.path.join(ROOT, "data", "raw")
CLEAN_DIR = os.path.join(ROOT, "data", "clean")
OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

log_lines = []


def log(msg):
    print(msg)
    log_lines.append(msg)


def clean_prices():
    df = pd.read_csv(os.path.join(RAW_DIR, "stock_prices_raw.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    n_before = len(df)

    cleaned = []
    outlier_count = 0
    filled_count = 0
    for ticker, g in df.groupby("ticker"):
        g = g.set_index("date").sort_index()

        # remove exact duplicate timestamps (keep first)
        g = g[~g.index.duplicated(keep="first")]

        # reindex to full business-day calendar to expose market-holiday gaps
        full_range = pd.bdate_range(g.index.min(), g.index.max())
        g = g.reindex(full_range)
        g["ticker"] = ticker
        missing_before = g["close"].isna().sum()
        filled_count += missing_before
        # forward-fill price columns (market closed = no new price info)
        price_cols = ["open", "high", "low", "close"]
        g[price_cols] = g[price_cols].ffill()
        g["volume"] = g["volume"].fillna(0)

        # outlier detection: >40% single-day jump vs previous close
        pct_change = g["close"].pct_change().abs()
        bad = pct_change > 0.40
        outlier_count += bad.sum()
        g.loc[bad, price_cols] = np.nan
        g[price_cols] = g[price_cols].ffill()  # re-fill after removing outlier

        g.index.name = "date"
        cleaned.append(g.reset_index())

    out = pd.concat(cleaned, ignore_index=True)
    out.to_csv(os.path.join(CLEAN_DIR, "stock_prices_clean.csv"), index=False)

    log(f"Stock prices: {n_before:,} raw rows -> {len(out):,} clean rows "
        f"(reindexed to full business-day calendar)")
    log(f"  Market-holiday / missing-day gaps filled (forward-fill): {filled_count}")
    log(f"  Bad-tick outliers detected & corrected (>40% single-day move): {outlier_count}")
    return out


def clean_fx():
    df = pd.read_csv(os.path.join(RAW_DIR, "fx_rates_raw.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["pair", "date"]).reset_index(drop=True)
    n_before = len(df)

    cleaned = []
    filled_count = 0
    for pair, g in df.groupby("pair"):
        g = g.set_index("date").sort_index()
        g = g[~g.index.duplicated(keep="first")]
        full_range = pd.bdate_range(g.index.min(), g.index.max())
        g = g.reindex(full_range)
        g["pair"] = pair
        filled_count += g["rate"].isna().sum()
        g["rate"] = g["rate"].ffill()
        g.index.name = "date"
        cleaned.append(g.reset_index())

    out = pd.concat(cleaned, ignore_index=True)
    out.to_csv(os.path.join(CLEAN_DIR, "fx_rates_clean.csv"), index=False)
    log(f"FX rates: {n_before:,} raw rows -> {len(out):,} clean rows "
        f"(reindexed to full business-day calendar, {filled_count} gaps forward-filled)")
    return out


def clean_macro():
    df = pd.read_csv(os.path.join(RAW_DIR, "macro_indicators_raw.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    n_null = df.isna().sum().sum()
    df = df.ffill()
    df.to_csv(os.path.join(CLEAN_DIR, "macro_indicators_clean.csv"), index=False)
    log(f"Macro indicators: {len(df)} monthly rows, {n_null} nulls forward-filled")
    return df


def clean_transactions():
    df = pd.read_csv(os.path.join(RAW_DIR, "creditcard.csv"))
    n_before = len(df)
    n_dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    n_nulls = df.isna().sum().sum()
    df = df.dropna()
    df.to_csv(os.path.join(CLEAN_DIR, "transactions_clean.csv"), index=False)
    log(f"Transactions: {n_before:,} raw rows -> {len(df):,} clean rows "
        f"({n_dupes} duplicates removed, {n_nulls} null values removed)")
    log(f"  Class balance: {df['Class'].sum()} fraud / {len(df):,} total "
        f"({100*df['Class'].mean():.3f}% fraud rate)")
    return df


if __name__ == "__main__":
    log("=== DATA QUALITY REPORT — Nexus Bank Capstone (Team 4) ===\n")
    clean_prices()
    clean_fx()
    clean_macro()
    clean_transactions()
    with open(os.path.join(OUT_DIR, "data_quality_report.md"), "w") as f:
        f.write("\n".join(log_lines))
    print("\nSaved data_quality_report.md")
