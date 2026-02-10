# backend/etl/load_to_mysql.py
# Author: Hoang Son Lai

import pandas as pd
import numpy as np  
import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config import DATA_CLEANED_DIR, DB_CONFIG

def get_db_engine():
    # 1. Encode password
    raw_pass = str(DB_CONFIG['password'])
    encoded_password = quote_plus(raw_pass)
    
    # 2. Connection string
    conn_str = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(conn_str)

def load_data():
    engine = get_db_engine()
    
    # --- 1. Load Companies ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'companies.csv')
        if os.path.exists(path):
            df_comp = pd.read_csv(path)
            df_comp = df_comp.where(pd.notnull(df_comp), None)
            
            print(f"Loading {len(df_comp)} companies...")
            with engine.connect() as conn:
                data_to_insert = df_comp.to_dict(orient='records')
                
                sql = text("""
                    INSERT INTO companies (ticker, name, sector, industry, country, website, description, currency)
                    VALUES (:ticker, :name, :sector, :industry, :country, :website, :description, :currency)
                    ON DUPLICATE KEY UPDATE 
                        name=VALUES(name), description=VALUES(description), last_updated=NOW();
                """)
                # Execute many (Batch insert)
                conn.execute(sql, data_to_insert)
                conn.commit()
            print("Companies loaded.")
        else:
            print("Skipping Companies: File not found.")
    except Exception as e:
        print(f"Error loading companies: {e}")

    # --- 2. Load Stock Prices  ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'stock_prices.csv')
        if os.path.exists(path):
            df_prices = pd.read_csv(path)
            # Xử lý NaN thành None
            df_prices = df_prices.where(pd.notnull(df_prices), None)
            
            print(f"Loading {len(df_prices)} stock price records...")
            
            with engine.connect() as conn:
                chunk_size = 2000 
                total_inserted = 0
                
                # Câu lệnh SQL INSERT IGNORE:
                # - Nếu trùng (ticker + date): BỎ QUA (Giữ nguyên data cũ)
                # - Nếu chưa có: THÊM MỚI
                sql = text("""
                    INSERT IGNORE INTO stock_prices (ticker, date, open, high, low, close, adj_close, volume)
                    VALUES (:ticker, :date, :open, :high, :low, :close, :adj_close, :volume)
                """)

                for i in range(0, len(df_prices), chunk_size):
                    chunk = df_prices.iloc[i:i+chunk_size]
                    
                    chunk_data = chunk.to_dict(orient='records')
                    
                    conn.execute(sql, chunk_data)
                    conn.commit() # Commit sau mỗi chunk để tránh tràn bộ nhớ DB
                    total_inserted += len(chunk)
                    print(f"Processed {total_inserted}/{len(df_prices)} rows...", end='\r')
                    
            print("\nStock prices loaded successfully (New records added, old records preserved).")
        else:
             print("Skipping Prices: File not found.")
    except Exception as e:
        print(f"Error loading prices: {e}")

    # --- 3. Load Financial Statements ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'financial_statements.csv')
        if os.path.exists(path):
            df_fin = pd.read_csv(path)

            df_fin.replace([np.inf, -np.inf], np.nan, inplace=True)
            df_fin = df_fin.astype(object)
            df_fin = df_fin.where(pd.notnull(df_fin), None)

            print(f"Loading {len(df_fin)} financial records...")

            with engine.connect() as conn:
                cols = ', '.join(df_fin.columns)
                vals = ', '.join([f':{c}' for c in df_fin.columns])

                update_clause = ', '.join(
                    [f"{c}=VALUES({c})" for c in df_fin.columns if c != 'id']
                )

                sql = text(f"""
                    INSERT INTO financial_statements ({cols})
                    VALUES ({vals})
                    ON DUPLICATE KEY UPDATE
                        {update_clause}
                """)

                data = df_fin.to_dict(orient='records')

                cleaned_data = [
                    {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in row.items()}
                    for row in data
                ]

                conn.execute(sql, cleaned_data)
                conn.commit()

            print("Financials loaded (inserted + updated).")
        else:
            print("Skipping Financials: File not found.")

    except Exception as e:
        print(f"Error loading financials: {e}")

def main():
    print("--- Starting Database Load ---")
    load_data()
    print("--- Database Load Complete ---")


if __name__ == "__main__":
    main()