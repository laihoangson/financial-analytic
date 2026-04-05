# backend/etl/export_queries.py
# Author: Hoang Son Lai

import os
import pandas as pd
from sqlalchemy import text
from config import BASE_DIR
from load_to_supabase import get_supabase_engine

# Đường dẫn đến thư mục chứa file kết quả CSV
QUERY_DATA_DIR = os.path.join(BASE_DIR, 'data', 'query_data')
os.makedirs(QUERY_DATA_DIR, exist_ok=True)

def export_views_to_csv():
    print("\n>>> EXPORTING SUPABASE VIEWS TO CSV <<<")
    engine = get_supabase_engine()
    
    for i in range(1, 9):
        view_name = f"view_query{i}"
        output_path = os.path.join(QUERY_DATA_DIR, f'result{i}.csv')
        
        try:
            print(f"Fetching data from {view_name}...", end='\r')
            with engine.connect() as conn:
                # Lấy dữ liệu từ View trên Supabase
                df = pd.read_sql(text(f"SELECT * FROM {view_name}"), conn)
            
            # Lưu đè lên file CSV cũ
            df.to_csv(output_path, index=False)
            print(f"[Success] Saved {view_name} to result{i}.csv ({len(df)} rows)")
            
        except Exception as e:
            print(f"[Error] Failed to export {view_name}: {e}")

def main():
    export_views_to_csv()

if __name__ == "__main__":
    main()