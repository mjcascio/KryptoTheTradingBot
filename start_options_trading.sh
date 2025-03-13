#!/bin/bash
# Start Options Trading Service
#
# This script starts the options trading service for KryptoBot.
# It can be used to enable options trading capabilities in the bot.

echo "===== Starting KryptoBot Options Trading Service ====="

# Check if the service is already running
if [ -f "options_trading.pid" ]; then
    PID=$(cat options_trading.pid)
    if ps -p $PID > /dev/null; then
        echo "Options Trading Service is already running with PID $PID"
        echo "To restart, run: ./stop_options_trading.sh && ./start_options_trading.sh"
        exit 1
    else
        echo "Found stale PID file. Removing..."
        rm options_trading.pid
    fi
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if required files exist
if [ ! -f "options_trading.py" ]; then
    echo "Error: options_trading.py not found."
    exit 1
fi

# Make sure the script is executable
chmod +x test_options_trading.py

# Create necessary directories
mkdir -p logs
mkdir -p data/options

# Start the options trading service
echo "Starting Options Trading Service..."

# Check if we're running in paper mode or live mode
PAPER_MODE="--paper"
if [ "$1" == "--live" ]; then
    PAPER_MODE="--live"
    echo "WARNING: Running in LIVE trading mode. Real money will be used!"
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborting..."
        exit 1
    fi
fi

# Start the service in the background
nohup python3 -c "
import time
import logging
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/options_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('options_service')

# Import options trading module
try:
    from options_trading import OptionsTrading
    logger.info('Options Trading module imported successfully')
except Exception as e:
    logger.error(f'Error importing Options Trading module: {e}')
    sys.exit(1)

# Initialize options trading
paper_mode = '$PAPER_MODE' == '--paper'
logger.info(f'Initializing Options Trading (Paper Mode: {paper_mode})')
try:
    options = OptionsTrading(paper=paper_mode)
    logger.info('Options Trading initialized successfully')
except Exception as e:
    logger.error(f'Error initializing Options Trading: {e}')
    sys.exit(1)

# Handle signals
def handle_signal(sig, frame):
    logger.info('Received signal to shut down')
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# Main loop
logger.info('Options Trading Service started')
try:
    while True:
        # This is a placeholder for any periodic tasks
        # In a real implementation, you might check for signals to execute trades
        time.sleep(60)
except Exception as e:
    logger.error(f'Error in main loop: {e}')
    sys.exit(1)
" > logs/options_service.out 2>&1 &

# Save the PID
echo $! > options_trading.pid

echo "Options Trading Service started with PID $(cat options_trading.pid)"
echo "Logs are available at logs/options_service.log and logs/options_service.out"
echo "To stop the service, run: ./stop_options_trading.sh"

# If --scan-now argument is provided, run an initial scan
if [ "$1" == "--scan-now" ] || [ "$2" == "--scan-now" ]; then
    echo "Running initial options scan..."
    ./test_options_trading.py --action chain --symbol SPY
fi 