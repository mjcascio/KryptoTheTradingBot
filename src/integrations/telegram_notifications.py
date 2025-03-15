#!/usr/bin/env python3
"""
Telegram Notifications Module

This module handles sending notifications to Telegram for various events
such as trade executions, position updates, and system alerts.
"""

import os
import logging
import asyncio
import aiohttp
import pytz
import requests
from datetime import datetime, time
from typing import Dict, List, Optional, Any, cast
from dotenv import load_dotenv

from utils.monitoring import SystemMonitor, MetricsConfig


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()


# Get Telegram credentials
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


# Check if Telegram is configured
is_valid_token = bool(
    TELEGRAM_BOT_TOKEN and not TELEGRAM_BOT_TOKEN.startswith('your_')
)
TELEGRAM_ENABLED = bool(is_valid_token and TELEGRAM_CHAT_ID)


# Market hours (EST)
EST = pytz.timezone('US/Eastern')
MARKET_OPEN = time(9, 30)  # 9:30 AM EST
MARKET_CLOSE = time(16, 0)  # 4:00 PM EST


class TelegramNotifier:
    """Telegram notification handler for the trading bot."""

    def __init__(self) -> None:
        """Initialize the Telegram notifier."""
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.command_handlers = {
            '/start': self.handle_start,
            '/stop': self.handle_stop,
            '/status': self.handle_status,
            '/positions': self.handle_positions,
            '/trades': self.handle_trades,
            '/performance': self.handle_performance,
            '/diagnostics': self.handle_diagnostics,
            '/start_stocks': self.handle_start_stocks,
            '/stop_stocks': self.handle_stop_stocks,
            '/start_options': self.handle_start_options,
            '/stop_options': self.handle_stop_options,
            '/help': self.handle_help
        }
        self.polling_active = False
        self.polling_task: Optional[asyncio.Task] = None
        self.trading_bot: Any = None  # Will be properly typed once TradingBot class is available
        self.session: Optional[aiohttp.ClientSession] = None

        # Initialize system monitor with config
        metrics_config = MetricsConfig(
            collection_interval=60,  # 1 minute interval
            retention_days=7,
            alert_thresholds={
                "cpu_usage": 80.0,
                "memory_usage": 80.0,
                "disk_usage": 80.0
            }
        )
        self.system_monitor = SystemMonitor(metrics_config)

    def connect_trading_bot(self, bot: Any) -> None:
        """Connect the trading bot instance."""
        self.trading_bot = bot
        logger.info("Trading bot connected to Telegram notifier")

    def start(self) -> bool:
        """Start the Telegram notifier."""
        if not TELEGRAM_ENABLED:
            logger.warning(
                "Telegram notifications are disabled - missing or invalid token/chat_id"
            )
            logger.warning(
                f"Bot Token valid: {bool(self.bot_token)}, "
                f"Chat ID valid: {bool(self.chat_id)}"
            )
            return False

        try:
            # Get the current event loop
            loop = asyncio.get_event_loop()

            # Create and start the session
            self.session = aiohttp.ClientSession()

            # Start polling task
            self.polling_task = loop.create_task(self.start_polling())

            # Send startup message
            startup_msg = (
                "🤖 *Trading Bot Online*\n\n"
                "Bot is starting up and ready for commands\\.\n"
                "Type /help to see available commands\\."
            )
            loop.create_task(self.send_message(startup_msg))

            # Safe string slicing with type checking
            token_prefix = self.bot_token[:4] if self.bot_token else "None"
            logger.info(
                f"Telegram notifier started with bot token: {token_prefix}... "
                f"and chat_id: {self.chat_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start Telegram notifier: {e}")
            return False

    def stop(self) -> None:
        """Stop the Telegram notifier."""
        if self.polling_active:
            self.polling_active = False
            if self.polling_task and not self.polling_task.done():
                self.polling_task.cancel()
            if self.session and not self.session.closed:
                loop = asyncio.get_event_loop()
                loop.create_task(self.session.close())
            logger.info("Telegram notifier stopped")

    async def start_polling(self) -> None:
        """Start polling for Telegram updates."""
        if not TELEGRAM_ENABLED:
            logger.warning("Telegram notifications are disabled.")
            return

        self.polling_active = True
        last_update_id = 0

        logger.info("Starting Telegram polling...")

        while self.polling_active:
            try:
                updates = await self.get_updates(last_update_id)
                for update in updates:
                    if 'message' in update and 'text' in update['message']:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message['text']

                        # Log incoming message
                        logger.info(f"Received Telegram message: {text} from chat_id: {chat_id}")

                        # Only process commands from authorized users
                        if str(chat_id) == str(self.chat_id):
                            await self.process_command(text)
                            logger.info(f"Processed command: {text}")
                        else:
                            logger.warning(
                                f"Unauthorized access attempt from chat_id: {chat_id}"
                            )

                    last_update_id = update['update_id'] + 1
            except aiohttp.ClientError as e:
                logger.error(f"Network error in Telegram polling: {e}")
                await asyncio.sleep(5)  # Wait longer on network errors
            except Exception as e:
                logger.error(f"Error in Telegram polling: {e}")
                await asyncio.sleep(1)

            await asyncio.sleep(1)

    async def get_updates(self, offset: int = 0) -> List[Dict[str, Any]]:
        """Get updates from Telegram."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params = {"offset": offset, "timeout": 30}

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return cast(List[Dict[str, Any]], data.get('result', []))
                logger.error(
                    f"Failed to get updates. Status: {response.status}"
                )
        except Exception as e:
            logger.error(f"Error getting Telegram updates: {e}")

        return []

    async def send_message(self, text: str) -> bool:
        """Send a message to the Telegram chat."""
        if not TELEGRAM_ENABLED:
            logger.warning("Telegram notifications are disabled - missing or invalid token/chat_id")
            return False

        if not self.session:
            logger.info("Creating new session for Telegram message")
            self.session = aiohttp.ClientSession()

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "MarkdownV2"  # Using V2 for better compatibility
        }

        try:
            logger.debug(f"Sending Telegram message to {self.chat_id}")
            async with self.session.post(url, json=data) as response:
                response_json = await response.json()
                if response.status == 200:
                    logger.info("Telegram message sent successfully")
                    return True
                else:
                    logger.error(
                        f"Failed to send Telegram message. "
                        f"Status code: {response.status}, "
                        f"Response: {response_json}"
                    )
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")

        return False

    async def process_command(self, command: str) -> None:
        """Process a Telegram command."""
        handler = self.command_handlers.get(command.split()[0].lower())
        if handler:
            try:
                await handler(command)
                logger.info(f"Successfully handled command: {command}")
            except Exception as e:
                error_msg = f"Error handling command {command}: {e}"
                logger.error(error_msg)
                await self.send_message(f"❌ {error_msg}")
        else:
            msg = "Unknown command. Type /help for available commands."
            await self.send_message(msg)

    async def handle_start(self, _: str) -> None:
        """Handle /start command."""
        if not self.trading_bot:
            await self.send_message("❌ Error: Trading bot not initialized\\.")
            return

        try:
            # Check if already running
            status = self.trading_bot.get_status()
            if status.get('running', False):
                await self.send_message("ℹ️ Trading bot is already running\\.")
                return

            # Attempt to start the bot
            success = self.trading_bot.start()
            if success:
                # Get updated status after starting
                status = self.trading_bot.get_status()
                msg = (
                    "✅ *Trading Bot Started Successfully*\n\n"
                    f"*Active Strategies:* "
                    f"{', '.join(status['active_strategies'])}\n"
                    f"*Paper Trading:* {'Yes' if status['paper_trading'] else 'No'}\n\n"
                    "Send /status to see detailed bot status\\."
                )
                await self.send_message(msg)
                logger.info("Trading bot started via Telegram command")
            else:
                await self.send_message(
                    "❌ Failed to start trading bot\\. Check logs for details\\."
                )
        except Exception as e:
            error_msg = f"Error starting trading bot: {str(e)}"
            logger.error(error_msg)
            await self.send_message(f"❌ {error_msg}")

    async def handle_stop(self, _: str) -> None:
        """Handle /stop command."""
        if not self.trading_bot:
            await self.send_message("❌ Error: Trading bot not initialized.")
            return

        try:
            # Check if already stopped
            status = self.trading_bot.get_status()
            if not status.get('running'):
                await self.send_message("ℹ️ Trading bot is already stopped.")
                return

            # Attempt to stop the bot
            if self.trading_bot.stop():
                await self.send_message("✅ Trading bot stopped successfully.")
                logger.info("Trading bot stopped via Telegram command")
            else:
                await self.send_message("❌ Failed to stop trading bot. Check logs for details.")
        except Exception as e:
            error_msg = f"Error stopping trading bot: {str(e)}"
            logger.error(error_msg)
            await self.send_message(f"❌ {error_msg}")

    async def handle_status(self, _: str) -> None:
        """Handle status command."""
        if not self.trading_bot:
            await self.send_message("❌ Error: Trading bot not initialized\\.")
            return

        try:
            # Get bot status and info
            bot_status = self.trading_bot.get_status()
            account_info = self.trading_bot.alpaca.get_account_info()

            def escape_markdown(text: str) -> str:
                """Escape special characters for MarkdownV2."""
                chars_to_escape = [
                    '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+',
                    '-', '=', '|', '{', '}', '.', '!'
                ]
                for char in chars_to_escape:
                    if char not in ['*', '\n']:  # Don't escape asterisks (for bold) or newlines
                        text = text.replace(char, f'\\{char}')
                return text

            # Format positions summary
            positions = bot_status.get('open_positions', [])
            positions_summary = ""
            if positions:
                for pos in positions:
                    symbol = escape_markdown(pos['symbol'])
                    qty = escape_markdown(str(pos['qty']))
                    price = escape_markdown(f"${pos['current_price']:.2f}")
                    pl = escape_markdown(f"${pos['unrealized_pl']:.2f}")
                    positions_summary += f"• {symbol}: {qty} @ {price} \\(P/L: {pl}\\)\n"
            else:
                positions_summary = "No open positions\\."

            # Format active strategies
            strategies = bot_status.get('active_strategies', [])
            strategies_str = ', '.join(escape_markdown(s) for s in strategies)

            # Format uptime
            uptime = escape_markdown(str(bot_status.get('uptime', 'Not started')))

            # Format account values
            equity = escape_markdown(f"${account_info.get('equity', 0.0):.2f}")
            buying_power = escape_markdown(f"${account_info.get('buying_power', 0.0):.2f}")

            # Build status message
            status_msg = (
                "*Trading Bot Status Report*\n\n"
                f"*Status:* {'🟢 Running' if bot_status.get('running', False) else '🔴 Stopped'}\n"
                f"*Uptime:* {uptime}\n"
                f"*Active Strategies:* {strategies_str}\n"
                f"*Paper Trading:* {'Yes' if bot_status.get('paper_trading', True) else 'No'}\n\n"
                "*Account Info:*\n"
                f"• Equity: {equity}\n"
                f"• Buying Power: {buying_power}\n\n"
                "*Open Positions:*\n"
                f"{positions_summary}\n"
                "*System Metrics:*\n"
                f"• CPU Usage: {bot_status.get('cpu_percent', 0.0):.1f}%\n"
                f"• Memory Usage: {bot_status.get('memory_percent', 0.0):.1f}%"
            )

            await self.send_message(status_msg)

        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            error_msg = (
                "❌ *Error Getting Status*\n\n"
                "Failed to retrieve bot status\\. Please check the logs\\."
            )
            await self.send_message(error_msg)

    async def handle_positions(self, _: str) -> None:
        """Handle /positions command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return

        positions = self.trading_bot.get_positions()
        if not positions:
            await self.send_message("No open positions.")
            return

        message = "📊 *Open Positions*\n\n"
        for pos in positions:
            pnl = pos['unrealized_pl']
            emoji = "🟢" if pnl >= 0 else "🔴"
            message += f"{emoji} *{pos['symbol']}*\n"
            message += f"Side: {pos['side'].title()}\n"
            message += f"Quantity: {pos['qty']}\n"
            message += f"Entry: ${pos['avg_entry_price']:.2f}\n"
            message += f"Current: ${pos['current_price']:.2f}\n"
            message += (
                f"P&L: ${pnl:.2f} ({pos['unrealized_plpc']:.1f}%)\n\n"
            )

        await self.send_message(message)

    async def handle_trades(self, _: str) -> None:
        """Handle /trades command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return

        trades = self.trading_bot.get_recent_trades()
        if not trades:
            await self.send_message("No recent trades.")
            return

        message = "📈 *Recent Trades*\n\n"
        for trade in trades:
            emoji = "🟢" if trade['side'] == 'buy' else "🔴"
            message += f"{emoji} *{trade['symbol']}*\n"
            message += f"Side: {trade['side'].title()}\n"
            message += f"Quantity: {trade['qty']}\n"
            message += f"Price: ${trade['price']:.2f}\n"
            message += f"Time: {trade['timestamp']}\n\n"

        await self.send_message(message)

    async def handle_performance(self, _: str) -> None:
        """Handle /performance command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return

        perf = self.trading_bot.get_performance()
        message = "📊 *Performance Summary*\n\n"
        message += f"*Daily P&L:* ${perf['daily_pl']:.2f}\n"
        message += f"*Total P&L:* ${perf['total_pl']:.2f}\n"
        message += f"*Win Rate:* {perf['win_rate']:.1f}%\n"
        message += f"*Sharpe Ratio:* {perf['sharpe_ratio']:.2f}\n"

        await self.send_message(message)

    async def handle_diagnostics(self, _: str) -> None:
        """Handle /diagnostics command."""
        message = "🔍 *System Diagnostics*\n\n"

        # Check API connection
        is_connected = (
            self.trading_bot and self.trading_bot.check_api_connection()
        )
        api_status = "✅ Connected" if is_connected else "❌ Disconnected"
        message += f"*API Status:* {api_status}\n"

        # Check market data
        has_data = (
            self.trading_bot and self.trading_bot.check_market_data()
        )
        market_data = "✅ Available" if has_data else "❌ Unavailable"
        message += f"*Market Data:* {market_data}\n"

        # System metrics
        metrics = self.system_monitor.get_current_metrics()
        message += "\n*System Metrics:*\n"
        message += f"CPU: {metrics['cpu_usage']:.1f}%\n"
        message += f"Memory: {metrics['memory_usage']:.1f}%\n"
        message += f"Disk: {metrics['disk_usage']:.1f}%\n"

        # Error logs
        recent_errors = self.system_monitor.get_recent_errors()
        if recent_errors:
            message += "\n*Recent Errors:*\n"
            for error in recent_errors[-3:]:  # Show last 3 errors
                message += f"- {error}\n"

        await self.send_message(message)

    async def handle_start_stocks(self, _: str) -> None:
        """Handle /start_stocks command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return

        if self.trading_bot.start_stock_trading():
            await self.send_message("Stock trading started successfully.")
        else:
            await self.send_message("Failed to start stock trading.")

    async def handle_stop_stocks(self, _: str) -> None:
        """Handle /stop_stocks command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return

        if self.trading_bot.stop_stock_trading():
            await self.send_message("Stock trading stopped successfully.")
        else:
            await self.send_message("Failed to stop stock trading.")

    async def handle_start_options(self, _: str) -> None:
        """Handle /start_options command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return

        if self.trading_bot.start_options_trading():
            await self.send_message("Options trading started successfully.")
        else:
            await self.send_message("Failed to start options trading.")

    async def handle_stop_options(self, _: str) -> None:
        """Handle /stop_options command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return

        if self.trading_bot.stop_options_trading():
            await self.send_message("Options trading stopped successfully.")
        else:
            await self.send_message("Failed to stop options trading.")

    async def handle_help(self, _: str) -> None:
        """Handle /help command."""
        message = "🤖 *Available Commands*\n\n"
        message += "*Basic Commands:*\n"
        message += "/start - Start the trading bot\n"
        message += "/stop - Stop the trading bot\n"
        message += "/status - Get bot status\n"
        message += "/positions - View open positions\n"
        message += "/trades - View recent trades\n"
        message += "/performance - View performance metrics\n"
        message += "/diagnostics - Run system diagnostics\n\n"

        message += "*Strategy Controls:*\n"
        message += "/start_stocks - Start stock trading\n"
        message += "/stop_stocks - Stop stock trading\n"
        message += "/start_options - Start options trading\n"
        message += "/stop_options - Stop options trading\n"

        await self.send_message(message)


def send_telegram_message(message: str) -> bool:
    """Send a one-off message to Telegram."""
    if not TELEGRAM_ENABLED:
        logger.warning("Telegram notifications are disabled.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return True
        logger.error(
            f"Failed to send Telegram message. "
            f"Status code: {response.status_code}"
        )
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")

    return False


def send_system_alert(alert_type: str, message: str) -> bool:
    """Send a system alert via Telegram."""
    emoji_map = {
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅"
    }
    emoji = emoji_map.get(alert_type.lower(), "🔔")
    formatted_message = f"{emoji} *{alert_type.upper()}*\n{message}"
    return send_telegram_message(formatted_message)


def is_market_hours() -> bool:
    """Check if it's currently market hours (EST)."""
    now = datetime.now(EST)
    current_time = now.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


# Initialize the notifier
notifier = TelegramNotifier()
