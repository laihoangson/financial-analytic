# backend/etl/fetch_data.py
# Author: Hoang Son Lai

import yfinance as yf
import pandas as pd
import os
import time
from config import TICKERS, DATA_RAW_DIR

def fetch_company_info(ticker_symbol):
    """Fetch general company information."""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    
    # Extract specific fields
    data = {
        'ticker': ticker_symbol,
        'name': info.get('longName'),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'country': info.get('country'),
        'website': info.get('website'),
        'description': info.get('longBusinessSummary'),
        'currency': info.get('currency')
    }
    return pd.DataFrame([data])

def fetch_stock_history(ticker_symbol, period="5y"):
    """Fetch historical stock prices."""
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)
    hist.reset_index(inplace=True)
    hist['Ticker'] = ticker_symbol
    return hist

def fetch_financials(ticker_symbol):
    """Fetch Income Statement, Balance Sheet, and Cash Flow."""
    t = yf.Ticker(ticker_symbol)
    
    # Get yearly financials
    inc = t.financials.T
    bal = t.balance_sheet.T
    cf = t.cashflow.T
    
    # Merge them based on Date index
    fin_df = inc.join(bal, lsuffix='_inc', rsuffix='_bal').join(cf, rsuffix='_cf')
    fin_df.reset_index(inplace=True)
    fin_df.rename(columns={'index': 'Date'}, inplace=True)
    fin_df['Ticker'] = ticker_symbol
    return fin_df

def main():
    print("--- Starting Data Fetching Process ---")
    
    all_companies = []
    all_prices = []
    all_financials = []

    for t in TICKERS:
        print(f"Fetching data for {t}...")
        try:
            # 1. Info
            all_companies.append(fetch_company_info(t))
            
            # 2. Stock Prices
            all_prices.append(fetch_stock_history(t))
            
            # 3. Financials
            all_financials.append(fetch_financials(t))
            
            time.sleep(1) # Be polite to API
        except Exception as e:
            print(f"Error fetching {t}: {e}")

    # Save Raw Data
    if all_companies:
        pd.concat(all_companies).to_csv(os.path.join(DATA_RAW_DIR, 'raw_companies.csv'), index=False)
    
    if all_prices:
        pd.concat(all_prices).to_csv(os.path.join(DATA_RAW_DIR, 'raw_prices.csv'), index=False)
    
    if all_financials:
        pd.concat(all_financials).to_csv(os.path.join(DATA_RAW_DIR, 'raw_financials.csv'), index=False)

    print(f"--- Fetching Complete. Data saved to {DATA_RAW_DIR} ---")

if __name__ == "__main__":
    main()