#!/bin/bash

# start_bot.sh - Script to start the KryptoBot trading bot

echo "===== Starting KryptoBot Trading Bot with Alpaca ====="

# Check if bot is already running
if [ -f "bot.pid" ]; then
    if ps -p $(cat bot.pid) > /dev/null; then
        echo "⚠️ Trading bot is already running (PID: $(cat bot.pid))"
        echo "To restart, run: ./restart_bot.sh"
        exit 1
    else
        echo "Removing stale PID file..."
        rm bot.pid
    fi
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

echo "Running preflight check..."
python test_options.py

# Check if preflight was successful
if [ $? -ne 0 ]; then
    echo "❌ Preflight check failed. Please resolve issues before starting the bot."
    exit 1
fi

echo "Starting trading bot..."

# Start the trading bot in the background
python3 src/main.py > logs/trading_bot.out 2>&1 &

# Save the PID
echo $! > bot.pid

# Wait a moment to ensure the process starts
sleep 2

# Check if the bot is running
if [ -f "bot.pid" ] && ps -p $(cat bot.pid) > /dev/null; then
    echo "✅ Trading bot started (PID: $(cat bot.pid))"
    echo "To view logs: tail -f logs/trading_bot.out"
    echo "To monitor positions: tail -f logs/positions.log"
    echo "To monitor trades: tail -f logs/trades.log"
else
    echo "❌ Failed to start trading bot"
    echo "Check logs for errors: cat logs/trading_bot.out"
    exit 1
fi 