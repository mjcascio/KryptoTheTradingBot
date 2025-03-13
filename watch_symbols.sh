#!/bin/bash

# watch_symbols.sh - Script to monitor specific symbols the bot is analyzing
# This script allows you to track specific ticker symbols you're interested in

echo "===== KryptoBot Symbol Watcher ====="
echo "This tool lets you track specific symbols the bot is analyzing"
echo "Press Ctrl+C at any time to exit the watcher (bot will continue running)"
echo ""

# Check if bot is running
if [ ! -f "bot.pid" ] || ! ps -p $(cat bot.pid) > /dev/null; then
    echo "❌ Trading bot is not running! Start it with ./start_bot.sh"
    exit 1
fi

echo "✅ Bot is running (PID: $(cat bot.pid))"
echo ""

# Function to watch a specific symbol
watch_symbol() {
    local symbol="$1"
    echo "Watching activity for symbol: $symbol"
    echo "-------------------------------------------"
    tail -f logs/trading_bot.out | grep -i "$symbol" | while read line; do
        echo "[$(date '+%H:%M:%S')] $line"
    done
}

# Function to watch multiple symbols
watch_multiple_symbols() {
    local symbols="$1"
    local grep_pattern=$(echo "$symbols" | sed 's/,/\\|/g')
    echo "Watching activity for symbols: $symbols"
    echo "-------------------------------------------"
    tail -f logs/trading_bot.out | grep -E "$grep_pattern" | while read line; do
        echo "[$(date '+%H:%M:%S')] $line"
    done
}

# Function to watch symbols that pass initial screening
watch_passing_symbols() {
    echo "Watching symbols that pass initial screening..."
    echo "-------------------------------------------"
    tail -f logs/trading_bot.out | grep -E "passed|screening|criteria" | while read line; do
        echo "[$(date '+%H:%M:%S')] $line"
    done
}

# Menu for different watching options
echo "Select what you want to do:"
echo "1) Watch a specific symbol (e.g., AAPL)"
echo "2) Watch multiple symbols (comma-separated, e.g., AAPL,MSFT,GOOGL)"
echo "3) Watch all symbols that pass initial screening"
echo "4) Watch top 10 most active symbols"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Enter the symbol you want to watch (e.g., AAPL):"
        read symbol
        watch_symbol "$symbol"
        ;;
    2)
        echo "Enter the symbols you want to watch (comma-separated, e.g., AAPL,MSFT,GOOGL):"
        read symbols
        watch_multiple_symbols "$symbols"
        ;;
    3)
        watch_passing_symbols
        ;;
    4)
        echo "Watching the most active symbols..."
        echo "-------------------------------------------"
        # First, collect symbol mentions for 10 seconds
        echo "Analyzing symbol activity (this will take 10 seconds)..."
        symbol_counts=$(timeout 10 tail -f logs/trading_bot.out | grep -o -E '[A-Z]{1,5}' | sort | uniq -c | sort -nr | head -10)
        
        # Then display the most active symbols
        echo "Most active symbols (based on recent log activity):"
        echo "$symbol_counts"
        echo ""
        
        # Extract just the symbols for monitoring
        symbols=$(echo "$symbol_counts" | awk '{print $2}' | tr '\n' '|' | sed 's/|$//')
        
        echo "Now monitoring these symbols..."
        echo "-------------------------------------------"
        tail -f logs/trading_bot.out | grep -E "$symbols" | while read line; do
            echo "[$(date '+%H:%M:%S')] $line"
        done
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac 