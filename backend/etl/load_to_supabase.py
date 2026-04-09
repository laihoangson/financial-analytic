# backend/etl/load_to_supabase.py
# Author: Hoang Son Lai

import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config import DATA_CLEANED_DIR, SUPABASE_DB_CONFIG

def get_supabase_engine():
    # 1. Encode password cho an toàn
    raw_pass = str(SUPABASE_DB_CONFIG['password'])
    encoded_password = quote_plus(raw_pass)
    
    # 2. Connection string dùng driver postgresql+psycopg2
    conn_str = f"postgresql+psycopg2://{SUPABASE_DB_CONFIG['user']}:{encoded_password}@{SUPABASE_DB_CONFIG['host']}:{SUPABASE_DB_CONFIG['port']}/{SUPABASE_DB_CONFIG['database']}"
    return create_engine(conn_str)

def load_data():
    engine = get_supabase_engine()
    
    # --- 1. Load Companies ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'companies.csv')
        if os.path.exists(path):
            df_comp = pd.read_csv(path)
            df_comp = df_comp.where(pd.notnull(df_comp), None)
            
            print(f"[Supabase] Loading {len(df_comp)} companies...")
            with engine.connect() as conn:
                data_to_insert = df_comp.to_dict(orient='records')
                
                # PostgreSQL dùng ON CONFLICT thay cho ON DUPLICATE KEY UPDATE
                sql = text("""
                    INSERT INTO companies (ticker, name, sector, industry, country, website, description, currency)
                    VALUES (:ticker, :name, :sector, :industry, :country, :website, :description, :currency)
                    ON CONFLICT (ticker) DO UPDATE SET 
                        name=EXCLUDED.name, 
                        description=EXCLUDED.description, 
                        last_updated=NOW();
                """)
                conn.execute(sql, data_to_insert)
                conn.commit()
            print("[Supabase] Companies loaded.")
        else:
            print("[Supabase] Skipping Companies: File not found.")
    except Exception as e:
        print(f"[Supabase] Error loading companies: {e}")

    # --- 2. Load Stock Prices ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'stock_prices.csv')
        if os.path.exists(path):
            df_prices = pd.read_csv(path)
            df_prices = df_prices.where(pd.notnull(df_prices), None)
            
            print(f"[Supabase] Loading {len(df_prices)} stock price records...")
            
            with engine.connect() as conn:
                chunk_size = 500 
                total_inserted = 0
                
                # PostgreSQL use DO NOTHING instead of INSERT IGNORE
                sql = text("""
                    INSERT INTO stock_prices (ticker, date, open, high, low, close, adj_close, volume)
                    VALUES (:ticker, :date, :open, :high, :low, :close, :adj_close, :volume)
                    ON CONFLICT (ticker, date) DO NOTHING;
                """)

                for i in range(0, len(df_prices), chunk_size):
                    chunk = df_prices.iloc[i:i+chunk_size]
                    chunk_data = chunk.to_dict(orient='records')
                    
                    conn.execute(sql, chunk_data)
                    conn.commit() 
                    total_inserted += len(chunk)
                    print(f"[Supabase] Processed {total_inserted}/{len(df_prices)} rows...", end='\r')
                    
            print("\n[Supabase] Stock prices loaded successfully.")
        else:
             print("[Supabase] Skipping Prices: File not found.")
    except Exception as e:
        print(f"[Supabase] Error loading prices: {e}")

    # --- 3. Load Financial Statements ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'financial_statements.csv')
        if os.path.exists(path):
            df_fin = pd.read_csv(path)

            df_fin.replace([np.inf, -np.inf], np.nan, inplace=True)
            df_fin = df_fin.astype(object)
            df_fin = df_fin.where(pd.notnull(df_fin), None)

            print(f"[Supabase] Loading {len(df_fin)} financial records...")

            with engine.connect() as conn:
                cols = ', '.join(df_fin.columns)
                vals = ', '.join([f':{c}' for c in df_fin.columns])

                # Tạo chuỗi update tự động cho PostgreSQL (dùng EXCLUDED.)
                # ĐÃ THÊM 'period' vào danh sách không update
                update_clause = ', '.join(
                    [f"{c}=EXCLUDED.{c}" for c in df_fin.columns if c not in ['id', 'ticker', 'report_date', 'period']]
                )

                # ĐÃ THÊM 'period' VÀO ON CONFLICT ĐỂ TRÁNH LỖI KEY
                sql = text(f"""
                    INSERT INTO financial_statements ({cols})
                    VALUES ({vals})
                    ON CONFLICT (ticker, report_date, period) DO UPDATE SET
                        {update_clause};
                """)

                data = df_fin.to_dict(orient='records')
                cleaned_data = [
                    {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in row.items()}
                    for row in data
                ]

                conn.execute(sql, cleaned_data)
                conn.commit()

            print("[Supabase] Financials loaded.")
        else:
            print("[Supabase] Skipping Financials: File not found.")

    except Exception as e:
        print(f"[Supabase] Error loading financials: {e}")

def main():
    print("--- Starting Database Load (Supabase) ---")
    load_data()
    print("--- Supabase Load Complete ---")

if __name__ == "__main__":
    main()