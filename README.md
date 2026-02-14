# Global Market Insight - Financial Analytics Platform

A comprehensive, automated financial analytics platform designed to extract, process, and visualize market data for 21 major global companies across 6 key sectors. This project integrates an automated ETL pipeline, interactive dashboards, advanced SQL analytics, and machine learning-driven forecasting.

**Author:** Hoang Son Lai

Website: https://laihoangson.github.io/financial-analytic/

## 🌟 Key Features

* **Automated ETL Pipeline:** Daily data extraction and transformation using Python and the `yfinance` API, orchestrated by GitHub Actions.
* **Interactive Dashboards:** Daily-updated visualizations powered by Javascript, allowing users to filter by metrics like Revenue, Net Income, and compare global market performance or dive deep into individual company fundamentals.
* **Predictive Analytics & Reports:** In-depth stock price trend forecasting integrating Technical Analysis, Quantitative Analysis, and Machine Learning models (XGBoost, Scikit-Learn).
* **Advanced SQL Analytics:** A robust MySQL database schema supporting complex financial queries, including fundamental analysis, sector comparisons, and market valuation metrics (e.g., P/E ratios, Volatility, Moving Averages).
* **CI/CD Automation:** Scheduled workflows ensuring data is refreshed daily at 06:00 AM (GMT+7) automatically.

---

## 📂 Basic Folder Structure

```text
financial-analytic/
├── .github/
│   └── workflows/
│       └── daily_etl.yml          # GitHub Actions CI/CD pipeline script
├── assets/
│   └── css/
│       └── styles.css             # Main styling for the web interface
├── backend/
│   ├── etl/
│   │   ├── fetch_data.py          # Extracts raw data via yFinance API
│   │   ├── clean_data.py          # Cleans data & calculates 15+ financial ratios
│   │   └── load_to_mysql.py       # Safely upserts processed data to MySQL
│   └── sql/
│       ├── schema.sql             # Database schema and table definitions
│       ├── analysis_queries.sql   # Queries to answer business questions
├── dashboard/
│   ├── global_dashboard.html      # Global market interactive dashboard
│   └── company_dashboard.html     # Deep-dive company interactive dashboard
├── data/
│   ├── cleaned/                   # Final datasets powering daily dashboard updates
│   │   ├── companies.csv
│   │   ├── financial_statements.csv
│   │   └── stock_prices.csv
│   ├── raw/                       # Raw, unprocessed data straight from the API
│   │   ├── raw_companies.csv
│   │   ├── raw_financials.csv
│   │   └── raw_prices.csv
│   └── query_data/
│       ├── result1.csv            # Pre-generated SQL query results for the frontend
│       └── ...                    # (result1.csv through result8.csv)
├── reports/
│   ├── ml_report.html             # Full Machine Learning forecasting report
│   └── world.jpg                  # Asset images for the reports section
├── about.html                     # Author portfolio and contact info
├── dashboard.html                 # Dashboards overview page
├── index.html                     # Main landing page
├── pipeline.html                  # ETL Architecture documentation page
├── reports.html                   # Analytical reports landing page
└── sql.html                       # SQL schema and interactive queries page
```

---

## 🏗️ Data Architecture & ETL Pipeline

The platform's data architecture is built for resilience and accuracy, dividing "Live" data for dashboards and "Static" snapshot data for deep-dive reporting.

1.  **Data Extraction (`fetch_data.py`):** Pulls 5 years of historical OHLCV data, financial statements (Income, Balance Sheet, Cash Flow), and company metadata using the yFinance API.
2.  **Data Transformation (`clean_data.py`):** Cleans the raw data and automatically computes over 15 financial ratios (ROE, ROA, Debt-to-Equity, Current Ratio, etc.).
3.  **Database Loading (`load_to_mysql.py`):** Safely upserts processed data into a MySQL database via SQLAlchemy using chunked batch processing.
4.  **Automation (`daily_etl.yml`):** GitHub Actions triggers the pipeline daily, pushing fresh CSV data to the frontend and updating the database.

---

## 💻 Technology Stack

* **Data Engineering & Machine Learning:** Python, Pandas, SQLAlchemy, Scikit-Learn, XGBoost, yFinance API
* **Database:** MySQL
* **Frontend, Dashboard & UI:** HTML5, CSS3, JavaScript
* **DevOps & Automation:** GitHub Actions

---

## 🗄️ Database Schema

The `financial_analytics` database is structured to support comprehensive fundamental and technical analysis:

* `companies`: Stores company metadata (ticker, name, sector, industry, country, currency).
* `stock_prices`: Contains daily historical trading data (open, high, low, close, adj_close, volume).
* `financial_statements`: Houses comprehensive yearly/quarterly reports and 30+ pre-calculated financial ratios (liquidity, profitability, solvency).

---

## 📊 Tracked Companies by Sector

The platform currently tracks 21 major global market leaders:
* **Technology:** AAPL, MSFT, GOOGL, NVDA, ADBE, META
* **Financial Services:** JPM, V, MA, PYPL, BAC
* **Healthcare:** JNJ, UNH
* **Consumer Cyclical:** TSLA, HD, AMZN
* **Consumer Defensive:** KO, PG, WMT
* **Entertainment:** DIS, NFLX

---

