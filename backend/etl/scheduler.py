# backend/etl/scheduler.py
# Author: Hoang Son Lai
import schedule
import time
import subprocess
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_etl_pipeline():
    """Chạy toàn bộ ETL pipeline."""
    try:
        logging.info("=== Starting Daily ETL Pipeline ===")
        
        # Run fetch_data.py
        subprocess.run(['python', 'backend/etl/fetch_data.py'], check=True)
        logging.info("Fetch data completed")
        
        # Run clean_data.py
        subprocess.run(['python', 'backend/etl/clean_data.py'], check=True)
        logging.info("Clean data completed")
        
        # Run load_to_mysql.py
        subprocess.run(['python', 'backend/etl/load_to_mysql.py'], check=True)
        logging.info("Load to MySQL completed")
        
        logging.info("=== ETL Pipeline Completed Successfully ===")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"ETL Pipeline failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

def main():
    """Cấu hình lịch trình."""
    # Schedule daily at 6:00 PM (sau khi thị trường đóng)
    schedule.every().day.at("18:00").do(run_etl_pipeline)
    
    # Chạy ngay lần đầu khi khởi động (tuỳ chọn)
    logging.info("Scheduler started. First run will be at 18:00 daily.")
    print("Scheduler started. First run will be at 18:00 daily.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()