#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Create necessary directories
mkdir -p data models logs reports

# Start the trading bot in the background with logging
nohup python main.py > logs/trading_bot.out 2>&1 &

# Save the process ID for later management
echo $! > bot.pid

echo "Enhanced Trading Bot started in background. Process ID: $(cat bot.pid)"
echo "View logs with: tail -f logs/trading_bot.out"
echo "Dashboard available at: http://localhost:5001" 