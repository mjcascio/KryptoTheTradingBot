#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start the trading bot
python main.py 