#!/bin/bash
# Start Market Scanner Service
#
# This script starts the market scanner service in the background.
# It schedules market scans after hours and sends morning summaries at 8:00 AM.

echo "===== Starting KryptoBot Market Scanner Service ====="

# Check if service is already running
if [ -f "market_scanner.pid" ]; then
    if ps -p $(cat market_scanner.pid) > /dev/null; then
        echo "⚠️ Market scanner service is already running (PID: $(cat market_scanner.pid))"
        echo "To restart, run: ./stop_market_scanner.sh first"
        exit 1
    else
        echo "Removing stale PID file..."
        rm market_scanner.pid
    fi
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if the required scripts exist
if [ ! -f "schedule_market_scan.py" ] || [ ! -f "market_scanner.py" ]; then
    echo "Error: Required scripts not found"
    exit 1
fi

# Make sure the scripts are executable
chmod +x schedule_market_scan.py market_scanner.py

# Create logs directory if it doesn't exist
mkdir -p logs

# Create data/scanner directory if it doesn't exist
mkdir -p data/scanner

# Start the service in the background
echo "Starting market scanner service..."
nohup python3 schedule_market_scan.py > logs/market_scanner.out 2>&1 &

# Save the process ID
echo $! > market_scanner.pid

echo "Market scanner service started with PID $(cat market_scanner.pid)"
echo "Logs are being written to logs/market_scanner.out and market_scan_scheduler.log"
echo "To stop the service, run: ./stop_market_scanner.sh"

# Run an initial scan if requested
if [ "$1" == "--scan-now" ]; then
    echo "Running initial market scan..."
    python3 schedule_market_scan.py --scan-now
fi 