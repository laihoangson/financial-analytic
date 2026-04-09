# backend/etl/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Project Author: Hoang Son Lai

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
DATA_CLEANED_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')

# Ensure directories exist
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_CLEANED_DIR, exist_ok=True)

# Target Companies 
TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'JPM', 'JNJ', 'V', 'WMT',
    'PG', 'HD', 'MA', 'UNH', 'DIS', 'BAC', 'NVDA', 'PYPL', 'NFLX', 'ADBE', 'KO'
]

# --- 1. MySQL Configuration (Local) ---
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME')
}

# --- 2. Supabase PostgreSQL Configuration (Cloud) ---
SUPABASE_DB_CONFIG = {
    'user': os.getenv('SUPA_DB_USER'),
    'password': os.getenv('SUPA_DB_PASSWORD'),
    'host': os.getenv('SUPA_DB_HOST'),
    'port': int(os.getenv('SUPA_DB_PORT', 5432)),
    'database': os.getenv('SUPA_DB_NAME')
}

# --- 3. Frontend API ---
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')