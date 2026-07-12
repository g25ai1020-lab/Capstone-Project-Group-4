import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW_DIR = os.path.join(ROOT, "data", "raw")
CLEAN_DIR = os.path.join(ROOT, "data", "clean")
CHART_DIR = os.path.join(ROOT, "outputs", "charts")
os.makedirs(CHART_DIR, exist_ok=True)
plt.rcParams["figure.dpi"] = 120

prices_raw = pd.read_csv(os.path.join(RAW_DIR, "stock_prices_raw.csv"), parse_dates=["date"])
prices_clean = pd.read_csv(os.path.join(CLEAN_DIR, "stock_prices_clean.csv"), parse_dates=["date"])
txn = pd.read_csv(os.path.join(CLEAN_DIR, "transactions_clean.csv"))

# 1. Missing-value summary BEFORE cleaning (per ticker, calendar-day basis)
missing_counts = []
for ticker, g in prices_raw.groupby("ticker"):
    full_range = pd.bdate_range(g.date.min(), g.date.max())
    missing = len(full_range) - g.date.nunique()
    missing_counts.append({"ticker": ticker, "missing_days": missing, "total_expected": len(full_range)})
miss_df = pd.DataFrame(missing_counts)

plt.figure(figsize=(7, 4))
plt.bar(miss_df.ticker, miss_df.missing_days, color="#1F3864")
plt.title("Missing Trading Days by Ticker (Before Cleaning)")
plt.ylabel("Missing days"); plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "07_eda_missing_values.png")); plt.close()

# 2. Distribution of daily returns (before any modeling)
prices_clean["returns"] = prices_clean.groupby("ticker")["close"].pct_change()
plt.figure(figsize=(7, 4))
for ticker, g in prices_clean.groupby("ticker"):
    plt.hist(g["returns"].dropna(), bins=60, alpha=0.5, label=ticker)
plt.title("Distribution of Daily Returns by Ticker (Pre-Modeling EDA)")
plt.xlabel("Daily return"); plt.ylabel("Frequency"); plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "08_eda_returns_distribution.png")); plt.close()

# 3. Class imbalance visualization (transactions)
counts = txn["Class"].value_counts()
plt.figure(figsize=(5, 4))
bars = plt.bar(["Legitimate", "Fraud"], [counts.get(0, 0), counts.get(1, 0)], color=["#1F3864", "#C0392B"])
plt.yscale("log")
plt.title(f"Class Imbalance in Transaction Data (Fraud rate: {100*txn['Class'].mean():.3f}%)")
plt.ylabel("Count (log scale)")
for b in bars:
    plt.text(b.get_x() + b.get_width()/2, b.get_height(), f"{int(b.get_height()):,}", ha="center", va="bottom")
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "09_eda_class_imbalance.png")); plt.close()

# 4. Amount distribution: legit vs fraud
plt.figure(figsize=(7, 4))
plt.hist(txn[txn.Class == 0]["Amount"], bins=60, alpha=0.6, label="Legitimate", density=True)
plt.hist(txn[txn.Class == 1]["Amount"], bins=60, alpha=0.6, label="Fraud", density=True)
plt.title("Transaction Amount Distribution: Legitimate vs Fraud")
plt.xlabel("Amount"); plt.ylabel("Density"); plt.legend(); plt.xlim(0, 500); plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "10_eda_amount_distribution.png")); plt.close()

print("EDA summary")
print(miss_df.to_string(index=False))
print(f"\nFraud rate: {100*txn['Class'].mean():.3f}% ({counts.get(1,0)} fraud / {len(txn):,} total)")
print(f"Return stats (all tickers pooled): mean={prices_clean['returns'].mean():.5f}, "
      f"std={prices_clean['returns'].std():.5f}, "
      f"skew={prices_clean['returns'].skew():.3f}")
print("\nSaved 4 EDA charts to", CHART_DIR)
