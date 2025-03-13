# KryptoBot Terminal Commands

This document lists all available terminal commands for KryptoBot.

## Trading Control
- `start` - Start the trading bot (both stocks and options)
- `stop` - Stop the trading bot (both stocks and options)
- `start-stocks` - Start stock trading only
- `stop-stocks` - Stop stock trading only
- `start-options` - Start options trading only
- `stop-options` - Stop options trading only

## Status and Information
- `status` - Display current bot status
- `positions` - Show current positions
- `trades` - Show recent trades
- `performance` - Show performance metrics
- `health` - Display system health report
- `diagnostics` - Run system diagnostics

## Configuration
- `config` - Show current configuration
- `set-strategy <id>` - Change trading strategy
- `set-risk <level>` - Change risk level (low/medium/high)
- `set-platform <platform>` - Switch trading platform

## Data and Analysis
- `scan` - Run market scanner
- `analyze <symbol>` - Analyze specific symbol
- `forecast` - Get market forecast
- `backtest <strategy>` - Run strategy backtest

## Maintenance
- `update` - Update trading bot
- `logs` - Show recent logs
- `clear-cache` - Clear cached data
- `reset-metrics` - Reset trading metrics

## Help
- `help` - Show available commands
- `version` - Show bot version
- `about` - Show bot information

## Note
Commands can be run from the terminal where KryptoBot is running. Use `help <command>` for detailed information about specific commands.

## Overview

KryptoBot is configured to use **Alpaca** as its only trading platform. The system consists of two main components:
- **Trading Bot**: Handles the trading logic and connects to Alpaca
- **Dashboard**: Provides a web interface to monitor trading activity

## Getting Started

### Opening Terminal
1. Open **Terminal** on your Mac (find it in Applications > Utilities > Terminal)
2. Navigate to the KryptoBot directory:
   ```bash
   cd /Users/mjcascio/Documents/KryptoTheTradingBot
   ```

### Basic Commands

Here are the essential commands for managing KryptoBot:

| Action | Command | Description |
|--------|---------|-------------|
| Start everything | `./start_all.sh` | Starts both the trading bot and dashboard |
| Stop everything | `./stop_all.sh` | Stops both the trading bot and dashboard |
| Check status | `./status.sh` | Shows if the bot and dashboard are running |

### Using Terminal Effectively

**Important**: When using commands that show continuous output (like `tail -f`):
- Press **Control+C** to stop the output and regain control of the Terminal
- This doesn't stop the bot or dashboard, just the command showing the output
- After pressing Control+C, you can enter new commands

Example workflow:
1. Start the bot: `./start_all.sh`
2. View logs: `tail -f logs/trading_bot.out`
3. Press **Control+C** to stop viewing logs
4. Enter another command (the bot continues running)

## Detailed Commands

### Starting Components

**Start the entire system (bot + dashboard):**
```bash
./start_all.sh
```

**Start only the trading bot:**
```bash
./start_bot.sh
```

**Start only the dashboard:**
```bash
./start_dashboard.sh
```

### Stopping Components

**Stop the entire system:**
```bash  
./stop_all.sh
```

**Stop only the trading bot:**
```bash
./stop_bot.sh
```

**Stop only the dashboard:**
```bash
./stop_dashboard.sh
```

### Restarting Components

**Restart the entire system (bot + dashboard):**
```bash
./restart_all.sh
```

**Restart only the trading bot:**
```bash
./restart_bot.sh
```

**Restart only the dashboard:**
```bash
./restart_dashboard.sh
```

These restart commands will properly stop the components, remove any stale PID files, and start them again. Use these commands if you encounter any issues with the bot or dashboard not responding.

### Monitoring

**Check the status of all components:**
```bash
./status.sh
```

**View trading bot logs:**
```bash
tail -f logs/trading_bot.out
```

**View dashboard logs:**
```bash
tail -f logs/dashboard.out
```

## Enhanced Monitoring Tools

KryptoBot comes with specialized monitoring tools to help you track the bot's activity in real-time:

