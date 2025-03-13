#!/bin/bash
#
# Start Ensemble-Enhanced Trading Bot
#
# This script starts the trading bot with ensemble learning integration.
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
TRAIN_ENSEMBLE=false
VOTING="soft"
WEIGHTS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --train-ensemble)
            TRAIN_ENSEMBLE=true
            shift
            ;;
        --voting)
            shift
            VOTING="$1"
            shift
            ;;
        --weights)
            shift
            WEIGHTS="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--train-ensemble] [--voting soft|hard] [--weights WEIGHTS]"
            exit 1
            ;;
    esac
done

# Build the command
CMD="python run_ensemble_bot.py"

if [ "$TRAIN_ENSEMBLE" = true ]; then
    CMD="$CMD --train-ensemble"
fi

CMD="$CMD --voting $VOTING"

if [ -n "$WEIGHTS" ]; then
    CMD="$CMD --weights $WEIGHTS"
fi

# Print the command
echo "Starting ensemble-enhanced trading bot with command:"
echo "$CMD"

# Run the command
$CMD 