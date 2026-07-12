# Nexus Bank Financial Analytics Capstone — Team 4

## Team Members
 
|--------|-------------|---------|
Devabhakthuni Vijay Sai Krishna | G25AI1016 | g25ai1016@iitj.ac.in 
Divya Daiyya | G25AI1017 | g25ai1017@iitj.ac.in |
Durgesh Pandey | G25AI1018 | g25ai1018@iitj.ac.in | 
Gautam Pant | G25AI1019 | g25ai1019@iitj.ac.in |
Gundlapalli Venkata Suneel Kumar | G25AI1020 | g25ai1020@iitj.ac.in |

## Project Overview

The primary objectives of this project are:

- Build automated financial data ingestion pipelines.
- Clean and validate financial and transaction datasets.
- Engineer financial indicators and analytical features.
- Forecast stock price movements using time-series models.
- Detect fraudulent transactions using machine learning.
- Store and manage large datasets efficiently.
- Create interactive dashboards for business insights.
- Demonstrate scalable data engineering practices for banking applications.

### Key Features
## Data Engineering:

- Automated financial data acquisition
- Batch and streaming ingestion workflows
- Data quality validation
- Missing value treatment
- Duplicate removal
- Outlier detection
- Database indexing and optimization
- PostgreSQL table partitioning

## Financial Analytics:

- Moving Average (MA7, MA30)
- Exponential Moving Average (EMA12, EMA26)
- Relative Strength Index (RSI-14)
- Bollinger Bands
- Volatility Indicators
- Portfolio Risk Analysis
- Correlation Analysis

## Machine Learning
- Stock Price Forecasting
- ARIMA Time-Series Forecasting
- Walk-forward Validation
- MAE, RMSE, MAPE Evaluation

## Fraud Detection

- Logistic Regression
- Random Forest Classification
- Precision
- Recall
- F1 Score
- ROC-AUC Evaluation

## Dashboard & Visualization

- Interactive Plotly Dashboard
- Stock Price Trends
- Risk Heatmaps
- Volatility Analysis
- Fraud Activity Timeline
- Portfolio Analytics

### Technologies Used
## Programming:
- Python
- SQL

## Libraries:
- Pandas
- NumPy
- Scikit-Learn
- Statsmodels
- Plotly
- yfinance
- Matplotlib
- Seaborn

## Database
- SQLite
- PostgreSQL

## Tools
- Git
- GitHub
- Jupyter Notebook

## Solution Architecture

Data Sources
│
├── Yahoo Finance
├── FRED
├── Kaggle Fraud Dataset
│
▼
Data Acquisition Layer
│
▼
Data Cleaning & Validation
│
▼
Feature Engineering
│
├── Moving Averages
├── RSI
├── Volatility
├── Bollinger Bands
├── EMA Indicators
│
▼
Database Storage
│
├── SQLite
└── PostgreSQL Partitioning
│
▼
Machine Learning Models
│
├── ARIMA Forecasting
├── Logistic Regression
└── Random Forest
│
▼
Analytics Dashboard
│
▼
Business Insights & Recommendations

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


## Business Impact:
This solution demonstrates how modern data engineering and machine learning techniques can be leveraged by financial institutions to
- Improve portfolio monitoring
- Enhance fraud detection capabilities
- Support risk management
- Automate financial analytics workflows
- Enable data-driven decision-making
The project provides a scalable foundation for future banking analytics initiatives.

## Future Enhancements:
- LSTM-based stock forecasting
- Real-time streaming analytics
- Streamlit-based live dashboard
- Advanced fraud detection models
- Cloud-native deployment
- MLOps pipeline automation
- Enterprise-scale data lake integration