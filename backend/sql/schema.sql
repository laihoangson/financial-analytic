-- backend/sql/schema.sql
-- Project: Global Market Insight 360
-- Author: Hoang Son Lai

CREATE DATABASE IF NOT EXISTS financial_analytics;
USE financial_analytics;

-- 1. Table: Company Information
CREATE TABLE IF NOT EXISTS companies (
    ticker VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    country VARCHAR(100),
    website VARCHAR(255),
    description TEXT,
    currency VARCHAR(10),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Table: Stock Prices (Daily)
CREATE TABLE IF NOT EXISTS stock_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10),
    date DATE,
    open DECIMAL(15, 4),
    high DECIMAL(15, 4),
    low DECIMAL(15, 4),
    close DECIMAL(15, 4),
    adj_close DECIMAL(15, 4),
    volume BIGINT,
    FOREIGN KEY (ticker) REFERENCES companies(ticker) ON DELETE CASCADE,
    UNIQUE KEY unique_stock (ticker, date)
);

-- 3. Table: Financial Statements (Yearly/Quarterly) & Calculated Ratios
CREATE TABLE IF NOT EXISTS financial_statements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10),
    report_date DATE,
    period VARCHAR(20), -- '12M' for Yearly, 'TTM' or '3M'

    -- Income Statement
    revenue DECIMAL(20, 2),
    cogs DECIMAL(20, 2),
    gross_profit DECIMAL(20, 2),
    opex DECIMAL(20, 2),
    operating_income_ebit DECIMAL(20, 2),
    ebt DECIMAL(20, 2),
    net_income DECIMAL(20, 2),
    ebitda DECIMAL(20, 2),
    basic_eps DECIMAL(10, 4),
    diluted_eps DECIMAL(10, 4),

    -- Balance Sheet
    total_assets DECIMAL(20, 2),
    current_assets DECIMAL(20, 2),
    cash_and_equivalents DECIMAL(20, 2),
    accounts_receivable DECIMAL(20, 2),
    inventory DECIMAL(20, 2),
    non_current_assets DECIMAL(20, 2),
    total_liabilities DECIMAL(20, 2),
    current_liabilities DECIMAL(20, 2),
    accounts_payable DECIMAL(20, 2),
    short_term_debt DECIMAL(20, 2),
    long_term_debt DECIMAL(20, 2),
    total_equity DECIMAL(20, 2),
    common_stock DECIMAL(20, 2),
    retained_earnings DECIMAL(20, 2),

    -- Calculated Ratios
    current_ratio DECIMAL(10, 4),
    quick_ratio DECIMAL(10, 4),
    cash_ratio DECIMAL(10, 4),
    debt_to_equity DECIMAL(10, 4),
    debt_ratio DECIMAL(10, 4),
    interest_coverage_ratio DECIMAL(10, 4),
    roa DECIMAL(10, 4),
    roe DECIMAL(10, 4),
    gross_margin DECIMAL(10, 4),
    net_margin DECIMAL(10, 4),
    asset_turnover DECIMAL(10, 4),
    inventory_turnover DECIMAL(10, 4),
    receivables_turnover DECIMAL(10, 4),

    FOREIGN KEY (ticker) REFERENCES companies(ticker) ON DELETE CASCADE,
    UNIQUE KEY unique_financial (ticker, report_date)
);