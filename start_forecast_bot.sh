#!/bin/bash
#
# Start Trading Bot with Time Series Forecasting
#
# This script starts the trading bot with time series forecasting integration.
# It handles activating the virtual environment and passing command line arguments.

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Parse command line arguments
TRAIN_LSTM=false
TRAIN_GRU=false
SYMBOLS=""
CONFIG="config/config.json"
FORECAST_CONFIG="config/forecasting_settings.json"

while [[ $# -gt 0 ]]; do
    case $1 in
        --train-lstm)
            TRAIN_LSTM=true
            shift
            ;;
        --train-gru)
            TRAIN_GRU=true
            shift
            ;;
        --symbols)
            shift
            SYMBOLS="$1"
            shift
            ;;
        --config)
            shift
            CONFIG="$1"
            shift
            ;;
        --forecast-config)
            shift
            FORECAST_CONFIG="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 run_forecast_bot.py"

if [ "$TRAIN_LSTM" = true ]; then
    CMD="$CMD --train-lstm"
fi

if [ "$TRAIN_GRU" = true ]; then
    CMD="$CMD --train-gru"
fi

if [ -n "$SYMBOLS" ]; then
    CMD="$CMD --symbols $SYMBOLS"
fi

CMD="$CMD --config $CONFIG --forecast-config $FORECAST_CONFIG"

# Print command
echo "Running: $CMD"

# Execute command
eval $CMD 