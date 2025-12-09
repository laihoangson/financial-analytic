#!/bin/bash
# automation/cronjob.sh
# Auto-update script for Render.com cron jobs

echo "=== Starting Daily Data Update ==="
echo "Date: $(date)"

# Navigate to project directory
cd /opt/render/project/src || exit

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run ETL pipeline
echo "Running fetch_data.py..."
python backend/etl/fetch_data.py

echo "Running clean_data.py..."
python backend/etl/clean_data.py

echo "Running load_to_mysql.py..."
python backend/etl/load_to_mysql.py

echo "=== Daily Update Completed ==="