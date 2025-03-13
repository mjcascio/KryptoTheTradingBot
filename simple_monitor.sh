#!/bin/bash

# Simple monitoring script that uses tail -f with grep for filtering
# Colors for different types of messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

LOG_FILE="logs/trading_bot.out"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "Error: Log file $LOG_FILE does not exist"
    exit 1
fi

echo "Starting real-time monitoring of $LOG_FILE"
echo "Press Ctrl+C to stop"
echo

# Use tail -f to follow the log file and pipe through grep with color highlighting
# The sed commands add colors to different types of messages
tail -f "$LOG_FILE" | sed \
    -e "s/\(.*SCAN: FAILED.*\)/${RED}\1${NC}/g" \
    -e "s/\(.*SCAN: PASSED.*\)/${GREEN}\1${NC}/g" \
    -e "s/\(.*SIGNAL:.*\)/${YELLOW}\1${NC}/g" \
    -e "s/\(.*TRADE:.*\)/${PURPLE}\1${NC}/g" \
    -e "s/\(.*DECISION:.*\)/${BLUE}\1${NC}/g" \
    -e "s/\(.*checking.*\)/${CYAN}\1${NC}/g" 