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
    'AAPL',  # Apple
    'MSFT',  # Microsoft
    'GOOGL', # Alphabet
    'AMZN',  # Amazon
    'META',  # Meta Platforms
    'TSLA',  # Tesla
    'JPM',   # JPMorgan Chase
    'JNJ',   # Johnson & Johnson
    'V',     # Visa
    'WMT',   # Walmart
    'PG',    # Procter & Gamble
    'UNH',   # UnitedHealth Group
    'HD',    # Home Depot
    'MA',    # Mastercard
    'DIS',   # Walt Disney
    'BAC',   # Bank of America
    'NVDA',  # NVIDIA
    'PYPL',  # PayPal
    'NFLX',  # Netflix
    'ADBE',  # Adobe
    'KO'     # Coca-Cola
]

# MySQL Configuration 
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME')
}