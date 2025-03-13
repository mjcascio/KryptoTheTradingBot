# KryptoBot Trading Tools

This document provides information about the enhanced trading tools available for KryptoBot.

## New Tools

### 1. Start Bot with Monitoring

The `start_bot_with_monitor.sh` script allows you to start the bot and automatically launch monitoring in a single command.

```bash
./start_bot_with_monitor.sh [OPTIONS]
```

#### Options:

- `-b, --basic`: Start bot with basic monitoring (default)
- `-d, --detailed`: Start bot with detailed monitoring
- `-f, --full`: Start bot with full activity monitoring
- `-s, --symbol SYM`: Start bot and monitor specific symbol(s)
- `-t, --trades`: Start bot and monitor only trades
- `-h, --help`: Show help message

#### Examples:

```bash
# Start with basic monitoring (default)
./start_bot_with_monitor.sh

# Start with detailed monitoring
./start_bot_with_monitor.sh --detailed

# Start and monitor specific symbols
./start_bot_with_monitor.sh -s AAPL,MSFT

# Start and monitor only trades
./start_bot_with_monitor.sh --trades
```

### 2. Execute Real Trades

The `execute_trade.py` script allows you to execute real trades with Alpaca directly.

```bash
python execute_trade.py SYMBOL SIDE QUANTITY [OPTIONS]
```

#### Arguments:

- `SYMBOL`: Stock symbol (e.g., AAPL)
- `SIDE`: Trade side (buy or sell)
- `QUANTITY`: Number of shares to trade

#### Options:

- `--type`: Order type (market or limit, default: market)
- `--price`: Limit price (required for limit orders)
- `--time-in-force`: Time in force (day, gtc, ioc, default: day)

#### Examples:

```bash
# Buy 1 share of AAPL at market price
python execute_trade.py AAPL buy 1

# Sell 2 shares of MSFT at market price
python execute_trade.py MSFT sell 2

# Buy 1 share of GOOGL with a limit order
python execute_trade.py GOOGL buy 1 --type limit --price 150.00
```

## Understanding Trade Execution

### Force Scan vs. Real Trades

It's important to understand the difference between the `force_scan.py` script and real trade execution:

1. **force_scan.py**: This script simulates the scanning and trading process by writing log entries to the log file. It does not execute real trades with Alpaca. It's useful for testing and monitoring the bot's decision-making process.

2. **execute_trade.py**: This script executes real trades with Alpaca. It connects to your Alpaca account and places actual orders. Use this script when you want to execute real trades.

### Verifying Trades

To verify that a trade has been executed:

1. Check the output of the `execute_trade.py` script for confirmation
2. Log in to your Alpaca account and check the Orders or Positions section
3. Run `./monitor.sh` to see if the trade appears in the logs

## Troubleshooting

### API Key Issues

If you encounter issues with the Alpaca API key:

1. Check that your API key is correctly set in the `.env` file
2. Run `./update_api_key.sh` to update your API key
3. Verify that the API key has the necessary permissions in your Alpaca account

### Trade Execution Issues

If trades are not being executed:

1. Check the logs for any error messages
2. Verify that your Alpaca account has sufficient buying power
3. Ensure that the market is open (trades can only be executed during market hours)
4. Check that the symbol you're trying to trade is available on Alpaca

## Best Practices

1. Always start with small quantities when testing real trades
2. Use paper trading (paper-api.alpaca.markets) for testing
3. Monitor your trades closely using the monitoring tools
4. Check your Alpaca account regularly to verify trades 