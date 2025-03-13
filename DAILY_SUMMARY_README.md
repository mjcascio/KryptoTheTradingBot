# KryptoBot Daily Summary

This document describes the daily summary feature of KryptoBot, which provides end-of-day trading reports.

## Overview

The daily summary feature automatically generates and sends a comprehensive report at the end of each trading day. The report includes:

- Summary of trades executed during the day
- Current active positions
- Performance metrics (P&L, win rate, Sharpe ratio)
- Performance charts (daily and cumulative P&L)

Reports can be delivered via email, Telegram, and are also saved locally as both text and HTML files.

## Features

### Trade Summary

- List of all trades executed during the day
- Entry and exit prices
- Profit/loss for each trade
- Strategy used for each trade
- Summary statistics (total profit/loss, win rate, etc.)

### Active Positions

- List of all currently open positions
- Entry prices and current prices
- Unrealized profit/loss
- Strategy used for each position

### Performance Metrics

- Total profit/loss
- Win rate
- Sharpe ratio
- Daily and cumulative P&L charts

## Usage

### Check Today's Trades

To check if the bot executed any trades today:

```bash
./check_trades.py
```

Options:
- `--days N`: Check trades from the last N days (default: 1 for today only)
- `--positions`: Show active positions

Examples:
```bash
# Check today's trades
./check_trades.py

# Check trades from the last 7 days
./check_trades.py --days 7

# Check today's trades and active positions
./check_trades.py --positions
```

### Generate Daily Summary

To generate and send a daily summary:

```bash
./daily_summary.py --now
```

This will:
- Generate a summary of today's trading activity
- Save the summary to text and HTML files
- Send the summary via email and/or Telegram (if configured)

### Schedule Daily Summary

To schedule a daily summary to run automatically at the end of each trading day:

```bash
./start_daily_summary.sh
```

Options:
- `--now`: Generate and send summary immediately
- `--time HH:MM`: Schedule time for daily summary (default: 16:00)

Examples:
```bash
# Start daily summary service to run at 16:00 (4:00 PM)
./start_daily_summary.sh

# Start daily summary service to run at 17:30 (5:30 PM)
./start_daily_summary.sh --time 17:30

# Generate and send summary immediately
./start_daily_summary.sh --now
```

## Configuration

### Email Configuration

To enable email notifications, add the following to your `.env` file:

```
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=your_email@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

Notes:
- For Gmail, you need to use an App Password instead of your regular password
- You can generate an App Password in your Google Account settings

### Telegram Configuration

To enable Telegram notifications, add the following to your `.env` file:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

To get your Telegram bot token and chat ID:
1. Open Telegram and search for @BotFather
2. Start a chat with BotFather and send the command `/newbot`
3. Follow the instructions to create a new bot:
   - Provide a name for your bot (e.g., "KryptoTradingBot")
   - Provide a username for your bot (must end with "bot", e.g., "krypto_trading_bot")
4. BotFather will give you a token for your new bot
5. Send a message to your new bot to activate the chat
6. Run the helper script to get your chat ID:
   ```bash
   ./get_chat_id.py
   ```
7. The script will display your chat ID and instructions for adding it to your `.env` file

Alternatively, you can manually get your chat ID:
1. Send a message to your bot
2. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` to get your chat ID

## Files

- `check_trades.py`: Script to check if the bot executed any trades
- `daily_summary.py`: Script to generate and send daily summaries
- `start_daily_summary.sh`: Shell script to start the daily summary service
- `reports/summary_YYYY-MM-DD.txt`: Text version of the daily summary
- `reports/summary_YYYY-MM-DD.html`: HTML version of the daily summary
- `reports/daily_pnl.png`: Chart of daily profit/loss
- `reports/cumulative_pnl.png`: Chart of cumulative profit/loss

## Dependencies

- pandas: For data manipulation
- matplotlib: For generating charts
- schedule: For scheduling daily summaries
- python-dotenv: For loading environment variables
- smtplib: For sending email notifications
- requests: For sending Telegram notifications 