### Interactive Monitoring Scripts

**1. Simple Activity Monitor:**
```bash
./monitor.sh
```
This script provides a simple, non-interactive view of:
- Recent scanning activity (last 20 entries)
- Live activity as it happens
- Color-highlighted output for better readability

**2. Monitor Trading Activity:**
```bash
./monitor_trades.sh
```
This interactive script provides a menu to monitor:
- Symbol scanning
- Trading signals
- Executed trades
- Full activity
- Custom filters

**3. Monitor Scanning Process:**
```bash
./monitor_activity.sh
```
This script focuses on the scanning process with:
- Color-coded output
- Basic or detailed scanning views
- Full decision process tracking

**4. Watch Specific Symbols:**
```bash
./watch_symbols.sh
```
This tool lets you:
- Track a specific symbol (e.g., AAPL)
- Monitor multiple symbols at once
- See which symbols pass initial screening
- Identify and watch the most active symbols

### Using the Monitoring Tools

1. Start the bot if it's not already running:
   ```bash
   ./start_bot.sh
   ```

2. Run any of the monitoring scripts:
   ```bash
   ./monitor.sh
   ```

3. Follow the on-screen menu to select what you want to monitor (for interactive tools)

4. Press **Control+C** when you want to exit the monitoring tool

### Generating Test Activity

If you want to see how the monitoring tools work without waiting for actual trading activity:

```bash
python force_scan.py
```

This script simulates the bot scanning symbols and making trading decisions, which you can then observe using the monitoring tools.

## New Enhanced Trading Tools

### Start Bot with Monitoring

The new `start_bot_with_monitor.sh` script allows you to start the bot and automatically launch monitoring in a single command:

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

### Execute Real Trades

The new `execute_trade.py` script allows you to execute real trades with Alpaca directly:

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

### Understanding Trade Execution

It's important to understand the difference between the `force_scan.py` script and real trade execution:

1. **force_scan.py**: This script simulates the scanning and trading process by writing log entries to the log file. It does not execute real trades with Alpaca. It's useful for testing and monitoring the bot's decision-making process.

2. **execute_trade.py**: This script executes real trades with Alpaca. It connects to your Alpaca account and places actual orders. Use this script when you want to execute real trades.

## Alpaca API Configuration

KryptoBot uses Alpaca for trading. You need to configure your Alpaca API key:

### Update Your API Key

Use the API key update tool:
```bash
./update_api_key.sh
```

This interactive script will:
1. Prompt you for your Alpaca API key
2. Validate the key format
3. Update the .env file
4. Offer to restart the bot

**Note**: KryptoBot is configured to work with just an API key (no secret key required).

### API Key Format

Your Alpaca API key should:
- Start with PK (paper trading) or AK (live trading)
- Be followed by letters and numbers
- Example: `PK1234567890ABCDEFGHIJ`

### Verifying API Configuration

To check if your API key is properly configured:
```bash
./run_diagnostic.sh
```

This will check your API configuration and other aspects of the system.

## Viewing Trades and Trading Activity

### Using the Dashboard (Recommended)

The easiest way to view trades is through the dashboard:

1. Make sure the dashboard is running:
   ```bash
   ./status.sh
   ```

2. Open the dashboard in your browser:
   ```
   http://localhost:5002
   ```

3. On the dashboard, you can view:
   - **Current Positions**: Active trades the bot is holding
   - **Recent Trades**: History of completed trades
   - **Bot Activity**: Log of trading decisions and actions
   - **Trading Signals**: Potential future trades the bot is considering

### Using Log Files

To see detailed trading information in the logs:

1. View real-time trading activity:
   ```bash
   tail -f logs/trading_bot.out | grep "TRADE"
   ```

2. View planned trades and signals:
   ```bash
   tail -f logs/trading_bot.out | grep "SIGNAL"
   ```

3. View all trading decisions:
   ```bash
   tail -f logs/trading_bot.out | grep -E "TRADE|SIGNAL|POSITION|ORDER"
   ```

4. **Remember**: Press **Control+C** to stop viewing logs and enter new commands

