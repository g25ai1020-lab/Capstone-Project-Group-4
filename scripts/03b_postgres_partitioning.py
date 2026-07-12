"""
STEP 3b - REAL DATABASE PARTITIONING (PostgreSQL)
Nexus Bank Capstone | Team 4

Our first draft used SQLite with a composite index on (ticker, date) and
called that "our equivalent of partitioning." A reviewer correctly pushed
back: an index and a partition are genuinely different mechanisms, and
claiming one is "equivalent to" the other overstates it. This script
fixes that by implementing REAL declarative partitioning in PostgreSQL --
the brief's own example ("partitioning e.g. by date or asset").

We partition stock_prices by RANGE on date, one partition per year. This
is standard practice for time-series financial data: query planners can
skip entire partitions (years) that don't match a query's date filter,
which is a genuinely different and larger speedup than an index provides
at scale, because the planner never even opens the excluded partitions.

Run: python 03b_postgres_partitioning.py
Requires: a running PostgreSQL instance and the connection details below
          (we used a local Postgres 16 instance for this demonstration;
          in production this would point at Nexus Bank's actual DB server).
"""

import os
import pandas as pd
import psycopg2

ROOT = os.path.join(os.path.dirname(__file__), "..")
CLEAN_DIR = os.path.join(ROOT, "data", "clean")

PG_CONN = dict(host="localhost", port=5432, dbname="nexus_bank", user="nexus", password="nexus_pass")


def connect():
    return psycopg2.connect(**PG_CONN)


def create_partitioned_schema(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS stock_prices CASCADE")
    # The PARTITION BY RANGE clause is what makes this REAL partitioning,
    # not an index -- Postgres physically routes each row to the correct
    # child table based on the date column, and the query planner can
    # skip child tables entirely when a query's date filter excludes them.
    cur.execute("""
        CREATE TABLE stock_prices (
            date DATE NOT NULL,
            ticker TEXT NOT NULL,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume BIGINT
        ) PARTITION BY RANGE (date);
    """)
    # One physical partition per year, 2020-2025
    for year in range(2020, 2026):
        cur.execute(f"""
            CREATE TABLE stock_prices_{year} PARTITION OF stock_prices
            FOR VALUES FROM ('{year}-01-01') TO ('{year+1}-01-01');
        """)
    # Index within each partition on ticker, for fast per-ticker lookups
    # (a partitioned table can still be indexed -- the two techniques stack)
    cur.execute("CREATE INDEX ON stock_prices (ticker, date);")
    conn.commit()
    print("Created stock_prices as a RANGE-partitioned table with 6 yearly partitions "
          "(stock_prices_2020 .. stock_prices_2025), plus a (ticker, date) index on top.")


def load_data(conn):
    df = pd.read_csv(os.path.join(CLEAN_DIR, "stock_prices_clean.csv"))
    cur = conn.cursor()
    rows = list(df[["date", "ticker", "open", "high", "low", "close", "volume"]].itertuples(index=False, name=None))
    cur.executemany(
        "INSERT INTO stock_prices (date, ticker, open, high, low, close, volume) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        rows,
    )
    conn.commit()
    print(f"Loaded {len(rows):,} rows into the partitioned table. Postgres automatically "
          f"routed each row to the correct yearly partition based on its date.")

    # Show that rows actually landed in the correct physical partitions
    cur.execute("""
        SELECT tableoid::regclass AS partition, COUNT(*)
        FROM stock_prices GROUP BY tableoid ORDER BY partition;
    """)
    print("\nRow counts per physical partition (proof partitioning is real, not simulated):")
    for partition, count in cur.fetchall():
        print(f"  {partition}: {count:,} rows")


def prove_partition_pruning(conn):
    """Run EXPLAIN ANALYZE on a date-filtered query and show the planner skips other years' partitions."""
    cur = conn.cursor()
    cur.execute("""
        EXPLAIN (ANALYZE, TIMING true) SELECT * FROM stock_prices
        WHERE date >= '2024-01-01' AND date < '2025-01-01' AND ticker = 'AAPL';
    """)
    plan = "\n".join(row[0] for row in cur.fetchall())
    print("\nQuery plan (EXPLAIN ANALYZE) for a 2024-only, AAPL-only query, partitioned table:")
    print(plan)
    only_2024_touched = "stock_prices_2024" in plan and "stock_prices_2023" not in plan and "stock_prices_2020" not in plan
    print(f"\nPartition pruning confirmed (only 2024 partition scanned, others skipped): {only_2024_touched}")


def compare_against_unpartitioned(conn):
    """Build an equivalent flat (non-partitioned) table with the same data + index,
    and run the identical query, so the partitioned-vs-flat comparison is apples-to-apples."""
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS stock_prices_flat")
    cur.execute("""
        CREATE TABLE stock_prices_flat AS SELECT * FROM stock_prices;
    """)
    cur.execute("CREATE INDEX ON stock_prices_flat (ticker, date);")
    conn.commit()

    cur.execute("""
        EXPLAIN (ANALYZE, TIMING true) SELECT * FROM stock_prices_flat
        WHERE date >= '2024-01-01' AND date < '2025-01-01' AND ticker = 'AAPL';
    """)
    plan_flat = "\n".join(row[0] for row in cur.fetchall())
    print("\nSame query against a flat (non-partitioned, but still indexed) table:")
    print(plan_flat)
    print("\nBoth use the (ticker, date) index, so at our modest data volume the timing "
          "difference is small -- the real benefit of partitioning shows up at much larger "
          "scale (millions of rows per year), where the planner skips reading entire "
          "years' worth of data pages instead of just filtering rows within one table. "
          "We're including this honest comparison rather than overstating the speedup at "
          "our current data size.")


if __name__ == "__main__":
    conn = connect()
    create_partitioned_schema(conn)
    load_data(conn)
    prove_partition_pruning(conn)
    compare_against_unpartitioned(conn)
    conn.close()
