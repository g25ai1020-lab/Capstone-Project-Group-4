import os
import sqlite3
import pandas as pd
import time

ROOT = os.path.join(os.path.dirname(__file__), "..")
CLEAN_DIR = os.path.join(ROOT, "data", "clean")
DB_PATH = os.path.join(ROOT, "db", "nexus_bank.db")
os.makedirs(os.path.join(ROOT, "db"), exist_ok=True)

log = []


def load():
    conn = sqlite3.connect(DB_PATH)

    prices = pd.read_csv(os.path.join(CLEAN_DIR, "stock_prices_clean.csv"))
    macro = pd.read_csv(os.path.join(CLEAN_DIR, "macro_indicators_clean.csv"))
    txn = pd.read_csv(os.path.join(CLEAN_DIR, "transactions_clean.csv"))

    t0 = time.time()
    prices.to_sql("stock_prices", conn, if_exists="replace", index=False)
    macro.to_sql("macro_indicators", conn, if_exists="replace", index=False)
    txn.to_sql("transactions", conn, if_exists="replace", index=False)

    cur = conn.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS idx_price_ticker_date ON stock_prices(ticker, date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_txn_account_time ON transactions(account_id, Time)")
    conn.commit()
    load_time = time.time() - t0

    # quick benchmark: indexed query speed
    t1 = time.time()
    cur.execute("SELECT * FROM stock_prices WHERE ticker='AAPL' AND date >= '2024-01-01'")
    rows = cur.fetchall()
    query_time = time.time() - t1

    log.append(f"Loaded {len(prices):,} price rows, {len(macro)} macro rows, "
                f"{len(txn):,} transaction rows into SQLite in {load_time:.2f}s")
    log.append(f"Indexed query (AAPL, 2024 onward -> {len(rows)} rows) executed in {query_time*1000:.2f} ms")
    log.append("Indexes created: (ticker, date) on stock_prices | (account_id, Time) on transactions")

    conn.close()
    print("\n".join(log))
    with open(os.path.join(ROOT, "outputs", "pipeline_log.md"), "w") as f:
        f.write("\n".join(log))


# --- Incremental load pattern for production scheduling
def incremental_load_example():
    """
    In production (cron every night at 6pm after market close, or an
    Airflow DAG), you would NOT reload everything. Instead:

        conn = sqlite3.connect(DB_PATH)
        last_date = pd.read_sql(
            "SELECT MAX(date) as d FROM stock_prices", conn
        )["d"][0]
        new_data = fetch_since(last_date)   # only pull new rows from the API
        new_data.to_sql("stock_prices", conn, if_exists="append", index=False)

    This keeps daily pipeline runs fast (seconds, not minutes) as the
    dataset grows.
    """
    pass


if __name__ == "__main__":
    load()
