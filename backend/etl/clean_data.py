# backend/etl/clean_data.py
# Author: Hoang Son Lai

import pandas as pd
import numpy as np
import os
from config import DATA_RAW_DIR, DATA_CLEANED_DIR

def clean_companies():
    """Clean company info data."""
    path = os.path.join(DATA_RAW_DIR, 'raw_companies.csv')
    if not os.path.exists(path):
        print(f"Skipping companies: {path} not found.")
        return

    df = pd.read_csv(path)
    df = df.drop_duplicates(subset=['ticker'])
    df.fillna({'website': '', 'description': ''}, inplace=True)
    
    output_path = os.path.join(DATA_CLEANED_DIR, 'companies.csv')
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

def clean_prices():
    """Clean stock price data."""
    path = os.path.join(DATA_RAW_DIR, 'raw_prices.csv')
    if not os.path.exists(path):
        print(f"Skipping prices: {path} not found.")
        return

    df = pd.read_csv(path)
    
    # Standardize columns
    cols_map = {
        'Date': 'date', 'Open': 'open', 'High': 'high', 
        'Low': 'low', 'Close': 'close', 'Volume': 'volume', 
        'Ticker': 'ticker'
    }
    df.rename(columns=cols_map, inplace=True)
    
    if 'adj_close' not in df.columns:
        df['adj_close'] = df['close']
        
    # --- FIX: Thêm utc=True để xử lý múi giờ ---
    df['date'] = pd.to_datetime(df['date'], utc=True).dt.date
    
    # Select only needed columns
    final_cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
    df = df[final_cols].dropna(subset=['ticker', 'date'])
    
    output_path = os.path.join(DATA_CLEANED_DIR, 'stock_prices.csv')
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

def clean_financials():
    """Clean financials and calculate metrics."""
    path = os.path.join(DATA_RAW_DIR, 'raw_financials.csv')
    if not os.path.exists(path):
        print(f"Skipping financials: {path} not found.")
        return

    df = pd.read_csv(path)
    
    # Helper to safe get column
    def get_col(col_name):
        return df[col_name] if col_name in df.columns else 0

    # 1. Mapping yfinance keys to Schema
    df['revenue'] = get_col('Total Revenue')
    df['cogs'] = get_col('Cost Of Revenue')
    df['gross_profit'] = get_col('Gross Profit')
    df['opex'] = get_col('Total Operating Expenses')
    df['operating_income_ebit'] = get_col('Operating Income')
    df['ebt'] = get_col('Pretax Income')
    df['net_income'] = get_col('Net Income')
    df['ebitda'] = get_col('EBITDA')
    df['basic_eps'] = get_col('Basic EPS')
    df['diluted_eps'] = get_col('Diluted EPS')
    
    df['total_assets'] = get_col('Total Assets')
    df['current_assets'] = get_col('Current Assets')
    df['cash_and_equivalents'] = get_col('Cash And Cash Equivalents')
    df['accounts_receivable'] = get_col('Net Receivables')
    df['inventory'] = get_col('Inventory')
    df['non_current_assets'] = df['total_assets'] - df['current_assets']
    
    df['total_liabilities'] = get_col('Total Liabilities Net Minority Interest')
    df['current_liabilities'] = get_col('Current Liabilities')
    df['accounts_payable'] = get_col('Accounts Payable')
    df['short_term_debt'] = get_col('Current Debt')
    df['long_term_debt'] = get_col('Long Term Debt')
    
    df['total_equity'] = get_col('Stockholders Equity')
    df['common_stock'] = get_col('Common Stock')
    df['retained_earnings'] = get_col('Retained Earnings')

    interest_expense = get_col('Interest Expense')
    
    # 2. Calculating Ratios
    # Replace 0 with NaN to avoid division by zero errors
    df['current_ratio'] = df['current_assets'] / df['current_liabilities'].replace(0, np.nan)
    df['quick_ratio'] = (df['current_assets'] - df['inventory']) / df['current_liabilities'].replace(0, np.nan)
    df['cash_ratio'] = df['cash_and_equivalents'] / df['current_liabilities'].replace(0, np.nan)
    
    df['debt_to_equity'] = df['total_liabilities'] / df['total_equity'].replace(0, np.nan)
    df['debt_ratio'] = df['total_liabilities'] / df['total_assets'].replace(0, np.nan)
    df['interest_coverage_ratio'] = df['operating_income_ebit'] / interest_expense.replace(0, np.nan)
    
    df['roa'] = df['net_income'] / df['total_assets'].replace(0, np.nan)
    df['roe'] = df['net_income'] / df['total_equity'].replace(0, np.nan)
    df['gross_margin'] = df['gross_profit'] / df['revenue'].replace(0, np.nan)
    df['net_margin'] = df['net_income'] / df['revenue'].replace(0, np.nan)
    
    df['asset_turnover'] = df['revenue'] / df['total_assets'].replace(0, np.nan)
    df['inventory_turnover'] = df['cogs'] / df['inventory'].replace(0, np.nan)
    df['receivables_turnover'] = df['revenue'] / df['accounts_receivable'].replace(0, np.nan)

    # 3. Formatting
    # --- FIX: Thêm utc=True ở đây nữa ---
    df['report_date'] = pd.to_datetime(df['Date'], utc=True).dt.date
    
    df['period'] = '12M'
    df.rename(columns={'Ticker': 'ticker'}, inplace=True)
    
    schema_cols = [
        'ticker', 'report_date', 'period',
        'revenue', 'cogs', 'gross_profit', 'opex', 'operating_income_ebit',
        'ebt', 'net_income', 'ebitda', 'basic_eps', 'diluted_eps',
        'total_assets', 'current_assets', 'cash_and_equivalents', 'accounts_receivable',
        'inventory', 'non_current_assets', 'total_liabilities', 'current_liabilities',
        'accounts_payable', 'short_term_debt', 'long_term_debt', 'total_equity',
        'common_stock', 'retained_earnings',
        'current_ratio', 'quick_ratio', 'cash_ratio', 'debt_to_equity',
        'debt_ratio', 'interest_coverage_ratio', 'roa', 'roe',
        'gross_margin', 'net_margin', 'asset_turnover', 'inventory_turnover', 'receivables_turnover'
    ]
    
    # Filter columns that actually exist
    existing_cols = [col for col in schema_cols if col in df.columns]
    df_final = df[existing_cols].copy()
    
    output_path = os.path.join(DATA_CLEANED_DIR, 'financial_statements.csv')
    df_final.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

def main():
    print("--- Starting Data Cleaning Process ---")
    clean_companies()
    clean_prices()
    clean_financials()
    print("--- Cleaning Complete ---")

if __name__ == "__main__":
    main()