### Checking Alpaca Account Directly

You can also verify trades on your Alpaca account:

1. Log in to your Alpaca account at https://app.alpaca.markets
2. Navigate to the "Positions" or "Orders" section
3. All trades made by the bot will appear in your Alpaca account

## Monitoring Ticker Symbol Scanning

To see the bot scanning through ticker symbols and making trading decisions in real-time:

### View the Scanning Process

1. Watch the bot scan through all ticker symbols:
   ```bash
   tail -f logs/trading_bot.out | grep "SCAN"
   ```

2. See which symbols are being analyzed:
   ```bash
   tail -f logs/trading_bot.out | grep "Analyzing"
   ```

3. View parameter checks for each symbol:
   ```bash
   tail -f logs/trading_bot.out | grep -E "parameter|threshold|criteria"
   ```

### View Decision-Making Process

1. See which symbols pass initial screening:
   ```bash
   tail -f logs/trading_bot.out | grep "passed initial screening"
   ```

2. View detailed analysis of promising symbols:
   ```bash
   tail -f logs/trading_bot.out | grep -A 10 "Detailed analysis"
   ```
   This shows 10 lines after each "Detailed analysis" mention

3. See final trade decisions:
   ```bash
   tail -f logs/trading_bot.out | grep -E "Decision|decided to|trade opportunity"
   ```

### Comprehensive View

To see the entire scanning and decision-making process for all symbols:

```bash
tail -f logs/trading_bot.out
```

This shows all log output, including the scanning process, parameter checks, and trade decisions.

For a cleaner view focused on just the scanning process:

```bash
tail -f logs/trading_bot.out | grep -E "SCAN|Analyzing|parameter|threshold|passed|failed|Decision"
```

**Note**: Remember to press **Control+C** when you want to stop viewing the output and enter a new command.

## Bot Configuration

### Viewing Current Configuration

To see the current configuration settings:

```bash
cat config.py
```

### Key Configuration Parameters

The bot's behavior is controlled by these key parameters in `config.py`:

- **WATCHLIST**: List of ticker symbols the bot will scan
- **MAX_POSITION_SIZE_PCT**: Maximum position size as percentage of portfolio
- **STOP_LOSS_PCT**: Stop loss percentage for risk management
- **TAKE_PROFIT_PCT**: Take profit percentage for profit targets
- **BREAKOUT_PARAMS**: Parameters for breakout detection
- **TREND_PARAMS**: Parameters for trend following strategies

### Modifying Configuration

To modify the bot's configuration:

1. Edit the config file:
   ```bash
   nano config.py
   ```

2. Save changes (Ctrl+O, then Enter, then Ctrl+X)

3. Restart the bot for changes to take effect:
   ```bash
   ./stop_bot.sh
   ./start_bot.sh
   ```

## System Diagnostics

### Running a Complete System Diagnostic

To check all aspects of the system:

```bash
./run_diagnostic.sh
```

This comprehensive diagnostic tool will check:
- Process status (bot and dashboard)
- Configuration files
- Watchlist configuration
- Alpaca API connection
- Log activity
- Market data access

### Fixing Configuration Issues

If the diagnostic identifies issues, you can fix them with:

```bash
python fix_config.py
```

This script will attempt to fix common configuration issues automatically.

## Performance Monitoring

### View Bot Performance

To see how the bot is performing:

1. Check overall performance metrics:
   ```bash
   tail -f logs/trading_bot.out | grep "Performance"
   ```

2. View profit and loss statistics:
   ```bash
   tail -f logs/trading_bot.out | grep -E "P&L|profit|loss"
   ```

3. Check win rate and trade statistics:
   ```bash
   tail -f logs/trading_bot.out | grep -E "win rate|success rate|statistics"
   ```

### Performance Dashboard

The dashboard provides visual performance metrics:

1. Open the dashboard at http://localhost:5002
2. Navigate to the "Performance" section
3. View charts showing:
   - Equity curve
   - Win/loss ratio
   - Daily P&L
   - Strategy performance breakdown

