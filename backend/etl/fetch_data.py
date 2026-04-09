# backend/etl/fetch_data.py
# Author: Hoang Son Lai

import yfinance as yf
import pandas as pd
import os
import time
from config import TICKERS, DATA_RAW_DIR

def fetch_company_info(ticker_symbol):
    """Lấy thông tin chung bằng yFinance"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
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
    except Exception as e:
        print(f"  -> Lỗi lấy Info {ticker_symbol}: {e}")
        return pd.DataFrame()

def fetch_stock_history(ticker_symbol, period="7y"):
    """Lấy lịch sử giá bằng yFinance (Đã xử lý chống lỗi dòng rỗng)"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        hist.reset_index(inplace=True)
        
        # Bộ lọc loại bỏ những ngày dữ liệu lỗi của Yahoo
        if 'Close' in hist.columns:
            hist.dropna(subset=['Close'], inplace=True)
            
        hist['Ticker'] = ticker_symbol
        return hist
    except Exception as e:
        print(f"  -> Lỗi lấy Giá Cổ Phiếu {ticker_symbol}: {e}")
        return pd.DataFrame()

def fetch_financials(ticker_symbol):
    """Lấy Báo cáo tài chính Năm và Quý và TRẢ VỀ 2 BẢNG RIÊNG BIỆT"""
    try:
        t = yf.Ticker(ticker_symbol)
        
        # ==========================================
        # 1. XỬ LÝ BÁO CÁO NĂM (ANNUAL)
        # ==========================================
        annual_df = pd.DataFrame()
        inc_ann = t.financials.T
        bal_ann = t.balance_sheet.T
        cf_ann = t.cashflow.T
        
        if not inc_ann.empty and not bal_ann.empty and not cf_ann.empty:
            annual_df = inc_ann.join(bal_ann, lsuffix='_inc', rsuffix='_bal').join(cf_ann, rsuffix='_cf')
            annual_df.reset_index(inplace=True)
            annual_df.rename(columns={'index': 'Date'}, inplace=True)
            annual_df['Report_Period'] = 'FY' # Năm tài chính
            annual_df['Ticker'] = ticker_symbol
            
        # ==========================================
        # 2. XỬ LÝ BÁO CÁO QUÝ (QUARTERLY)
        # ==========================================
        quarterly_df = pd.DataFrame()
        inc_qtr = t.quarterly_financials.T
        bal_qtr = t.quarterly_balance_sheet.T
        cf_qtr = t.quarterly_cashflow.T
        
        if not inc_qtr.empty and not bal_qtr.empty and not cf_qtr.empty:
            quarterly_df = inc_qtr.join(bal_qtr, lsuffix='_inc', rsuffix='_bal').join(cf_qtr, rsuffix='_cf')
            quarterly_df.reset_index(inplace=True)
            quarterly_df.rename(columns={'index': 'Date'}, inplace=True)
            quarterly_df['Report_Period'] = 'Q' # Quý
            quarterly_df['Ticker'] = ticker_symbol
            
        return annual_df, quarterly_df
        
    except Exception as e:
        print(f"  -> Lỗi xử lý BCTC {ticker_symbol}: {e}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    print("--- Starting Data Fetching Process (Powered by Bulletproof yFinance) ---")
    
    all_companies = []
    all_prices = []
    all_financials_annual = []
    all_financials_quarterly = []

    for t in TICKERS:
        print(f"Fetching data for {t}...")
        try:
            # 1. Info
            all_companies.append(fetch_company_info(t))
            
            # 2. Prices
            all_prices.append(fetch_stock_history(t))
            
            # 3. Financials (Tách làm 2 mảng riêng biệt)
            ann_df, qtr_df = fetch_financials(t)
            all_financials_annual.append(ann_df)
            all_financials_quarterly.append(qtr_df)
            
            time.sleep(1)
        except Exception as e:
            print(f"LỖI TOÀN CỤC khi lấy {t}: {e}")

    # Lọc bỏ các DataFrame rỗng trước khi concat
    all_companies = [df for df in all_companies if not df.empty]
    all_prices = [df for df in all_prices if not df.empty]
    all_financials_annual = [df for df in all_financials_annual if not df.empty]
    all_financials_quarterly = [df for df in all_financials_quarterly if not df.empty]

    # Lưu 4 file CSV riêng biệt
    if all_companies:
        pd.concat(all_companies, ignore_index=True).to_csv(os.path.join(DATA_RAW_DIR, 'raw_companies.csv'), index=False)
    
    if all_prices:
        pd.concat(all_prices, ignore_index=True).to_csv(os.path.join(DATA_RAW_DIR, 'raw_prices.csv'), index=False)
    
    # LƯU FILE BÁO CÁO NĂM (Giữ nguyên tên cũ)
    if all_financials_annual:
        pd.concat(all_financials_annual, ignore_index=True).to_csv(os.path.join(DATA_RAW_DIR, 'raw_financials.csv'), index=False)

    # LƯU FILE BÁO CÁO QUÝ (File mới)
    if all_financials_quarterly:
        pd.concat(all_financials_quarterly, ignore_index=True).to_csv(os.path.join(DATA_RAW_DIR, 'raw_financials_quarterly.csv'), index=False)

    print(f"--- Fetching Complete. 4 files saved to {DATA_RAW_DIR} ---")

if __name__ == "__main__":
    main()