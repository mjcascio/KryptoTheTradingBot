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
from typing import Dict, List, Optional
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
    
    def __init__(self):
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
        self.polling_task = None
        self.trading_bot = None
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
    
    async def start_polling(self):
        """Start polling for Telegram updates."""
        if not TELEGRAM_ENABLED:
            logger.warning("Telegram notifications are disabled.")
            return
        
        self.polling_active = True
        last_update_id = 0
        self.session = aiohttp.ClientSession()
        
        logger.info("Starting Telegram polling...")
        
        while self.polling_active:
            try:
                updates = await self.get_updates(last_update_id)
                for update in updates:
                    if 'message' in update and 'text' in update['message']:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message['text']
                        
                        # Only process commands from authorized users
                        if str(chat_id) == TELEGRAM_CHAT_ID:
                            await self.process_command(text)
                            logger.info(f"Processed command: {text}")
                    
                    last_update_id = update['update_id'] + 1
            except Exception as e:
                logger.error(f"Error in Telegram polling: {e}")
            
            await asyncio.sleep(1)
    
    async def get_updates(self, offset: int = 0) -> List[Dict]:
        """Get updates from Telegram."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params = {"offset": offset, "timeout": 30}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('result', [])
                logger.error(
                    f"Failed to get updates. Status: {response.status}"
                )
        except Exception as e:
            logger.error(f"Error getting Telegram updates: {e}")
        
        return []
    
    async def send_message(self, text: str) -> bool:
        """Send a message to the Telegram chat."""
        if not TELEGRAM_ENABLED:
            logger.warning("Telegram notifications are disabled.")
            return False
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    return True
                logger.error(
                    f"Failed to send Telegram message. "
                    f"Status code: {response.status}"
                )
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
        
        return False
    
    async def process_command(self, command: str):
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
    
    async def handle_start(self, _):
        """Handle /start command."""
        await self.send_message("Starting trading bot...")
        if self.trading_bot:
            self.trading_bot.start()
            await self.send_message("Trading bot started successfully.")
        else:
            await self.send_message("Error: Trading bot not initialized.")
    
    async def handle_stop(self, _):
        """Handle /stop command."""
        await self.send_message("Stopping trading bot...")
        if self.trading_bot:
            self.trading_bot.stop()
            await self.send_message("Trading bot stopped successfully.")
        else:
            await self.send_message("Error: Trading bot not initialized.")
    
    async def handle_status(self, _):
        """Handle /status command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return
        
        status = self.trading_bot.get_status()
        metrics = self.system_monitor.get_current_metrics()
        
        message = "🤖 *Trading Bot Status*\n\n"
        message += f"*Status:* {'Running' if status['running'] else 'Stopped'}\n"
        message += f"*Uptime:* {status['uptime']}\n"
        message += f"*Active Strategies:* {len(status['active_strategies'])}\n"
        message += f"*Open Positions:* {len(status['open_positions'])}\n\n"
        
        message += "💻 *System Metrics*\n"
        message += f"*CPU Usage:* {metrics['cpu_usage']:.1f}%\n"
        message += f"*Memory Usage:* {metrics['memory_usage']:.1f}%\n"
        message += f"*Disk Usage:* {metrics['disk_usage']:.1f}%\n"
        
        await self.send_message(message)
    
    async def handle_positions(self, _):
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
    
    async def handle_trades(self, _):
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
    
    async def handle_performance(self, _):
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
    
    async def handle_diagnostics(self, _):
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
    
    async def handle_start_stocks(self, _):
        """Handle /start_stocks command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return
        
        if self.trading_bot.start_stock_trading():
            await self.send_message("Stock trading started successfully.")
        else:
            await self.send_message("Failed to start stock trading.")
    
    async def handle_stop_stocks(self, _):
        """Handle /stop_stocks command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return
        
        if self.trading_bot.stop_stock_trading():
            await self.send_message("Stock trading stopped successfully.")
        else:
            await self.send_message("Failed to stop stock trading.")
    
    async def handle_start_options(self, _):
        """Handle /start_options command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return
        
        if self.trading_bot.start_options_trading():
            await self.send_message("Options trading started successfully.")
        else:
            await self.send_message("Failed to start options trading.")
    
    async def handle_stop_options(self, _):
        """Handle /stop_options command."""
        if not self.trading_bot:
            await self.send_message("Error: Trading bot not initialized.")
            return
        
        if self.trading_bot.stop_options_trading():
            await self.send_message("Options trading stopped successfully.")
        else:
            await self.send_message("Failed to stop options trading.")
    
    async def handle_help(self, _):
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
    
    def start(self):
        """Start the Telegram notifier."""
        if not TELEGRAM_ENABLED:
            logger.warning("Telegram notifications are disabled.")
            return False
        
        if self.polling_task is None:
            loop = asyncio.get_event_loop()
            self.polling_task = loop.create_task(self.start_polling())
            logger.info("Telegram notifier started")
            return True
        
        return False
    
    async def stop(self):
        """Stop the Telegram notifier."""
        self.polling_active = False
        if self.polling_task:
            self.polling_task.cancel()
            self.polling_task = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Telegram notifier stopped")
        return True
    
    def connect_trading_bot(self, bot):
        """Connect the trading bot instance."""
        self.trading_bot = bot
        logger.info("Trading bot connected to Telegram notifier")


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