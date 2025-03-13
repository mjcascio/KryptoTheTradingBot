#!/bin/bash

# run_diagnostic.sh - Comprehensive diagnostic script for KryptoBot
# This script checks all aspects of the bot's functionality and configuration

echo "===== KryptoBot System Diagnostic ====="
echo "Running comprehensive system check..."
echo ""

# Function to display section headers
section() {
    echo ""
    echo "===== $1 ====="
    echo ""
}

# Check if bot is running
section "PROCESS STATUS"
if [ -f "bot.pid" ] && ps -p $(cat bot.pid) > /dev/null; then
    echo "✅ Trading bot is running (PID: $(cat bot.pid))"
    BOT_RUNNING=true
    
    # Show process uptime
    BOT_START_TIME=$(ps -p $(cat bot.pid) -o lstart= 2>/dev/null)
    if [ -n "$BOT_START_TIME" ]; then
        echo "   Started: $BOT_START_TIME"
    fi
else
    echo "❌ Trading bot is NOT running"
    BOT_RUNNING=false
fi

if [ -f "dashboard.pid" ] && ps -p $(cat dashboard.pid) > /dev/null; then
    echo "✅ Dashboard is running (PID: $(cat dashboard.pid))"
    DASHBOARD_RUNNING=true
else
    echo "❌ Dashboard is NOT running"
    DASHBOARD_RUNNING=false
fi

# Check configuration files
section "CONFIGURATION CHECK"

# Check .env file
echo "Checking .env file:"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Check Alpaca API keys
    ALPACA_API_KEY=$(grep "ALPACA_API_KEY" .env | cut -d= -f2)
    ALPACA_SECRET_KEY=$(grep "ALPACA_SECRET_KEY" .env | cut -d= -f2)
    
    if [[ "$ALPACA_API_KEY" == "your_api_key_here" || "$ALPACA_API_KEY" == "PK1234567890ABCDEFGHIJ" ]]; then
        echo "❌ ERROR: Alpaca API keys are not properly configured!"
        echo "   You need to set your actual Alpaca API keys in the .env file."
        ALPACA_CONFIGURED=false
    else
        echo "✅ Alpaca API key is configured: ${ALPACA_API_KEY:0:4}...${ALPACA_API_KEY: -4}"
        ALPACA_CONFIGURED=true
    fi
else
    echo "❌ ERROR: .env file is missing!"
    ALPACA_CONFIGURED=false
fi

# Check config.py
echo ""
echo "Checking config.py:"
if [ -f "config.py" ]; then
    echo "✅ config.py file exists"
    
    # Check watchlist
    WATCHLIST_COUNT=$(grep -A 100 "WATCHLIST" config.py | grep -c '"[A-Z]\{1,5\}"')
    echo "   Watchlist contains approximately $WATCHLIST_COUNT symbols"
    
    if [ "$WATCHLIST_COUNT" -eq 0 ]; then
        echo "❌ ERROR: Watchlist is empty!"
    fi
    
    # Check if Alpaca is enabled - FIXED to check for Python-style "True"
    ALPACA_ENABLED=$(grep -A 5 '"alpaca"' config.py | grep -c '"enabled": True')
    if [ "$ALPACA_ENABLED" -gt 0 ]; then
        echo "✅ Alpaca is enabled in configuration"
    else
        echo "❌ ERROR: Alpaca is not enabled in configuration!"
    fi
else
    echo "❌ ERROR: config.py file is missing!"
fi

# Check log files
section "LOG ANALYSIS"

echo "Checking trading_bot.log for activity:"
if [ -f "logs/trading_bot.out" ]; then
    LOG_SIZE=$(du -h logs/trading_bot.out | cut -f1)
    echo "✅ Log file exists (Size: $LOG_SIZE)"
    
    # Check for recent activity
    LAST_LOG_TIME=$(tail -n 1 logs/trading_bot.out | grep -o "^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}" || echo "No timestamp found")
    echo "   Last log entry: $LAST_LOG_TIME"
    
    # Check for scanning activity
    SCAN_COUNT=$(grep -c "SCAN\|scan\|analyz\|process" logs/trading_bot.out)
    echo "   Scanning/analysis entries: $SCAN_COUNT"
    
    # Check for trading activity
    TRADE_COUNT=$(grep -c "trade\|order\|position" logs/trading_bot.out)
    echo "   Trading activity entries: $TRADE_COUNT"
    
    # Check for errors
    ERROR_COUNT=$(grep -c "error\|exception\|fail" logs/trading_bot.out)
    echo "   Error/exception entries: $ERROR_COUNT"
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo ""
        echo "Last 3 errors:"
        grep -i "error\|exception\|fail" logs/trading_bot.out | tail -n 3
    fi
