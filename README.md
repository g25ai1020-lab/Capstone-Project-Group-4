# Nexus Bank Financial Analytics Capstone — Team 4

## Run order (scripts/ folder):
1. 01_data_acquisition.py        (--mode sample | --mode live) -- now includes FX rates
2. 02_data_cleaning.py            -- now cleans FX rates too
3. 02b_eda.py                     (exploratory data analysis)
4. 03_pipeline_storage.py         (SQLite batch loader + indexes)
5. 03a_streaming_ingestion.py     (NEW: append-only streaming ingestion demo)
6. 03b_postgres_partitioning.py   (NEW: real PostgreSQL RANGE partitioning + proof)
7. 04_feature_engineering.py
8. 05_modeling_forecasting.py
9. 06_modeling_fraud.py
10. 07_visualization.py            (static charts)
11. 07b_interactive_dashboard.py   (interactive Plotly dashboard)

## What changed in this update
- **FX rates added**: EURUSD, GBPUSD, USDJPY, sourced and cleaned the same way as stock prices
  (brief explicitly asks for "stock prices, FX rates").
- **Streaming vs batch, genuinely separated**: 03a_streaming_ingestion.py is a real append-only
  polling loop (streaming_ticks table), distinct from the batch loader which replaces whole tables.
- **Real database partitioning**: 03b_postgres_partitioning.py builds actual PostgreSQL
  `PARTITION BY RANGE (date)` tables (one per year) — not just a SQLite index. Proof is in
  evidence/postgres_partitioning_proof.txt: shows real per-partition row counts and an
  EXPLAIN ANALYZE query plan confirming partition pruning (only the matching year's partition
  is scanned).
- Requires a running PostgreSQL instance — see script docstring for connection setup
  (`CREATE USER`, `CREATE DATABASE`, install psycopg2-binary).

## Key outputs
- data/clean/                          -> cleaned datasets, including fx_rates_clean.csv
- db/nexus_bank.db                     -> SQLite warehouse (batch + streaming tables)
- evidence/postgres_partitioning_proof.txt -> real partitioning proof (query plans, row counts)
- charts/                              -> 10 static PNG charts (6 core + 4 EDA)
- dashboard/nexus_bank_dashboard.html  -> open directly in any browser; interactive

## Before submitting
- [ ] Push this folder to a GitHub repo and add the URL to the report
- [ ] Run 01_data_acquisition.py --mode live if possible and update metrics
- [ ] Fill in the report's screenshot placeholders
- [ ] Ask Claude to update the report text (Sections 4, 7) to reflect FX/streaming/partitioning
