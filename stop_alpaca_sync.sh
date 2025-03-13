#!/bin/bash
# Stop Alpaca Sync Service
#
# This script stops the Alpaca sync service.

# Check if the PID file exists
if [ ! -f "alpaca_sync.pid" ]; then
  echo "Error: alpaca_sync.pid not found. Service may not be running."
  exit 1
fi

# Get the PID
PID=$(cat alpaca_sync.pid)

# Check if the process is running
if ! ps -p $PID > /dev/null; then
  echo "Error: Process with PID $PID is not running."
  rm alpaca_sync.pid
  exit 1
fi

# Stop the process
echo "Stopping Alpaca sync service with PID $PID..."
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
rm alpaca_sync.pid

echo "Alpaca sync service stopped." 