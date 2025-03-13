#!/bin/bash
# Stop Options Trading Service
#
# This script stops the options trading service.

echo "===== Stopping KryptoBot Options Trading Service ====="

# Check if the PID file exists
if [ ! -f "options_trading.pid" ]; then
    echo "Error: options_trading.pid not found. Service may not be running."
    exit 1
fi

# Get the PID
PID=$(cat options_trading.pid)

# Check if the process is running
if ! ps -p $PID > /dev/null; then
    echo "Error: Process with PID $PID is not running."
    rm options_trading.pid
    exit 1
fi

# Stop the process
echo "Stopping options trading service with PID $PID..."
kill $PID

# Wait for the process to stop
sleep 2

# Check if the process is still running
if ps -p $PID > /dev/null; then
    echo "Process is still running. Sending SIGKILL..."
    kill -9 $PID
    sleep 1
fi

# Remove the PID file
rm options_trading.pid

echo "Options trading service stopped." 