## Data Management

### Backup Trading Data

To backup your trading data:

```bash
mkdir -p backups
cp -r data/* backups/$(date +%Y%m%d)/
```

### Clear Old Logs

To clear old log files (while preserving recent logs):

```bash
find logs -name "*.out" -type f -mtime +7 -delete
```

## Advanced Usage

### Running in Background Mode

To run the bot in true background mode (persists after terminal closes):

```bash
nohup ./start_all.sh > /dev/null 2>&1 &
```

### Scheduled Restarts

To set up a daily restart at 4 AM (requires crontab):

```bash
(crontab -l 2>/dev/null; echo "0 4 * * * cd $(pwd) && ./restart_all.sh") | crontab -
```

### Debug Mode

To run the bot in debug mode with more verbose logging:

```bash
DEBUG=1 ./start_bot.sh
```

## Accessing the Dashboard

Once started, the dashboard is available at:
- **URL**: http://localhost:5002
- Open this address in any web browser on your Mac

## Troubleshooting

If you encounter issues with the scripts:

1. **Permission errors**: Make sure the scripts are executable
   ```bash
   chmod +x *.sh
   ```

2. **"Command not found"**: Make sure you're in the correct directory
   ```bash
   cd /Users/mjcascio/Documents/KryptoTheTradingBot
   ```

3. **Bot or dashboard not starting**: Check the logs for errors
   ```bash
   cat logs/trading_bot.out
   cat logs/dashboard.out
   ```

4. **Stale PID files**: If you see errors about processes not running but PID files exist, use the restart scripts:
   ```bash
   # For the bot:
   ./restart_bot.sh
   
   # For the dashboard:
   ./restart_dashboard.sh
   
   # For both:
   ./restart_all.sh
   ```
   These scripts will automatically remove stale PID files and restart the components.

5. **Connection issues**: If the bot can't connect to Alpaca:
   ```bash
   # Check your .env file for correct API keys
   cat .env | grep ALPACA
   ```

6. **Dashboard not showing data**: Restart both components:
   ```bash
   ./restart_all.sh
   ```

7. **Terminal stuck in output view**: Press **Control+C** to regain control without stopping the bot

8. **No scanning activity visible**: Generate test activity:
   ```bash
   python force_scan.py
   ```

9. **Trade execution issues**: If trades are not being executed:
   - Check the logs for any error messages
   - Verify that your Alpaca account has sufficient buying power
   - Ensure that the market is open (trades can only be executed during market hours)
   - Check that the symbol you're trying to trade is available on Alpaca

## Important Notes

- The trading bot is configured to use **Alpaca only** - MetaTrader is disabled
- All trading operations will be performed through Alpaca
- The dashboard displays data from Alpaca only
- Always check the status of the system before starting or stopping components
- Use your Mac's Terminal (not the terminal in Cursor IDE) for best results
- The bot follows market hours and will not trade during off-hours
- All configuration is stored in `config.py` and environment variables in `.env`
- **Control+C** stops viewing output but doesn't stop the bot or dashboard
- Alpaca API configuration requires only an API key (no secret key needed)
- The `force_scan.py` script simulates trading activity but does not execute real trades
- Use `execute_trade.py` when you want to execute real trades with Alpaca

## Quick Reference

1. **Start everything**: `./start_all.sh`
2. **Start with monitoring**: `./start_bot_with_monitor.sh`
3. **Execute real trade**: `python execute_trade.py AAPL buy 1`
4. **Check status**: `./status.sh`
5. **View dashboard**: Open http://localhost:5002 in browser
6. **Monitor bot activity**: `./monitor.sh`
7. **Watch specific symbols**: `./watch_symbols.sh`
8. **Update API key**: `./update_api_key.sh`
9. **Generate test activity**: `python force_scan.py`
10. **Run diagnostics**: `./run_diagnostic.sh`
11. **Restart everything**: `./restart_all.sh`
12. **Stop viewing output**: Press **Control+C** (bot continues running)
13. **Stop everything**: `./stop_all.sh` 