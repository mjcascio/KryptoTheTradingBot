#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if dashboard PID file exists
if [ -f "dashboard.pid" ]; then
    PID=$(cat dashboard.pid)
    
    # Check if process is running
    if ps -p $PID > /dev/null; then
        echo "Stopping dashboard with PID: $PID"
        kill $PID
        
        # Wait for process to terminate gracefully
        for i in {1..5}; do
            if ! ps -p $PID > /dev/null; then
                echo "Dashboard stopped successfully."
                rm dashboard.pid
                exit 0
            fi
            echo "Waiting for dashboard to stop gracefully... ($i/5)"
            sleep 1
        done
        
        # Force kill if still running
        echo "Force stopping dashboard..."
        kill -9 $PID 2>/dev/null
        rm dashboard.pid
        echo "Dashboard stopped forcefully."
    else
        echo "Dashboard process (PID: $PID) is not running."
        rm dashboard.pid
    fi
else
    # Try to find and kill any running dashboard process on port 5001
    DASHBOARD_PID=$(lsof -i :5001 | grep -v PID | awk '{print $2}' | head -n 1)
    
    if [ -n "$DASHBOARD_PID" ]; then
        echo "Found dashboard running on port 5001 with PID: $DASHBOARD_PID"
        kill $DASHBOARD_PID
        sleep 1
        
        # Force kill if still running
        if ps -p $DASHBOARD_PID > /dev/null; then
            echo "Force stopping dashboard..."
            kill -9 $DASHBOARD_PID 2>/dev/null
        fi
        
        echo "Dashboard stopped."
    else
        echo "No running dashboard found."
    fi
fi 