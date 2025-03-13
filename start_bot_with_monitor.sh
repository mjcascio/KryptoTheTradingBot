#!/bin/bash

# start_bot_with_monitor.sh - Script to start the trading bot and launch monitoring

# Function to display usage information
show_usage() {
    echo "Usage: ./start_bot_with_monitor.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --basic       Start bot with basic monitoring (default)"
    echo "  -d, --detailed    Start bot with detailed monitoring"
    echo "  -f, --full        Start bot with full activity monitoring"
    echo "  -s, --symbol SYM  Start bot and monitor specific symbol(s)"
    echo "  -t, --trades      Start bot and monitor only trades"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start_bot_with_monitor.sh -b"
    echo "  ./start_bot_with_monitor.sh --detailed"
    echo "  ./start_bot_with_monitor.sh -s AAPL,MSFT"
    echo "  ./start_bot_with_monitor.sh --trades"
}

# Function to start the bot
start_bot() {
    echo "===== Starting KryptoBot Trading System ====="
    
    # Check if bot is already running
    if [ -f "bot.pid" ] && ps -p $(cat bot.pid) > /dev/null; then
        echo "⚠️  Trading bot is already running (PID: $(cat bot.pid))"
        echo "If you want to restart it, run ./restart_bot.sh first"
    else
        echo "Starting trading bot..."
        ./start_bot.sh
        
        # Wait for bot to initialize
        sleep 2
        
        if [ -f "bot.pid" ] && ps -p $(cat bot.pid) > /dev/null; then
            echo "✅ Trading bot started successfully (PID: $(cat bot.pid))"
        else
            echo "❌ Failed to start trading bot"
            exit 1
        fi
    fi
    
    # Check if dashboard is running
    if [ -f "dashboard.pid" ] && ps -p $(cat dashboard.pid) > /dev/null; then
        echo "✅ Dashboard is already running (PID: $(cat dashboard.pid))"
    else
        echo "Starting dashboard..."
        ./start_dashboard.sh
        
        # Wait for dashboard to initialize
        sleep 2
        
        if [ -f "dashboard.pid" ] && ps -p $(cat dashboard.pid) > /dev/null; then
            echo "✅ Dashboard started successfully (PID: $(cat dashboard.pid))"
            echo "   Dashboard URL: http://localhost:5002"
        else
            echo "❌ Failed to start dashboard"
        fi
    fi
    
    echo ""
    echo "===== System Status ====="
    ./status.sh
    echo ""
}

# Function to run basic monitoring
run_basic_monitoring() {
    echo "===== Starting Basic Monitoring ====="
    echo "Press Ctrl+C to stop monitoring (bot will continue running)"
    echo ""
    tail -f logs/trading_bot.out | grep "SCAN\|SIGNAL\|TRADE\|DECISION"
}

# Function to run detailed monitoring
run_detailed_monitoring() {
    echo "===== Starting Detailed Monitoring ====="
    echo "Press Ctrl+C to stop monitoring (bot will continue running)"
    echo ""
    tail -f logs/trading_bot.out | grep "SCAN\|Analyzing\|checking\|PASSED\|FAILED\|SIGNAL\|TRADE\|DECISION"
}

# Function to run full monitoring
run_full_monitoring() {
    echo "===== Starting Full Activity Monitoring ====="
    echo "Press Ctrl+C to stop monitoring (bot will continue running)"
    echo ""
    tail -f logs/trading_bot.out
}

# Function to monitor specific symbols
monitor_symbols() {
    local symbols="$1"
    local grep_pattern=$(echo "$symbols" | sed 's/,/\\|/g')
    
    echo "===== Monitoring Symbols: $symbols ====="
    echo "Press Ctrl+C to stop monitoring (bot will continue running)"
    echo ""
    tail -f logs/trading_bot.out | grep -E "$grep_pattern"
}

# Function to monitor trades only
monitor_trades() {
    echo "===== Monitoring Trades Only ====="
    echo "Press Ctrl+C to stop monitoring (bot will continue running)"
    echo ""
    tail -f logs/trading_bot.out | grep -E "SIGNAL\|TRADE\|ORDER\|BUY\|SELL\|position\|executed"
}

# Main script execution
if [ "$#" -eq 0 ]; then
    # Default behavior: start bot with basic monitoring
    start_bot
    run_basic_monitoring
else
    case "$1" in
        -b|--basic)
            start_bot
            run_basic_monitoring
            ;;
        -d|--detailed)
            start_bot
            run_detailed_monitoring
            ;;
        -f|--full)
            start_bot
            run_full_monitoring
            ;;
        -s|--symbol)
            if [ -z "$2" ]; then
                echo "Error: Symbol(s) must be specified with -s or --symbol"
                show_usage
                exit 1
            fi
            start_bot
            monitor_symbols "$2"
            ;;
        -t|--trades)
            start_bot
            monitor_trades
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
fi 