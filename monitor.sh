#!/bin/bash

# monitor.sh - Simple script to monitor the bot's activity

echo "===== KryptoBot Activity Monitor ====="
echo "This script shows you the bot's scanning and trading activity"
echo ""

# Check if bot is running
if [ ! -f "bot.pid" ] || ! ps -p $(cat bot.pid) > /dev/null; then
    echo "❌ Trading bot is not running! Start it with ./start_bot.sh"
    exit 1
fi

echo "✅ Bot is running (PID: $(cat bot.pid))"
echo ""

# Show the most recent scanning activity
echo "===== Recent Scanning Activity ====="
echo "Showing the last 20 scan entries:"
echo ""
grep "SCAN\|Analyzing\|checking\|PASSED\|FAILED\|SIGNAL\|TRADE\|DECISION" logs/trading_bot.out | tail -n 20
echo ""
echo "===== End of Recent Activity ====="
echo ""

# Show options
echo "For more detailed monitoring, use one of these tools:"
echo "1. ./monitor_activity.sh - Interactive monitoring of scanning activity"
echo "2. ./monitor_trades.sh - Interactive monitoring of trading activity"
echo "3. ./watch_symbols.sh - Track specific symbols"
echo ""
echo "To generate more scanning activity, run: python force_scan.py"
echo ""
# Modified for macOS and Linux compatibility
echo "To see live updates, run this exact command:"
echo ""
echo "For macOS:"
echo "tail -f logs/trading_bot.out | grep --line-buffered \"SCAN\|Analyzing\|checking\|PASSED\|FAILED\|SIGNAL\|TRADE\|DECISION\""
echo ""
echo "For Linux:"
echo "tail -f logs/trading_bot.out | grep --line-buffered \"SCAN\|Analyzing\|checking\|PASSED\|FAILED\|SIGNAL\|TRADE\|DECISION\""
echo ""
echo "Or simply run: ./live_monitor.sh for optimized real-time monitoring" 