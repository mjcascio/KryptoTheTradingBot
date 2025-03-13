#!/bin/bash

# realtime_monitor.sh - Advanced script for real-time monitoring of KryptoBot
# This script uses optimized buffering settings for true real-time updates

echo "===== KryptoBot Real-Time Activity Monitor ====="
echo "This script provides true real-time updates of bot activity"
echo "Press Ctrl+C at any time to exit (bot will continue running)"
echo ""

# Check if bot is running
if [ ! -f "bot.pid" ] || ! ps -p $(cat bot.pid) > /dev/null; then
    echo "❌ Trading bot is not running! Start it with ./start_bot.sh"
    exit 1
fi

echo "✅ Bot is running (PID: $(cat bot.pid))"
echo ""

# Function to display a timestamp
show_timestamp() {
    echo -e "\033[1;36m[$(date '+%H:%M:%S')]\033[0m"
}

# Function to colorize output
colorize() {
    # Add colors based on keywords
    sed 's/SCAN/\x1b[1;34mSCAN\x1b[0m/g' |
    sed 's/SIGNAL/\x1b[1;33mSIGNAL\x1b[0m/g' |
    sed 's/TRADE/\x1b[1;32mTRADE\x1b[0m/g' |
    sed 's/ORDER/\x1b[1;32mORDER\x1b[0m/g' |
    sed 's/BUY/\x1b[1;32mBUY\x1b[0m/g' |
    sed 's/SELL/\x1b[1;31mSELL\x1b[0m/g' |
    sed 's/PASSED/\x1b[1;32mPASSED\x1b[0m/g' |
    sed 's/FAILED/\x1b[1;31mFAILED\x1b[0m/g' |
    sed 's/ERROR/\x1b[1;31mERROR\x1b[0m/g' |
    sed 's/WARNING/\x1b[1;33mWARNING\x1b[0m/g'
}

# Menu for different monitoring options
echo "Select what you want to monitor:"
echo "1) Symbol scanning (shows which symbols are being analyzed)"
echo "2) Trading signals (shows potential trade opportunities)"
echo "3) Executed trades (shows actual trades being made)"
echo "4) Full activity (shows everything - can be verbose)"
echo "5) Custom filter (enter your own search term)"
echo ""
read -p "Enter your choice (1-5): " choice

# Determine if we can use stdbuf for better buffering control
use_stdbuf=""
if command -v stdbuf &> /dev/null; then
    use_stdbuf="stdbuf -oL -eL"
fi

# Create a temporary named pipe for better real-time processing
PIPE=$(mktemp -u)
mkfifo "$PIPE"

# Cleanup function to remove the pipe when script exits
cleanup() {
    rm -f "$PIPE"
    echo -e "\nMonitoring stopped. Bot is still running."
    exit 0
}
trap cleanup EXIT INT TERM

case $choice in
    1)
        echo "Monitoring symbol scanning activity in real-time..."
        echo "-------------------------------------------"
        
        # Start tail in background, writing to the pipe
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -E "SCAN|Analyzing|screening|symbol" > "$PIPE" &
        else
            tail -f logs/trading_bot.out | grep --line-buffered -E "SCAN|Analyzing|screening|symbol" > "$PIPE" &
        fi
        
        # Read from the pipe with immediate output
        while read -r line; do
            show_timestamp
            echo "$line" | colorize
            echo "-------------------------------------------"
        done < "$PIPE"
        ;;
    2)
        echo "Monitoring trading signals in real-time..."
        echo "-------------------------------------------"
        
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -E "SIGNAL|opportunity|pattern|indicator|threshold|criteria" > "$PIPE" &
        else
            tail -f logs/trading_bot.out | grep --line-buffered -E "SIGNAL|opportunity|pattern|indicator|threshold|criteria" > "$PIPE" &
        fi
        
        while read -r line; do
            show_timestamp
            echo "$line" | colorize
            echo "-------------------------------------------"
        done < "$PIPE"
        ;;
    3)
        echo "Monitoring executed trades in real-time..."
        echo "-------------------------------------------"
        
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -E "TRADE|ORDER|BUY|SELL|position|executed" > "$PIPE" &
        else
            tail -f logs/trading_bot.out | grep --line-buffered -E "TRADE|ORDER|BUY|SELL|position|executed" > "$PIPE" &
        fi
        
        while read -r line; do
            show_timestamp
            echo "$line" | colorize
            echo "-------------------------------------------"
        done < "$PIPE"
        ;;
    4)
        echo "Monitoring full bot activity in real-time..."
        echo "-------------------------------------------"
        
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out > "$PIPE" &
        else
            tail -f logs/trading_bot.out > "$PIPE" &
        fi
        
        while read -r line; do
            show_timestamp
            echo "$line" | colorize
            echo "-------------------------------------------"
        done < "$PIPE"
        ;;
    5)
        echo "Enter your custom filter term (e.g., 'AAPL' to track a specific symbol):"
        read filter_term
        echo "Monitoring for: $filter_term in real-time..."
        echo "-------------------------------------------"
        
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -i "$filter_term" > "$PIPE" &
        else
            tail -f logs/trading_bot.out | grep --line-buffered -i "$filter_term" > "$PIPE" &
        fi
        
        while read -r line; do
            show_timestamp
            echo "$line" | colorize
            echo "-------------------------------------------"
        done < "$PIPE"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac 