#!/bin/bash

# restart_dashboard.sh - Script to restart the KryptoBot dashboard

echo "===== Restarting KryptoBot Dashboard ====="

# Stop the dashboard
echo "Stopping the dashboard..."
./stop_dashboard.sh

# Wait a moment to ensure it's stopped
sleep 2

# Remove any stale PID file
if [ -f "dashboard.pid" ]; then
    echo "Removing stale dashboard PID file..."
    rm dashboard.pid
fi

# Kill any processes that might be using port 5000
EXISTING_PID=$(lsof -t -i:5000 2>/dev/null)
if [ ! -z "$EXISTING_PID" ]; then
    echo "Killing existing process on port 5000 (PID: $EXISTING_PID)..."
    kill -9 $EXISTING_PID 2>/dev/null
fi

# Start the dashboard
echo "Starting the dashboard..."
./start_dashboard.sh

# Verify it's running
if [ -f "dashboard.pid" ] && ps -p $(cat dashboard.pid) > /dev/null; then
    echo "✅ Dashboard successfully restarted (PID: $(cat dashboard.pid))"
    echo "Dashboard should be available at: http://localhost:5000"
    echo "To view logs: tail -f logs/dashboard.out"
else
    echo "❌ Failed to restart dashboard"
    echo "Check logs for errors: cat logs/dashboard.out"
fi 