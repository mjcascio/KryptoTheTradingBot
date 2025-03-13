#!/bin/bash
# Start Alpaca Sync Service
#
# This script starts the Alpaca sync service in the background.
# It ensures that local data is synchronized with Alpaca at regular intervals.

# Default sync interval in minutes
INTERVAL=15

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--interval MINUTES]"
      exit 1
      ;;
  esac
done

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  echo "Activating virtual environment..."
  source .venv/bin/activate
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 is not installed or not in PATH"
  exit 1
fi

# Check if the auto_sync_alpaca.py script exists
if [ ! -f "auto_sync_alpaca.py" ]; then
  echo "Error: auto_sync_alpaca.py not found"
  exit 1
fi

# Make sure the script is executable
chmod +x auto_sync_alpaca.py

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the sync service in the background
echo "Starting Alpaca sync service with interval of $INTERVAL minutes..."
nohup python3 auto_sync_alpaca.py --interval $INTERVAL > logs/alpaca_sync.out 2>&1 &

# Save the process ID
echo $! > alpaca_sync.pid

echo "Alpaca sync service started with PID $(cat alpaca_sync.pid)"
echo "Logs are being written to logs/alpaca_sync.out and alpaca_sync.log"
echo "To stop the service, run: kill $(cat alpaca_sync.pid)" 