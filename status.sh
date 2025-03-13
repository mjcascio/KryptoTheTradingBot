#!/bin/bash

# Simple script to check the status of the KryptoBot trading system
echo "===== KryptoBot Trading System Status ====="

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check trading bot status
echo "Trading Bot Status:"
if [ -f "bot.pid" ]; then
    BOT_PID=$(cat bot.pid)
    if ps -p $BOT_PID > /dev/null; then
        echo "✅ Running (PID: $BOT_PID)"
        
        # Show uptime
        BOT_START_TIME=$(ps -p $BOT_PID -o lstart= 2>/dev/null)
        if [ -n "$BOT_START_TIME" ]; then
            echo "   Started: $BOT_START_TIME"
        fi
    else
        echo "❌ Not running (stale PID file)"
    fi
else
    echo "❌ Not running (no PID file)"
fi

# Check dashboard status
echo "Dashboard Status:"
if [ -f "dashboard.pid" ] && ps -p $(cat dashboard.pid) > /dev/null; then
    echo "✅ Running (PID: $(cat dashboard.pid))"
    
    # Show process uptime
    DASHBOARD_START_TIME=$(ps -p $(cat dashboard.pid) -o lstart= 2>/dev/null)
    if [ -n "$DASHBOARD_START_TIME" ]; then
        echo "   Started: $DASHBOARD_START_TIME"
    fi
    
    echo "   URL: http://localhost:5002"
else
    echo "❌ Not running"
    
    # Check for stale PID file
    if [ -f "dashboard.pid" ]; then
        echo "   (stale PID file)"
    fi
fi

echo ""
echo "Log Files:"
echo "  - Trading bot: logs/trading_bot.out"
echo "  - Dashboard: logs/dashboard.out"

echo ""
echo "To start all components: ./start_all.sh"
echo "To stop all components: ./stop_all.sh" 