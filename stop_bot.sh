#!/bin/bash

# Simple script to stop the KryptoBot trading bot
echo "===== Stopping KryptoBot Trading Bot ====="

# Navigate to the script's directory
cd "$(dirname "$0")"

# Stop the bot process
if [ -f "bot.pid" ]; then
    echo "Stopping trading bot (PID: $(cat bot.pid))..."
    kill $(cat bot.pid) 2>/dev/null || true
    
    # Check if process is still running
    sleep 2
    if ps -p $(cat bot.pid) > /dev/null 2>&1; then
        echo "Force stopping trading bot..."
        kill -9 $(cat bot.pid) 2>/dev/null || true
    fi
    
    rm bot.pid
    echo "✅ Trading bot stopped"
else
    echo "⚠️ No bot.pid file found"
    # Try to find and kill any running bot process
    pkill -f "python.*main.py" || true
fi

echo "Trading bot has been stopped." 