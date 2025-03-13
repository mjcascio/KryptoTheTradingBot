#!/bin/bash

# start_all.sh - Script to start both the KryptoBot trading bot and dashboard

echo "===== Starting KryptoBot Trading System with Alpaca ====="

# Stop any existing processes
echo "Stopping any existing processes..."
./stop_all.sh

# Remove any stale PID files
if [ -f "bot.pid" ]; then
    echo "Removing stale bot PID file..."
    rm bot.pid
fi

if [ -f "dashboard.pid" ]; then
    echo "Removing stale dashboard PID file..."
    rm dashboard.pid
fi

# Kill any processes that might be using the required ports
EXISTING_PID_5002=$(lsof -t -i:5002 2>/dev/null)
if [ ! -z "$EXISTING_PID_5002" ]; then
    echo "Killing existing process on port 5002 (PID: $EXISTING_PID_5002)..."
    kill -9 $EXISTING_PID_5002 2>/dev/null
fi

# Start the trading bot
echo "Starting trading bot..."
./start_bot.sh

# Start the dashboard
echo "Starting dashboard..."
./start_dashboard.sh

# Verify all processes are running
echo "Verifying all processes are running..."
./status.sh

echo "===== KryptoBot Trading System Startup Complete ====="
echo "To view logs:"
echo "  - Trading bot: tail -f logs/trading_bot.out"
echo "  - Dashboard: tail -f logs/dashboard.out"
echo ""
echo "Dashboard should be available at: http://localhost:5002" 