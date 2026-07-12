import argparse
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(ROOT, "db", "nexus_bank.db")
CLEAN_DIR = os.path.join(ROOT, "data", "clean")


def ensure_streaming_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS streaming_ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            tick_time TEXT NOT NULL,
            price REAL NOT NULL,
            source TEXT NOT NULL DEFAULT 'stream'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_stream_ticker_time ON streaming_ticks(ticker, tick_time)")
    conn.commit()


def poll_live(tickers):
    """LIVE MODE: pull the latest intraday tick from Yahoo Finance for each ticker."""
    import yfinance as yf
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for t in tickers:
        info = yf.Ticker(t).fast_info
        rows.append({"ticker": t, "tick_time": now, "price": info["lastPrice"], "source": "yfinance_live"})
    return rows


def poll_sample(tickers, last_prices, rng):
    """SAMPLE MODE: simulate the next tick via a small random walk from the last real close."""
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for t in tickers:
        step = rng.normal(0, 0.0015)
        last_prices[t] *= (1 + step)
        rows.append({"ticker": t, "tick_time": now, "price": round(last_prices[t], 2), "source": "simulated_stream"})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["live", "sample"], default="sample")
    parser.add_argument("--ticks", type=int, default=20, help="number of polling cycles to run")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between polls")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_streaming_table(conn)

    # seed the simulated walk from the last real closing price per ticker
    prices = pd.read_csv(os.path.join(CLEAN_DIR, "stock_prices_clean.csv"))
    last_prices = prices.sort_values("date").groupby("ticker")["close"].last().to_dict()
    rng = np.random.default_rng(7)

    print(f"Starting streaming ingestion ({args.mode} mode): {args.ticks} ticks, "
          f"{args.interval}s apart. This APPENDS to streaming_ticks — it never replaces "
          f"existing rows, unlike the batch loader in 03_pipeline_storage.py.")

    total_inserted = 0
    for i in range(args.ticks):
        rows = poll_live(list(last_prices.keys())) if args.mode == "live" else poll_sample(list(last_prices.keys()), last_prices, rng)
        conn.executemany(
            "INSERT INTO streaming_ticks (ticker, tick_time, price, source) VALUES (:ticker, :tick_time, :price, :source)",
            rows,
        )
        conn.commit()
        total_inserted += len(rows)
        print(f"  tick {i+1}/{args.ticks}: inserted {len(rows)} rows "
              f"(running total in table: {conn.execute('SELECT COUNT(*) FROM streaming_ticks').fetchone()[0]})")
        if i < args.ticks - 1:
            time.sleep(args.interval)

    print(f"\nStreaming run complete. {total_inserted} new rows appended this run.")
    print("This table only ever grows via INSERT (append), which is the defining "
          "difference from the batch tables (stock_prices, transactions) that are "
          "replaced wholesale on each run of 03_pipeline_storage.py — see Section 7.1 "
          "of the report for why we treat these as two distinct ingestion patterns.")
    conn.close()


if __name__ == "__main__":
    main()