else
    echo "❌ ERROR: Log file is missing!"
fi

# Check for market data access
section "MARKET DATA CHECK"

if [ "$BOT_RUNNING" = true ]; then
    echo "Checking if bot is receiving market data..."
    MARKET_DATA_ENTRIES=$(grep -c "market data\|price\|quote\|tick" logs/trading_bot.out)
    echo "   Market data entries: $MARKET_DATA_ENTRIES"
    
    if [ "$MARKET_DATA_ENTRIES" -eq 0 ]; then
        echo "❌ WARNING: No market data entries found in logs!"
        echo "   This may indicate the bot is not receiving market data."
    fi
else
    echo "⚠️ Bot is not running, cannot check market data access."
fi

# Check Alpaca connection
section "ALPACA CONNECTION CHECK"

if [ "$ALPACA_CONFIGURED" = true ]; then
    echo "Checking connection to Alpaca..."
    ALPACA_CONNECTED=$(grep -c "Connected to Alpaca\|Alpaca connection\|Alpaca API\|Alpaca Markets\|alpaca: Enabled" logs/trading_bot.out)
    
    if [ "$ALPACA_CONNECTED" -gt 0 ]; then
        echo "✅ Bot has attempted to connect to Alpaca"
    else
        echo "❌ WARNING: No evidence of Alpaca connection attempts in logs!"
    fi
    
    # Check for Alpaca errors
    ALPACA_ERRORS=$(grep -i "alpaca" logs/trading_bot.out | grep -i -c "error\|exception\|fail")
    if [ "$ALPACA_ERRORS" -gt 0 ]; then
        echo "❌ ERROR: Found $ALPACA_ERRORS Alpaca-related errors in logs!"
        echo ""
        echo "Last 3 Alpaca errors:"
        grep -i "alpaca" logs/trading_bot.out | grep -i "error\|exception\|fail" | tail -n 3
    else
        echo "✅ No Alpaca-related errors found in logs"
    fi
else
    echo "❌ Alpaca is not properly configured, skipping connection check."
fi

# Summary and recommendations
section "DIAGNOSTIC SUMMARY"

ISSUES_FOUND=0

if [ "$BOT_RUNNING" = false ]; then
    echo "❌ ISSUE: Trading bot is not running"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$DASHBOARD_RUNNING" = false ]; then
    echo "❌ ISSUE: Dashboard is not running"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$ALPACA_CONFIGURED" = false ]; then
    echo "❌ ISSUE: Alpaca API keys are not properly configured"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$WATCHLIST_COUNT" -eq 0 ]; then
    echo "❌ ISSUE: Watchlist is empty"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$SCAN_COUNT" -eq 0 ]; then
    echo "❌ ISSUE: No scanning/analysis activity detected"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$MARKET_DATA_ENTRIES" -eq 0 ]; then
    echo "❌ ISSUE: No market data entries detected"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$ALPACA_ERRORS" -gt 0 ]; then
    echo "❌ ISSUE: Alpaca-related errors detected"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

echo ""
if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo "✅ No major issues detected!"
else
    echo "❌ Found $ISSUES_FOUND issues that need attention!"
fi

section "RECOMMENDATIONS"

if [ "$ALPACA_CONFIGURED" = false ]; then
    echo "1. Update your Alpaca API keys in the .env file:"
    echo "   - Open .env file: nano .env"
    echo "   - Replace 'your_api_key_here' with your actual Alpaca API key"
    echo "   - Replace 'your_secret_key_here' with your actual Alpaca secret key"
    echo "   - Save the file and restart the bot"
fi

if [ "$BOT_RUNNING" = false ]; then
    echo "2. Start the trading bot:"
    echo "   - Run: ./start_bot.sh"
fi

if [ "$DASHBOARD_RUNNING" = false ]; then
    echo "3. Start the dashboard:"
    echo "   - Run: ./start_dashboard.sh"
fi

if [ "$ISSUES_FOUND" -gt 0 ]; then
    echo ""
    echo "After making these changes, run this diagnostic again to verify the issues are resolved."
fi

echo ""
echo "===== Diagnostic Complete =====" 