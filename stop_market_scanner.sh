#!/bin/bash
# Stop Market Scanner Service
#
# This script stops the market scanner service.

echo "===== Stopping KryptoBot Market Scanner Service ====="

# Check if the PID file exists
if [ ! -f "market_scanner.pid" ]; then
    echo "Error: market_scanner.pid not found. Service may not be running."
    exit 1
fi

# Get the PID
PID=$(cat market_scanner.pid)

# Check if the process is running
if ! ps -p $PID > /dev/null; then
    echo "Error: Process with PID $PID is not running."
    rm market_scanner.pid
    exit 1
fi

# Stop the process
echo "Stopping market scanner service with PID $PID..."
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
rm market_scanner.pid

echo "Market scanner service stopped." 