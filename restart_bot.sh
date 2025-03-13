#!/bin/bash

# restart_bot.sh - Script to restart the KryptoBot trading bot

echo "===== Restarting KryptoBot Trading Bot ====="

# Stop the bot
echo "Stopping the trading bot..."
./stop_bot.sh

# Wait a moment to ensure it's stopped
sleep 2

# Remove any stale PID file
if [ -f "bot.pid" ]; then
    echo "Removing stale bot PID file..."
    rm bot.pid
fi

# Start the bot
echo "Starting the trading bot..."
./start_bot.sh

# Verify it's running
if [ -f "bot.pid" ] && ps -p $(cat bot.pid) > /dev/null; then
    echo "✅ Trading bot successfully restarted (PID: $(cat bot.pid))"
    echo "To monitor bot activity: ./monitor.sh"
    echo "To view logs: tail -f logs/trading_bot.out"
else
    echo "❌ Failed to restart trading bot"
    echo "Check logs for errors: cat logs/trading_bot.out"
fi 