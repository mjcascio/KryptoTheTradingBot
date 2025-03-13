#!/bin/bash

# restart_all.sh - Script to restart both the KryptoBot trading bot and dashboard

echo "===== Restarting KryptoBot Trading System ====="

# Stop all components
echo "Stopping all components..."
./stop_all.sh

# Wait a moment to ensure everything is stopped
sleep 3

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

# Start all components
echo "Starting all components..."
./start_all.sh

# Verify everything is running
echo "Verifying all components are running..."
./status.sh

echo "===== KryptoBot Trading System Restart Complete ====="
echo "To monitor bot activity: ./monitor.sh"
echo "To view logs:"
echo "  - Trading bot: tail -f logs/trading_bot.out"
echo "  - Dashboard: tail -f logs/dashboard.out"
echo ""
echo "Dashboard should be available at: http://localhost:5002" 