#!/bin/bash
#
# Start ML-Enhanced Trading Bot
#
# This script starts the trading bot with ML integration.
#

# Set the directory to the script's location
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Parse command line arguments
TRAIN_ML=false
TRAIN_ANOMALY=false
SYMBOLS=""
EPOCHS=50
BATCH_SIZE=32

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --train-ml)
            TRAIN_ML=true
            shift
            ;;
        --train-anomaly)
            TRAIN_ANOMALY=true
            shift
            ;;
        --symbols)
            shift
            SYMBOLS="$1"
            shift
            ;;
        --epochs)
            shift
            EPOCHS="$1"
            shift
            ;;
        --batch-size)
            shift
            BATCH_SIZE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build the command
CMD="python run_ml_bot.py"

if [ "$TRAIN_ML" = true ]; then
    CMD="$CMD --train-ml"
fi

if [ "$TRAIN_ANOMALY" = true ]; then
    CMD="$CMD --train-anomaly"
fi

if [ -n "$SYMBOLS" ]; then
    CMD="$CMD --symbols $SYMBOLS"
fi

CMD="$CMD --epochs $EPOCHS --batch-size $BATCH_SIZE"

# Print the command
echo "Starting ML-enhanced trading bot with command:"
echo "$CMD"

# Run the command
$CMD 