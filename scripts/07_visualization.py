import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(ROOT, "db", "nexus_bank.db")
CHART_DIR = os.path.join(ROOT, "outputs", "charts")
os.makedirs(CHART_DIR, exist_ok=True)
plt.rcParams["figure.dpi"] = 120

conn = sqlite3.connect(DB_PATH)
feat = pd.read_sql("SELECT * FROM price_features", conn, parse_dates=["date"])
txn = pd.read_sql("SELECT * FROM transactions", conn)
conn.close()

# 1. Price + moving averages (AAPL)
aapl = feat[feat.ticker == "AAPL"]
plt.figure(figsize=(9, 4.5))
plt.plot(aapl.date, aapl.close, label="Close", linewidth=1)
plt.plot(aapl.date, aapl.MA7, label="MA7", linewidth=1)
plt.plot(aapl.date, aapl.MA30, label="MA30", linewidth=1)
plt.fill_between(aapl.date, aapl.BB_lower, aapl.BB_upper, alpha=0.15, label="Bollinger Band")
plt.title("AAPL — Price Trend with Moving Averages & Bollinger Bands")
plt.xlabel("Date"); plt.ylabel("Price (USD)"); plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "01_price_trend_aapl.png")); plt.close()

# 2. Forecast vs actual (backtest)
fva = pd.read_csv(os.path.join(ROOT, "data", "clean", "forecast_vs_actual.csv"), parse_dates=["date"])
fig, axes = plt.subplots(2, 3, figsize=(14, 7))
for ax, (ticker, g) in zip(axes.flat, fva.groupby("ticker")):
    ax.plot(g.date, g.actual, label="Actual", marker="o", markersize=3)
    ax.plot(g.date, g.forecast, label="ARIMA Forecast", marker="x", markersize=3)
    ax.set_title(ticker); ax.tick_params(axis="x", rotation=45)
axes.flat[-1].axis("off")
handles, labels = axes.flat[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower right")
fig.suptitle("30-Day Backtest: ARIMA Forecast vs Actual Close Price")
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "02_forecast_vs_actual.png")); plt.close()

# 3. Volatility over time
plt.figure(figsize=(9, 4.5))
for ticker, g in feat.groupby("ticker"):
    plt.plot(g.date, g.Volatility20, label=ticker, linewidth=1)
plt.title("20-Day Rolling Annualised Volatility by Ticker")
plt.xlabel("Date"); plt.ylabel("Volatility"); plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "03_volatility.png")); plt.close()

# 4. Portfolio risk heatmap (correlation of daily returns)
pivot = feat.pivot(index="date", columns="ticker", values="returns")
corr = pivot.corr()
plt.figure(figsize=(6, 5))
im = plt.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
plt.xticks(range(len(corr)), corr.columns, rotation=45)
plt.yticks(range(len(corr)), corr.columns)
for i in range(len(corr)):
    for j in range(len(corr)):
        plt.text(j, i, f"{corr.iloc[i,j]:.2f}", ha="center", va="center", fontsize=8)
plt.colorbar(im, label="Correlation")
plt.title("Portfolio Risk Heatmap — Return Correlations")
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "04_risk_heatmap.png")); plt.close()

# 5. ROC curves
roc = np.load(os.path.join(ROOT, "outputs", "roc_data.npz"))
plt.figure(figsize=(6, 5))
for name in ["LogisticRegression", "RandomForest"]:
    plt.plot(roc[f"{name}_fpr"], roc[f"{name}_tpr"], label=name)
plt.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Random")
plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate")
plt.title("ROC Curve — Fraud Detection Models")
plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "05_roc_curve.png")); plt.close()

# 6. Fraud incident timeline
txn_sorted = txn.sort_values("Time")
plt.figure(figsize=(9, 4.5))
plt.scatter(txn_sorted.Time / 3600, txn_sorted.Amount, s=4, alpha=0.3, label="Legit", color="steelblue")
fraud = txn_sorted[txn_sorted.Class == 1]
plt.scatter(fraud.Time / 3600, fraud.Amount, s=25, color="red", label="Fraud", marker="x")
plt.xlabel("Time (hours since start)"); plt.ylabel("Transaction Amount")
plt.title("Fraud Incident Timeline")
plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "06_fraud_timeline.png")); plt.close()

print("Saved 6 charts to", CHART_DIR)
for f in sorted(os.listdir(CHART_DIR)):
    print(" -", f)
