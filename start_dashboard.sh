#!/bin/bash

# start_dashboard.sh - Script to start the KryptoBot dashboard

echo "===== Starting KryptoBot Dashboard with Alpaca Integration ====="

# Check if dashboard is already running
if [ -f "dashboard.pid" ]; then
    if ps -p $(cat dashboard.pid) > /dev/null; then
        echo "⚠️ Dashboard is already running (PID: $(cat dashboard.pid))"
        echo "To restart, run: ./restart_dashboard.sh"
        exit 1
    else
        echo "Removing stale PID file..."
        rm dashboard.pid
    fi
fi

# Kill any existing processes on port 5002
EXISTING_PID=$(lsof -t -i:5002 2>/dev/null)
if [ ! -z "$EXISTING_PID" ]; then
    echo "Killing existing process on port 5002 (PID: $EXISTING_PID)..."
    kill -9 $EXISTING_PID 2>/dev/null
fi

# Create logs directory if it doesn't exist
mkdir -p logs data

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="$PWD:$PYTHONPATH"

echo "Starting dashboard..."

# Start the dashboard in the background
python dashboard.py > logs/dashboard.out 2>&1 &

# Save the PID
echo $! > dashboard.pid

# Wait a moment to ensure the process starts
sleep 2

# Check if the dashboard is running
if [ -f "dashboard.pid" ] && ps -p $(cat dashboard.pid) > /dev/null; then
    echo "✅ Dashboard started (PID: $(cat dashboard.pid))"
    echo "Dashboard should be available at: http://localhost:5002"
    echo "To view logs: tail -f logs/dashboard.out"
else
    echo "❌ Failed to start dashboard"
    echo "Check logs for errors: cat logs/dashboard.out"
    exit 1
fi 