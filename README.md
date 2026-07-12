# Nexus Bank Financial Analytics Capstone — Team 4

## Team Members4 5| Name | Roll Number | Email 
|--------|-------------|---------|
Devabhakthuni Vijay Sai Krishna | G25AI1016 | g25ai1016@iitj.ac.in 
Divya Daiyya | G25AI1017 | g25ai1017@iitj.ac.in |
Durgesh Pandey | G25AI1018 | g25ai1018@iitj.ac.in | 
Gautam Pant | G25AI1019 | g25ai1019@iitj.ac.in |
Gundlapalli Venkata Suneel Kumar | G25AI1020 | g25ai1020@iitj.ac.in |

## Project Overview
**Financial Analytics and Modeling Project for Nexus Bank** is an end-to-end financial data engineering and analytics platform developed as part of a capstone project. The solution focuses on building scalable data pipelines for collecting, processing, storing, and analyzing large-scale financial and transactional datasets.16 17The project simulates a real-world banking analytics environment, enabling portfolio analysis, financial modeling, and fraud detection through modern data engineering practices and machine learning techniques.18 19### Key Features20 21- Data ingestion from stock market, cryptocurrency, and macroeconomic data sources22- Financial transaction data processing and fraud analysis23- Data cleaning, normalization, and validation24- Automated ETL/ELT pipelines25- Financial indicator computation (RSI, Moving Average, MACD, Volatility, Bollinger Bands)26- Portfolio performance analysis27- Fraud detection and anomaly identification28- Database partitioning and optimized storage strategies29- Automated reporting and workflow orchestration30 31### Technologies Used32 33- Python34- Pandas35- NumPy36- Scikit-Learn37- Apache Spark (if applicable)38- SQL39- PostgreSQL/MySQL40- Yahoo Finance API41- Kaggle Datasets42- Jupyter Notebook43- Git & GitHub

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
