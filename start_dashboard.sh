#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Error: Virtual environment not found. Please create one first."
    exit 1
fi

# Check if port 5001 is already in use
if lsof -i :5001 > /dev/null 2>&1; then
    echo "Port 5001 is already in use. Stopping existing process..."
    lsof -i :5001 | grep -v PID | awk '{print $2}' | xargs kill -9 2>/dev/null
    sleep 1
fi

# Create necessary directories
mkdir -p data templates logs

# Start the dashboard in the background
echo "Starting KryptoBot Dashboard..."
nohup python dashboard.py > logs/dashboard.log 2>&1 &

# Save the process ID
echo $! > dashboard.pid

echo "Dashboard started with PID: $(cat dashboard.pid)"
echo "Dashboard available at: http://localhost:5001"
echo "View logs with: tail -f logs/dashboard.log" 