#!/bin/bash

# Check if PID file exists
if [ -f bot.pid ]; then
    PID=$(cat bot.pid)
    
    # Check if process is still running
    if ps -p $PID > /dev/null; then
        echo "Stopping trading bot (PID: $PID)..."
        kill $PID
        rm bot.pid
        echo "Trading bot stopped."
    else
        echo "Trading bot not running (stale PID file)."
        rm bot.pid
    fi
else
    echo "No running trading bot found."
fi 