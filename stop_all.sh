#!/bin/bash

# Simple script to stop both the KryptoBot trading bot and dashboard
echo "===== Stopping KryptoBot Trading System ====="

# Navigate to the script's directory
cd "$(dirname "$0")"

# Stop the bot
echo "Stopping trading bot..."
./stop_bot.sh

# Stop the dashboard
echo "Stopping dashboard..."
./stop_dashboard.sh

# Verify all processes are stopped
if pgrep -f "python.*main.py|python.*dashboard.py" > /dev/null; then
    echo "Warning: Some processes could not be stopped. Attempting to kill by PID..."
    pgrep -f "python.*main.py|python.*dashboard.py" | xargs kill -9 || true
    sleep 2
    
    if pgrep -f "python.*main.py|python.*dashboard.py" > /dev/null; then
        echo "❌ Failed to stop all processes. Please check manually."
        exit 1
    fi
fi

echo "✅ All processes stopped successfully"
echo "===== KryptoBot Trading System Shutdown Complete =====" 