# Alpaca Integration for KryptoBot

This document provides an overview of the Alpaca integration for KryptoBot, which ensures proper synchronization between your local system and Alpaca account.

## Overview

The Alpaca integration consists of several components:

1. **Data Synchronization**: Keeps your local trade history and positions in sync with Alpaca
2. **API Integration**: Provides a clean interface for interacting with Alpaca API
3. **Auto Sync Service**: Automatically synchronizes data at regular intervals
4. **Trade Hooks**: Ensures notifications are sent when trades are executed or positions change
5. **Trade Execution**: Execute trades directly through the Alpaca integration
6. **Account Monitoring**: Monitor your Alpaca account in real-time
7. **Performance Analysis**: Analyze your trading performance
8. **Watchlist Management**: Manage your Alpaca watchlists

## Components

### 1. Data Synchronization (`sync_alpaca_data.py`)

This script synchronizes your local trade history and positions with Alpaca:

```bash
python3 sync_alpaca_data.py
```

It fetches orders and positions from Alpaca and updates your local files:
- `data/trade_history.json`: Contains your trade history
- `data/positions.json`: Contains your current positions

### 2. API Integration (`alpaca_integration.py`)

This module provides a clean interface for interacting with Alpaca API:

```python
from alpaca_integration import AlpacaIntegration

# Get account information
account = AlpacaIntegration.get_account()

# Place an order
order = AlpacaIntegration.place_order(
    symbol="AAPL",
    side="buy",
    quantity=10,
    order_type="market",
    strategy="breakout"
)

# Get positions
positions = AlpacaIntegration.get_positions()

# Close a position
AlpacaIntegration.close_position("AAPL")

# Update positions and trigger hooks
AlpacaIntegration.update_positions()
```

### 3. Auto Sync Service (`auto_sync_alpaca.py`)

This script automatically synchronizes data at regular intervals:

```bash
# Run once
python3 auto_sync_alpaca.py --once

# Run as a service with default 15-minute interval
python3 auto_sync_alpaca.py

# Run as a service with custom interval
python3 auto_sync_alpaca.py --interval 5
```

### 4. Service Management Scripts

- `start_alpaca_sync.sh`: Starts the auto sync service in the background
- `stop_alpaca_sync.sh`: Stops the auto sync service

```bash
# Start the service
./start_alpaca_sync.sh

# Start with custom interval (in minutes)
./start_alpaca_sync.sh --interval 5

# Stop the service
./stop_alpaca_sync.sh
```

### 5. Trade Execution (`execute_alpaca_trade.py`)

This script allows you to execute trades directly through the Alpaca integration:

```bash
# Execute a market order
python3 execute_alpaca_trade.py AAPL buy 10

# Execute a limit order
python3 execute_alpaca_trade.py AAPL buy 10 --type limit --limit-price 150.00

# Execute a stop order
python3 execute_alpaca_trade.py AAPL sell 10 --type stop --stop-price 145.00

# Execute a stop-limit order
python3 execute_alpaca_trade.py AAPL sell 10 --type stop_limit --limit-price 145.00 --stop-price 146.00

# Execute a market order with a specific strategy
python3 execute_alpaca_trade.py AAPL buy 10 --strategy breakout
```

### 6. Account Monitoring (`monitor_alpaca.py`)

This script monitors your Alpaca account in real-time:

```bash
# Monitor with default 60-second refresh interval
python3 monitor_alpaca.py

# Monitor with custom refresh interval
python3 monitor_alpaca.py --refresh 30

# Monitor with custom number of orders to display
python3 monitor_alpaca.py --orders 10
```

### 7. Performance Analysis (`analyze_alpaca_performance.py`)

This script analyzes your Alpaca trading performance:

```bash
# Analyze performance for the last 30 days
python3 analyze_alpaca_performance.py

# Analyze performance for a custom number of days
python3 analyze_alpaca_performance.py --days 90

# Analyze performance and save results to a custom directory
python3 analyze_alpaca_performance.py --output custom_reports
```

### 8. Watchlist Management (`manage_alpaca_watchlist.py`)

This script allows you to manage your Alpaca watchlists:

```bash
# List all watchlists
python3 manage_alpaca_watchlist.py list

# Get a specific watchlist
python3 manage_alpaca_watchlist.py get WATCHLIST_ID

# Create a new watchlist
python3 manage_alpaca_watchlist.py create "My Watchlist" --symbols AAPL MSFT GOOGL

# Update a watchlist
python3 manage_alpaca_watchlist.py update WATCHLIST_ID --name "New Name" --symbols AAPL MSFT GOOGL

# Delete a watchlist
python3 manage_alpaca_watchlist.py delete WATCHLIST_ID

# Add a symbol to a watchlist
python3 manage_alpaca_watchlist.py add WATCHLIST_ID AAPL

# Remove a symbol from a watchlist
python3 manage_alpaca_watchlist.py remove WATCHLIST_ID AAPL
```

## Setup

1. Make sure your Alpaca API credentials are set in your `.env` file:

```
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

2. Install required packages:

```bash
pip install requests schedule python-dotenv pandas numpy matplotlib
```

3. Run the initial sync:

```bash
python3 sync_alpaca_data.py
```

4. Start the auto sync service:

```bash
./start_alpaca_sync.sh
```

## Troubleshooting

If you encounter issues with the Alpaca integration:

1. **Check API Credentials**: Ensure your API key and secret are correct in the `.env` file
2. **Check API Access**: Make sure your API key has the necessary permissions
3. **Check Logs**: Look at `alpaca_sync.log` and `logs/alpaca_sync.out` for error messages
4. **Manual Sync**: Try running `python3 sync_alpaca_data.py` to manually sync data
5. **Restart Service**: Stop and restart the auto sync service

## Integration with Trading Bot

The Alpaca integration is designed to work seamlessly with the KryptoBot trading system:

1. **Trade Execution**: Use `AlpacaIntegration.place_order()` to execute trades
2. **Position Management**: Use `AlpacaIntegration.get_positions()` and `AlpacaIntegration.close_position()` to manage positions
3. **Data Synchronization**: The auto sync service keeps your local data in sync with Alpaca
4. **Notifications**: Trade hooks are automatically called when trades are executed or positions change
5. **Performance Analysis**: Analyze your trading performance to improve your strategies
6. **Watchlist Management**: Manage your watchlists to track potential trading opportunities

By using these components, you ensure that your trading bot is always working with accurate data from your Alpaca account. 