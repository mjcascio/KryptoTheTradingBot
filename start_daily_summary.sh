#!/bin/bash
#
# Start Daily Summary Service
#
# This script starts the daily summary service to generate and send
# end-of-day trading reports.

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Parse command line arguments
NOW=false
SCHEDULE_TIME="16:00"

while [[ $# -gt 0 ]]; do
    case $1 in
        --now)
            NOW=true
            shift
            ;;
        --time)
            shift
            SCHEDULE_TIME="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--now] [--time HH:MM]"
            exit 1
            ;;
    esac
done

# Set environment variables for Telegram
export TELEGRAM_BOT_TOKEN="8078241360:AAE3KoFYSUhV7uKSDaTBuWuCWtTRHkw4dyk"
export TELEGRAM_CHAT_ID="7924393886"

# Build command
if [ "$NOW" = true ]; then
    CMD="python3 run_daily_summary.py"
else
    CMD="python3 daily_summary.py --schedule $SCHEDULE_TIME"
fi

# Print command
echo "Running: $CMD"

# Run in background if not running now
if [ "$NOW" = false ]; then
    echo "Starting daily summary service in the background..."
    nohup $CMD > daily_summary.out 2>&1 &
    echo "Service started with PID $!"
    echo "Logs are being written to daily_summary.out"
else
    # Run in foreground
    $CMD
fi 