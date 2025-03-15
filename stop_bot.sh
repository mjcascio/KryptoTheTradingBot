#!/bin/bash

# stop_bot.sh - Script to stop the KryptoBot trading bot
echo "===== Stopping KryptoBot Trading Bot ====="

# Navigate to the script's directory
cd "$(dirname "$0")"

# Function to check if a PID is a valid bot process
check_bot_process() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi
    
    # Check if process exists and is a Python process
    if ps -p "$pid" -o command= | grep -q "python.*main.py"; then
        return 0
    fi
    return 1
}

# Function to safely read PID file
read_pid_file() {
    if [ ! -f "bot.pid" ]; then
        return 1
    fi
    
    local pid
    pid=$(cat "bot.pid" 2>/dev/null)
    if [ -z "$pid" ] || ! [[ "$pid" =~ ^[0-9]+$ ]]; then
        echo "Invalid PID file contents" >&2
        rm -f "bot.pid"
        return 1
    fi
    echo "$pid"
    return 0
}

# Function to stop the bot process
stop_bot_process() {
    local pid=$1
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempting to stop bot (attempt $attempt of $max_attempts)..."
        
        # Try graceful shutdown first
        if [ $attempt -eq 1 ]; then
            kill "$pid" 2>/dev/null
        else
            # Force kill on subsequent attempts
            kill -9 "$pid" 2>/dev/null
        fi
        
        # Wait and check if process is still running
        sleep 2
        if ! check_bot_process "$pid"; then
            return 0
        fi
        
        attempt=$((attempt + 1))
    done
    
    return 1
}

# Main script logic
pid=$(read_pid_file)
if [ $? -eq 0 ]; then
    if check_bot_process "$pid"; then
        echo "Found running bot process (PID: $pid)"
        if stop_bot_process "$pid"; then
            echo "✅ Bot process stopped successfully"
        else
            echo "❌ Failed to stop bot process"
        fi
    else
        echo "Found stale PID file (PID: $pid doesn't match a running bot)"
    fi
    
    # Always try to remove PID file
    if rm -f "bot.pid"; then
        echo "✅ PID file removed"
    else
        echo "❌ Failed to remove PID file"
    fi
else
    echo "⚠️ No valid PID file found"
    
    # Try to find and kill any running bot processes
    if pgrep -f "python.*main.py" > /dev/null; then
        echo "Found running bot process without PID file, attempting to stop..."
        pkill -f "python.*main.py"
        sleep 2
        
        if pgrep -f "python.*main.py" > /dev/null; then
            echo "❌ Failed to stop all bot processes"
            pkill -9 -f "python.*main.py"
        else
            echo "✅ Bot processes stopped"
        fi
    else
        echo "No running bot processes found"
    fi
fi

echo "Stop script completed." 