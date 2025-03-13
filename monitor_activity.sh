#!/bin/bash

# monitor_activity.sh - Script to monitor KryptoBot's scanning process in real-time
# This script focuses on showing the bot's scanning and analysis of potential trades

echo "===== KryptoBot Scanning Activity Monitor ====="
echo "This tool shows you exactly which symbols the bot is analyzing"
echo "Press Ctrl+C at any time to exit the monitor (bot will continue running)"
echo ""

# Check if bot is running
if [ ! -f "bot.pid" ] || ! ps -p $(cat bot.pid) > /dev/null; then
    echo "❌ Trading bot is not running! Start it with ./start_bot.sh"
    exit 1
fi

echo "✅ Bot is running (PID: $(cat bot.pid))"
echo ""

# Function to display colored output
color_output() {
    local line="$1"
    
    # Highlight symbols
    if [[ $line == *"Analyzing"* ]]; then
        echo -e "\033[1;36m$line\033[0m"  # Cyan for symbols being analyzed
    elif [[ $line == *"passed"* ]]; then
        echo -e "\033[1;32m$line\033[0m"  # Green for passed checks
    elif [[ $line == *"failed"* ]]; then
        echo -e "\033[1;31m$line\033[0m"  # Red for failed checks
    elif [[ $line == *"SIGNAL"* ]]; then
        echo -e "\033[1;33m$line\033[0m"  # Yellow for signals
    elif [[ $line == *"TRADE"* ]]; then
        echo -e "\033[1;35m$line\033[0m"  # Purple for trades
    else
        echo "$line"
    fi
}

# Menu for different monitoring options
echo "Select what you want to monitor:"
echo "1) Basic scanning (just symbol names and basic status)"
echo "2) Detailed scanning (includes parameter checks)"
echo "3) Full decision process (all details including analysis)"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "Monitoring basic scanning activity..."
        echo "-------------------------------------------"
        tail -f logs/trading_bot.out | grep -E "Analyzing|scanning|screened|symbol" | while read line; do
            color_output "$line"
        done
        ;;
    2)
        echo "Monitoring detailed scanning activity..."
        echo "-------------------------------------------"
        tail -f logs/trading_bot.out | grep -E "Analyzing|parameter|threshold|criteria|passed|failed|screening" | while read line; do
            color_output "$line"
        done
        ;;
    3)
        echo "Monitoring full decision process..."
        echo "-------------------------------------------"
        tail -f logs/trading_bot.out | grep -E "SCAN|Analyzing|parameter|threshold|passed|failed|Decision|SIGNAL|opportunity|pattern|indicator" | while read line; do
            color_output "$line"
        done
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac 