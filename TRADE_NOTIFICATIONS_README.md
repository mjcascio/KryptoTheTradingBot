# KryptoBot Trade Notification System

This document provides an overview of the KryptoBot Trade Notification System, which enables real-time notifications for trade executions, position updates, and daily summaries.

## Overview

The Trade Notification System is designed to keep you informed about your trading bot's activities through Telegram messages. It provides:

- Real-time trade execution notifications
- Position opened/closed/updated notifications
- System event alerts
- Daily trading summaries

## Components

The system consists of the following components:

1. **Trade Hooks (`trade_hooks.py`)**: Event hooks that are triggered when trades are executed, positions are opened/closed/updated, or system events occur.
2. **Telegram Notifications (`telegram_notifications.py`)**: Handles sending notifications to Telegram.
3. **Trade Simulation (`simulate_trade.py`)**: Allows you to simulate trades for testing purposes.
4. **Daily Summary (`send_today_summary.py`)**: Sends a summary of the day's trading activity.

## Setup

### Prerequisites

- A Telegram bot token (obtain from BotFather)
- Your Telegram chat ID

### Configuration

1. Add the following to your `.env` file:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## Usage

### Trade Hooks

Integrate the trade hooks into your trading bot by importing and calling the appropriate functions:

```python
from trade_hooks import (
    on_trade_executed,
    on_position_opened,
    on_position_closed,
    on_position_updated,
    on_system_event
)

# When a trade is executed
on_trade_executed(
    symbol="AAPL",
    side="buy",
    quantity=10,
    price=198.50,
    strategy="breakout"
)

# When a position is opened
on_position_opened(
    symbol="AAPL",
    side="long",
    quantity=10,
    price=198.50,
    strategy="breakout"
)

# When a position is closed
on_position_closed(
    symbol="AAPL",
    side="long",
    quantity=10,
    entry_price=198.50,
    exit_price=205.75,
    profit=72.50,
    strategy="breakout"
)

# When a position is updated
on_position_updated(
    symbol="AAPL",
    side="long",
    quantity=10,
    entry_price=198.50,
    current_price=200.25,
    unrealized_profit=17.50,
    strategy="breakout"
)

# When a system event occurs
on_system_event(
    event_type="info",
    message="Trading bot started successfully"
)
```

### Simulating Trades

You can simulate trades for testing purposes using the `simulate_trade.py` script:

```bash
python3 simulate_trade.py --symbol AAPL --side buy --quantity 10 --price 198.50 --strategy breakout
```

Options:
- `--symbol`: Trading symbol (e.g., AAPL)
- `--side`: Trade side (buy or sell)
- `--quantity`: Trade quantity
- `--price`: Trade price
- `--strategy`: Trading strategy (optional)
- `--profit`: Profit/loss amount for sell trades (optional)

### Sending Daily Summaries

Send a summary of today's trading activity:

```bash
python3 send_today_summary.py
```

The summary includes:
- Number of trades executed today
- Profitable vs. losing trades
- Total profit/loss
- Details of each trade
- Active positions

## Integration with Trading Bot

To fully integrate the notification system with your trading bot, add the appropriate hook calls at the relevant points in your trading logic:

1. **Trade Execution**: Call `on_trade_executed()` when a trade is executed.
2. **Position Management**: Call `on_position_opened()`, `on_position_closed()`, and `on_position_updated()` when positions change.
3. **System Events**: Call `on_system_event()` for important system events.
4. **Daily Summary**: Schedule `send_today_summary.py` to run at the end of each trading day.

## Files

- `trade_hooks.py`: Contains event hooks for trade-related events.
- `telegram_notifications.py`: Handles sending notifications to Telegram.
- `simulate_trade.py`: Simulates trade executions for testing.
- `send_today_summary.py`: Sends a summary of today's trading activity.
- `check_trades.py`: Checks for trades executed today and active positions.

## Troubleshooting

If you're not receiving notifications:

1. Verify your Telegram bot token and chat ID in the `.env` file.
2. Ensure your bot has permission to send messages to your chat.
3. Check the logs for any error messages.
4. Test the connection using `python3 telegram_notifications.py`.

## Customization

You can customize the notification messages by modifying the relevant functions in `telegram_notifications.py`. 