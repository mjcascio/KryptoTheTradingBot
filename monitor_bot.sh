#!/bin/bash

# Function to check if bot is running
check_bot() {
    if [ -f bot.pid ]; then
        PID=$(cat bot.pid)
        if ps -p $PID > /dev/null; then
            return 0  # Bot is running
        fi
    fi
    return 1  # Bot is not running
}

# Function to start bot
start_bot() {
    echo "[$(date)] Starting trading bot..."
    ./run_bot_background.sh
    sleep 5  # Wait for bot to start
}

# Main monitoring loop
while true; do
    if ! check_bot; then
        echo "[$(date)] Bot not running. Restarting..."
        start_bot
    fi
    
    # Check every 5 minutes
    sleep 300
done 