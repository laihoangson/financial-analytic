-- Author: Hoang Son Lai
-- Description: Analytical SQL queries for financial data analysis

USE financial_analytics;

-- =======================================================
-- SECTION 1: FUNDAMENTAL ANALYSIS 
-- =======================================================

-- 1. Top 10 Companies by Revenue (Most Recent Year)
WITH LatestFinancials AS (
    SELECT 
        f1.*,
        ROW_NUMBER() OVER (PARTITION BY f1.ticker ORDER BY f1.report_date DESC) as rn
    FROM financial_statements f1
    WHERE f1.revenue IS NOT NULL AND f1.revenue > 0
)
SELECT 
    c.name, 
    c.sector, 
    f.report_date, 
    FORMAT(f.revenue, 0) as revenue, 
    FORMAT(f.net_income, 0) as net_income
FROM LatestFinancials f
JOIN companies c ON f.ticker = c.ticker
WHERE f.rn = 1
ORDER BY f.revenue DESC
LIMIT 10;

-- 2. Profitability Leaders: Highest Net Profit Margin (Most Recent Year)
WITH LatestFinancials AS (
    SELECT 
        f1.*,
        ROW_NUMBER() OVER (PARTITION BY f1.ticker ORDER BY f1.report_date DESC) as rn
    FROM financial_statements f1
    WHERE f1.revenue > 0
)
SELECT 
    c.ticker, 
    c.name, 
    f.report_date,
    ROUND(f.net_margin * 100, 2) as net_margin_percent,
    ROUND(f.gross_margin * 100, 2) as gross_margin_percent
FROM LatestFinancials f
JOIN companies c ON f.ticker = c.ticker
WHERE f.rn = 1
ORDER BY f.net_margin DESC
LIMIT 10;

-- 3. Financial Health: Companies with High Debt Risk (Most Recent Year)
WITH LatestFinancials AS (
    SELECT 
        f1.*,
        ROW_NUMBER() OVER (PARTITION BY f1.ticker ORDER BY f1.report_date DESC) as rn
    FROM financial_statements f1
    WHERE f1.debt_to_equity IS NOT NULL
)
SELECT 
    c.name, 
    c.industry, 
    f.debt_to_equity,
    f.current_ratio,
    f.interest_coverage_ratio,
    f.report_date
FROM LatestFinancials f
JOIN companies c ON f.ticker = c.ticker
WHERE f.rn = 1 AND f.debt_to_equity > 2
ORDER BY f.debt_to_equity DESC;

-- 4. Efficient Operations: Best Return on Equity (ROE) & ROA (Most Recent Year)
WITH LatestFinancials AS (
    SELECT 
        f1.*,
        ROW_NUMBER() OVER (PARTITION BY f1.ticker ORDER BY f1.report_date DESC) as rn
    FROM financial_statements f1
    WHERE f1.roe IS NOT NULL
)
SELECT 
    c.ticker,
    c.name,
    f.report_date,
    ROUND(f.roe * 100, 2) as roe_percent,
    ROUND(f.roa * 100, 2) as roa_percent
FROM LatestFinancials f
JOIN companies c ON f.ticker = c.ticker
WHERE f.rn = 1
ORDER BY f.roe DESC
LIMIT 10;

-- =======================================================
-- SECTION 2: SECTOR ANALYSIS 
-- =======================================================

-- 5. Average Profit Margin by Sector (Most Recent Year)
WITH LatestFinancials AS (
    SELECT 
        f1.*,
        ROW_NUMBER() OVER (PARTITION BY f1.ticker ORDER BY f1.report_date DESC) as rn
    FROM financial_statements f1
    WHERE f1.revenue > 0
),
LatestCompanyData AS (
    SELECT 
        c.sector,
        f.ticker,
        f.net_margin,
        f.roe,
        f.report_date
    FROM LatestFinancials f
    JOIN companies c ON f.ticker = c.ticker
    WHERE f.rn = 1
)
SELECT 
    sector,
    COUNT(DISTINCT ticker) as company_count,
    ROUND(AVG(net_margin) * 100, 2) as avg_net_margin_percent,
    ROUND(AVG(roe) * 100, 2) as avg_roe_percent,
    MAX(report_date) as latest_report_date
FROM LatestCompanyData
GROUP BY sector
ORDER BY avg_net_margin_percent DESC;

-- =======================================================
-- SECTION 3: MARKET ANALYSIS & VALUATION
-- =======================================================

-- 6. Calculate P/E Ratio (Price-to-Earnings) manually
WITH LatestPrice AS (
    -- Get the most recent closing price for each ticker
    SELECT ticker, close as latest_price, date
    FROM stock_prices
    WHERE date = (SELECT MAX(date) FROM stock_prices)
),
LatestEPS AS (
    -- Get the most recent EPS
    SELECT ticker, basic_eps, report_date
    FROM financial_statements
    WHERE (ticker, report_date) IN (
        SELECT ticker, MAX(report_date) 
        FROM financial_statements 
        GROUP BY ticker
    )
)
SELECT 
    lp.ticker,
    lp.latest_price,
    le.basic_eps,
    ROUND(lp.latest_price / NULLIF(le.basic_eps, 0), 2) as PE_Ratio
FROM LatestPrice lp
JOIN LatestEPS le ON lp.ticker = le.ticker
ORDER BY PE_Ratio ASC; 

-- 7. Stock Volatility 
-- Calculate Standard Deviation of close price
SELECT 
    ticker,
    ROUND(AVG(close), 2) as avg_price,
    ROUND(STDDEV(close), 2) as price_volatility,
    MIN(close) as min_price_period,
    MAX(close) as max_price_period
FROM stock_prices
GROUP BY ticker
ORDER BY price_volatility DESC;

-- 8. Moving Average for Apple (Calculating 30-Day Moving Average)
SELECT 
    ticker,
    date,
    close,
    AVG(close) OVER (
        PARTITION BY ticker 
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as MA_30
FROM stock_prices
WHERE ticker = 'AAPL' 
ORDER BY date DESC
LIMIT 100;