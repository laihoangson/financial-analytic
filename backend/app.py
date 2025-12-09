# backend/app.py
from flask import Flask, render_template, jsonify
import pandas as pd
from sqlalchemy import create_engine
from config import DB_CONFIG
from urllib.parse import quote_plus

app = Flask(__name__, 
            template_folder='../frontend',
            static_folder='../frontend/assets')

def get_db_engine():
    encoded_password = quote_plus(DB_CONFIG['password'])
    conn_str = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(conn_str)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pipeline')
def pipeline():
    return render_template('pipeline.html')

@app.route('/sql')
def sql_demo():
    return render_template('sql.html')

@app.route('/powerbi')
def powerbi():
    return render_template('powerbi.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

# API endpoints for data
@app.route('/api/companies')
def get_companies():
    engine = get_db_engine()
    df = pd.read_sql("SELECT * FROM companies", engine)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stock_prices/<ticker>')
def get_stock_prices(ticker):
    engine = get_db_engine()
    query = f"SELECT * FROM stock_prices WHERE ticker = '{ticker}' ORDER BY date DESC LIMIT 100"
    df = pd.read_sql(query, engine)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/financials/<ticker>')
def get_financials(ticker):
    engine = get_db_engine()
    query = f"SELECT * FROM financial_statements WHERE ticker = '{ticker}' ORDER BY report_date DESC"
    df = pd.read_sql(query, engine)
    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)