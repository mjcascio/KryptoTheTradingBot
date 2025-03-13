#!/bin/bash

# monitor_trades.sh - Script to monitor KryptoBot's trading activity in real-time
# This script provides a clear, filtered view of the bot's scanning and trading activities

echo "===== KryptoBot Trading Activity Monitor ====="
echo "Press Ctrl+C at any time to exit the monitor (bot will continue running)"
echo ""

# Function to display a timestamp
show_timestamp() {
    echo "[$(date '+%H:%M:%S')]"
}

# Check if bot is running
if [ ! -f "bot.pid" ] || ! ps -p $(cat bot.pid) > /dev/null; then
    echo "❌ Trading bot is not running! Start it with ./start_bot.sh"
    exit 1
fi

echo "✅ Bot is running (PID: $(cat bot.pid))"
echo ""

# Menu for different monitoring options
echo "Select what you want to monitor:"
echo "1) Symbol scanning (shows which symbols are being analyzed)"
echo "2) Trading signals (shows potential trade opportunities)"
echo "3) Executed trades (shows actual trades being made)"
echo "4) Full activity (shows everything - can be verbose)"
echo "5) Custom filter (enter your own search term)"
echo ""
read -p "Enter your choice (1-5): " choice

# Use stdbuf if available for better real-time output
use_stdbuf=""
if command -v stdbuf &> /dev/null; then
    use_stdbuf="stdbuf -oL -eL"
fi

case $choice in
    1)
        echo "Monitoring symbol scanning activity..."
        echo "-------------------------------------------"
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -E "SCAN|Analyzing|screening|symbol" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        else
            tail -f logs/trading_bot.out | grep --line-buffered -E "SCAN|Analyzing|screening|symbol" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        fi
        ;;
    2)
        echo "Monitoring trading signals..."
        echo "-------------------------------------------"
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -E "SIGNAL|opportunity|pattern|indicator|threshold|criteria" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        else
            tail -f logs/trading_bot.out | grep --line-buffered -E "SIGNAL|opportunity|pattern|indicator|threshold|criteria" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        fi
        ;;
    3)
        echo "Monitoring executed trades..."
        echo "-------------------------------------------"
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -E "TRADE|ORDER|BUY|SELL|position|executed" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        else
            tail -f logs/trading_bot.out | grep --line-buffered -E "TRADE|ORDER|BUY|SELL|position|executed" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        fi
        ;;
    4)
        echo "Monitoring full bot activity..."
        echo "-------------------------------------------"
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        else
            tail -f logs/trading_bot.out | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        fi
        ;;
    5)
        echo "Enter your custom filter term (e.g., 'AAPL' to track a specific symbol):"
        read filter_term
        echo "Monitoring for: $filter_term"
        echo "-------------------------------------------"
        if [ -n "$use_stdbuf" ]; then
            $use_stdbuf tail -f logs/trading_bot.out | $use_stdbuf grep --line-buffered -i "$filter_term" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        else
            tail -f logs/trading_bot.out | grep --line-buffered -i "$filter_term" | while read line; do
                show_timestamp
                echo "$line"
                echo "-------------------------------------------"
            done
        fi
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac 