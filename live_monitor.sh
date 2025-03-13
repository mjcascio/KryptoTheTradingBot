#!/bin/bash

# live_monitor.sh - Simple script to monitor the bot's activity in real-time

echo "===== KryptoBot Live Activity Monitor ====="
echo "This script shows you the bot's scanning and trading activity in real-time"
echo "Press Ctrl+C at any time to exit"
echo ""

# Check if bot is running
if [ ! -f "bot.pid" ] || ! ps -p $(cat bot.pid) > /dev/null; then
    echo "❌ Trading bot is not running! Start it with ./start_bot.sh"
    exit 1
fi

echo "✅ Bot is running (PID: $(cat bot.pid))"
echo ""
echo "Showing live activity as it happens..."
echo "-------------------------------------------"
echo ""

# Create a named pipe for better real-time processing
PIPE=$(mktemp -u)
mkfifo "$PIPE"

# Cleanup function to remove the pipe when script exits
cleanup() {
    rm -f "$PIPE"
    echo -e "\nMonitoring stopped. Bot is still running."
    exit 0
}
trap cleanup EXIT INT TERM

# Start tail in background, writing to the pipe
tail -f logs/trading_bot.out > "$PIPE" &

# Read from the pipe with immediate output and colorize
cat "$PIPE" | grep --line-buffered "SCAN\|Analyzing\|checking\|PASSED\|FAILED\|SIGNAL\|TRADE\|DECISION" | while read -r line; do
    # Add timestamp
    echo -e "\033[1;36m[$(date '+%H:%M:%S')]\033[0m $line"
done 