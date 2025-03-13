#!/bin/bash

# Simple script to stop the KryptoBot dashboard
echo "===== Stopping KryptoBot Dashboard ====="

# Navigate to the script's directory
cd "$(dirname "$0")"

# Stop the dashboard process
if [ -f "dashboard.pid" ]; then
    echo "Stopping dashboard (PID: $(cat dashboard.pid))..."
    kill $(cat dashboard.pid) 2>/dev/null || true
    
    # Check if process is still running
    sleep 2
    if ps -p $(cat dashboard.pid) > /dev/null 2>&1; then
        echo "Force stopping dashboard..."
        kill -9 $(cat dashboard.pid) 2>/dev/null || true
    fi
    
    rm dashboard.pid
    echo "✅ Dashboard stopped"
else
    echo "⚠️ No dashboard.pid file found"
    # Try to find and kill any running dashboard process
    pkill -f "python.*dashboard.py" || true
fi

echo "Dashboard has been stopped." 