# KryptoBot Telegram Commands

This document provides a comprehensive list of available Telegram commands for interacting with KryptoBot.

## General Commands
- `/help` - Show all available commands
- `/status` - Get current bot status including trading metrics and positions
- `/health` - Get detailed system health report
- `/diagnostics` - Run system diagnostics and get a detailed report

## Trading Control Commands
- `/start` - Start all trading (stocks and options)
- `/stop` - Stop all trading (emergency only)
- `/start_stocks` - Start stock trading only
- `/stop_stocks` - Stop stock trading only
- `/start_options` - Start options trading only
- `/stop_options` - Stop options trading only

## Trading Information Commands
- `/positions` - Show current positions
- `/trades` - Show recent trades
- `/performance` - Show performance metrics
- `/forecast` - Get market forecast

## Strategy Commands
- `/strategy [id]` - Change trading strategy to specified ID
- `/continue` - Continue with current strategy

## Automated Reports
KryptoBot automatically sends the following reports:

### Morning Report (Pre-market)
- Market forecast
- Potential trades for the day
- Strategy recommendations
- Market hours
- Available commands

### Daily Summary (Post-market)
- Trade summary
- Profitable vs losing trades
- Total P/L
- Active positions
- Performance metrics
- Strategy information

### Trade Notifications
- Real-time notifications for:
  - Trade executions
  - Position closures
  - Stop loss/take profit triggers
  - Critical system alerts

## Note
All commands are case-insensitive. Commands can be sent directly to the bot in the Telegram chat after the bot has been properly configured with your Telegram credentials. 