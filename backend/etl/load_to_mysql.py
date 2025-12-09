# backend/etl/load_to_mysql.py
# Author: Hoang Son Lai

import pandas as pd
import numpy as np  # <--- Cần thêm thư viện này
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
            # Replace NaN with None
            df_comp = df_comp.where(pd.notnull(df_comp), None)
            
            print(f"Loading {len(df_comp)} companies...")
            with engine.connect() as conn:
                for _, row in df_comp.iterrows():
                    row_data = row.to_dict()
                    sql = text("""
                        INSERT INTO companies (ticker, name, sector, industry, country, website, description, currency)
                        VALUES (:ticker, :name, :sector, :industry, :country, :website, :description, :currency)
                        ON DUPLICATE KEY UPDATE 
                            name=VALUES(name), description=VALUES(description), last_updated=NOW();
                    """)
                    conn.execute(sql, row_data)
                conn.commit()
            print("Companies loaded.")
        else:
            print("Skipping Companies: File not found.")
    except Exception as e:
        print(f"Error loading companies: {e}")

    # --- 2. Load Stock Prices ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'stock_prices.csv')
        if os.path.exists(path):
            df_prices = pd.read_csv(path)
            # Replace NaN with None
            df_prices = df_prices.where(pd.notnull(df_prices), None)
            
            print(f"Loading {len(df_prices)} stock price records...")
            with engine.connect() as conn:
                chunk_size = 1000
                for i in range(0, len(df_prices), chunk_size):
                    chunk = df_prices.iloc[i:i+chunk_size]
                    for _, row in chunk.iterrows():
                         row_data = row.to_dict()
                         sql = text("""
                            INSERT IGNORE INTO stock_prices (ticker, date, open, high, low, close, adj_close, volume)
                            VALUES (:ticker, :date, :open, :high, :low, :close, :adj_close, :volume)
                        """)
                         conn.execute(sql, row_data)
                    conn.commit()
            print("Stock prices loaded.")
        else:
             print("Skipping Prices: File not found.")
    except Exception as e:
        print(f"Error loading prices: {e}")

    # --- 3. Load Financial Statements ---
    try:
        path = os.path.join(DATA_CLEANED_DIR, 'financial_statements.csv')
        if os.path.exists(path):
            df_fin = pd.read_csv(path)
            
            # --- FIX: Xử lý triệt để NaN và Infinity ---
            # 1. Chuyển Infinity (chia cho 0) thành NaN
            df_fin.replace([np.inf, -np.inf], np.nan, inplace=True)
            
            # 2. Chuyển NaN thành None (NULL trong SQL)
            # Dùng object type để chứa được None
            df_fin = df_fin.astype(object)
            df_fin = df_fin.where(pd.notnull(df_fin), None)
            
            print(f"Loading {len(df_fin)} financial records...")
            
            with engine.connect() as conn:
                 for _, row in df_fin.iterrows():
                    row_data = row.to_dict()
                    
                    # Safety check: Đảm bảo không còn sót NaN float nào trong dictionary
                    for k, v in row_data.items():
                        if isinstance(v, float) and np.isnan(v):
                            row_data[k] = None
                            
                    cols = ', '.join(df_fin.columns)
                    vals = ', '.join([f':{c}' for c in df_fin.columns])
                    
                    sql = text(f"""
                        INSERT IGNORE INTO financial_statements ({cols})
                        VALUES ({vals})
                    """)
                    conn.execute(sql, row_data)
                 conn.commit()
            print("Financials loaded.")
        else:
             print("Skipping Financials: File not found.")

    except Exception as e:
        print(f"Error loading financials: {e}")

if __name__ == "__main__":
    print("--- Starting Database Load ---")
    load_data()
    print("--- Database Load Complete ---")