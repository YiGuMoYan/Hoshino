#!/bin/bash

# Initialize Database
echo "Initializing database..."
python init_db.py

# Start Huey Worker in background
echo "Starting Huey worker..."
python run_worker.py > worker.log 2>&1 &

# Start FastAPI application
echo "Starting Hoshino..."
# Bind to 0.0.0.0 to accessible from outside container
exec uvicorn app.main:app --host 0.0.0.0 --port 8712
