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
import backoff
import pytz
import requests
from datetime import datetime, time
from typing import Dict, List, Optional, Any, cast
from dotenv import load_dotenv

from utils.monitoring import SystemMonitor, MetricsConfig


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram.log'),
        logging.StreamHandler()
    ]
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


# Telegram API constants
TELEGRAM_API_BASE = "https://api.telegram.org/bot"
TELEGRAM_TIMEOUT = 30
MAX_RETRIES = 3


class TelegramNotifier:
    """Telegram notification handler for the trading bot."""

    def __init__(self) -> None:
        """Initialize the Telegram notifier."""
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_base = f"{TELEGRAM_API_BASE}{self.bot_token}"
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
        self.last_update_id = 0
        
        # Initialize system monitor
        metrics_config = MetricsConfig(
            collection_interval=60,
            retention_days=7,
            alert_thresholds={
                "cpu_usage": 80.0,
                "memory_usage": 80.0,
                "disk_usage": 80.0
            }
        )
        self.system_monitor = SystemMonitor(metrics_config)
        
        # Initialize error tracking
        self.error_count = 0
        self.max_errors = 10
        self.error_reset_interval = 300  # 5 minutes
        self.last_error_reset = datetime.now()

    def connect_trading_bot(self, bot: Any) -> None:
        """Connect the trading bot instance."""
        self.trading_bot = bot
        logger.info("Trading bot connected to Telegram notifier")

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=MAX_RETRIES
    )
    async def send_message(self, message: str, parse_mode: str = "MarkdownV2") -> bool:
        """Send a message via Telegram."""
        if not TELEGRAM_ENABLED:
            logger.warning("Telegram notifications are disabled")
            return False

        try:
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            url = f"{self.api_base}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            async with self.session.post(url, json=data, timeout=TELEGRAM_TIMEOUT) as response:
                if response.status == 200:
                    return True
                else:
                    error_data = await response.text()
                    logger.error(f"Failed to send message. Status: {response.status}, Error: {error_data}")
                    return False

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            self._track_error()
            return False

    async def start_polling(self) -> None:
        """Start polling for Telegram updates."""
        self.polling_active = True
        
        while self.polling_active:
            try:
                if not self.session or self.session.closed:
                    self.session = aiohttp.ClientSession()

                url = f"{self.api_base}/getUpdates"
                params = {
                    "offset": self.last_update_id + 1,
                    "timeout": 30
                }

                async with self.session.get(url, params=params, timeout=TELEGRAM_TIMEOUT) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok", False):
                            updates = data.get("result", [])
                            for update in updates:
                                await self._process_update(update)
                                self.last_update_id = update["update_id"]
                    else:
                        logger.error(f"Failed to get updates. Status: {response.status}")
                        await asyncio.sleep(5)

            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                self._track_error()
                await asyncio.sleep(5)

    async def _process_update(self, update: Dict[str, Any]) -> None:
        """Process a Telegram update."""
        try:
            message = update.get("message", {})
            if not message:
                return

            text = message.get("text", "")
            if not text:
                return

            logger.info(f"Received command: {text}")
            await self.process_command(text)

        except Exception as e:
            logger.error(f"Error processing update: {e}")
            self._track_error()

    def _track_error(self) -> None:
        """Track errors and reset counter periodically."""
        now = datetime.now()
        if (now - self.last_error_reset).total_seconds() > self.error_reset_interval:
            self.error_count = 0
            self.last_error_reset = now
        
        self.error_count += 1
        if self.error_count >= self.max_errors:
            logger.critical("Too many errors occurred. Stopping Telegram notifier.")
            self.stop()

    def start(self) -> bool:
        """Start the Telegram notifier."""
        if not TELEGRAM_ENABLED:
            logger.warning(
                "Telegram notifications are disabled - "
                "missing or invalid token/chat_id"
            )
            logger.warning(
                f"Bot Token valid: {bool(self.bot_token)}, "
                f"Chat ID valid: {bool(self.chat_id)}"
            )
            return False

        try:
            # Get the current event loop
            loop = asyncio.get_event_loop()

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
            logger.info(f"Telegram notifier started with chat_id: {self.chat_id}")
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

    async def process_command(self, command: str) -> None:
        """Process a Telegram command."""
        try:
            handler = self.command_handlers.get(command.split()[0].lower())
            if handler:
                await handler()
            else:
                await self.send_message(
                    "❌ Unknown command\\. Type /help for available commands\\."
                )
        except Exception as e:
            logger.error(f"Error processing command {command}: {e}")
            await self.send_message(
                f"❌ Error processing command: {str(e)}\\. "
                "Please try again or contact support\\."
            )

    async def handle_start(self) -> None:
        """Handle the /start command."""
        if not self.trading_bot:
            await self.send_message("❌ Trading bot not connected")
            return

        try:
            await self.trading_bot.start()
            await self.send_message(
                "✅ Trading bot started successfully\n"
                "Use /status to check current state"
            )
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            await self.send_message(f"❌ Failed to start trading bot: {str(e)}")

    async def handle_stop(self) -> None:
        """Handle the /stop command."""
        if not self.trading_bot:
            await self.send_message("❌ Trading bot not connected")
            return

        try:
            await self.trading_bot.stop()
            await self.send_message("✅ Trading bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")
            await self.send_message(f"❌ Failed to stop trading bot: {str(e)}")

    async def handle_status(self) -> None:
        """Handle the /status command."""
        if not self.trading_bot:
            await self.send_message("❌ Trading bot not connected")
            return

        try:
            status = await self.trading_bot.get_status()
            positions = await self.trading_bot.get_positions()
            
            # Format status message
            msg = (
                "*Trading Bot Status*\n\n"
                f"Status: {status['state']}\n"
                f"Active Since: {status['start_time']}\n"
                f"Total Trades: {status['total_trades']}\n"
                f"Win Rate: {status['win_rate']}%\n\n"
                f"Open Positions: {len(positions)}\n"
                f"Total P&L: ${status['total_pnl']:,.2f}\n"
                f"Daily P&L: ${status['daily_pnl']:,.2f}"
            )
            
            await self.send_message(msg)
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            await self.send_message(f"❌ Failed to get bot status: {str(e)}")

    async def handle_positions(self) -> None:
        """Handle the /positions command."""
        if not self.trading_bot:
            await self.send_message("❌ Trading bot not connected")
            return

        try:
            positions = await self.trading_bot.get_positions()
            
            if not positions:
                await self.send_message("No open positions")
                return
                
            msg = "*Current Positions*\n\n"
            for pos in positions:
                msg += (
                    f"Symbol: {pos['symbol']}\n"
                    f"Side: {pos['side']}\n" 
                    f"Size: {pos['size']}\n"
                    f"Entry: ${pos['entry_price']:,.2f}\n"
                    f"Current: ${pos['current_price']:,.2f}\n"
                    f"P&L: ${pos['unrealized_pnl']:,.2f}\n\n"
                )
                
            await self.send_message(msg)
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            await self.send_message(f"❌ Failed to get positions: {str(e)}")

    async def handle_trades(self) -> None:
        """Handle the /trades command."""
        if not self.trading_bot:
            await self.send_message("❌ Trading bot not connected")
            return

        try:
            trades = await self.trading_bot.get_recent_trades()
            
            if not trades:
                await self.send_message("No recent trades")
                return
                
            msg = "*Recent Trades*\n\n"
            for trade in trades[:5]:  # Show last 5 trades
                msg += (
                    f"Symbol: {trade['symbol']}\n"
                    f"Side: {trade['side']}\n"
                    f"Size: {trade['size']}\n"
                    f"Entry: ${trade['entry_price']:,.2f}\n"
                    f"Exit: ${trade['exit_price']:,.2f}\n"
                    f"P&L: ${trade['realized_pnl']:,.2f}\n"
                    f"Time: {trade['exit_time']}\n\n"
                )
                
            await self.send_message(msg)
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            await self.send_message(f"❌ Failed to get trades: {str(e)}")

    async def handle_performance(self) -> None:
        """Handle the /performance command."""
        if not self.trading_bot:
            await self.send_message("❌ Trading bot not connected")
            return

        try:
            perf = await self.trading_bot.get_performance()
            
            msg = (
                "*Performance Metrics*\n\n"
                f"Total Return: {perf['total_return']}%\n"
                f"Sharpe Ratio: {perf['sharpe_ratio']:.2f}\n"
                f"Max Drawdown: {perf['max_drawdown']}%\n"
                f"Win Rate: {perf['win_rate']}%\n"
                f"Profit Factor: {perf['profit_factor']:.2f}\n"
                f"Total Trades: {perf['total_trades']}\n"
                f"Avg Trade: ${perf['avg_trade']:,.2f}\n"
                f"Best Trade: ${perf['best_trade']:,.2f}\n"
                f"Worst Trade: ${perf['worst_trade']:,.2f}"
            )
            
            await self.send_message(msg)
        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            await self.send_message(f"❌ Failed to get performance: {str(e)}")

    async def handle_diagnostics(self) -> None:
        """Handle the /diagnostics command."""
        try:
            metrics = self.system_monitor.get_current_metrics()
            
            msg = (
                "*System Diagnostics*\n\n"
                f"CPU Usage: {metrics['cpu_usage']}%\n"
                f"Memory Usage: {metrics['memory_usage']}%\n"
                f"Disk Usage: {metrics['disk_usage']}%\n"
                f"Network Latency: {metrics['network_latency']}ms\n\n"
                f"Active Processes: {metrics['active_processes']}\n"
                f"Error Rate: {metrics['error_rate']}/min\n"
                f"Last Error: {metrics['last_error']}\n"
                f"Uptime: {metrics['uptime']}"
            )
            
            await self.send_message(msg)
        except Exception as e:
            logger.error(f"Error getting diagnostics: {e}")
            await self.send_message(f"❌ Failed to get diagnostics: {str(e)}")

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

    async def handle_help(self) -> None:
        """Handle the /help command."""
        help_text = (
            "*Available Commands*\n\n"
            "/start \\- Start the trading bot\n"
            "/stop \\- Stop the trading bot\n"
            "/status \\- Get current bot status\n"
            "/positions \\- View open positions\n"
            "/trades \\- View recent trades\n"
            "/performance \\- View performance metrics\n"
            "/diagnostics \\- View system diagnostics\n"
            "/help \\- Show this help message"
        )
        await self.send_message(help_text)


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
