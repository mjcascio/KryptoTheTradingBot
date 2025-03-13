#!/usr/bin/env python3
"""
Telegram Notifications Module

This module handles sending notifications to Telegram for various events
such as trade executions, position updates, and system alerts.
"""

import os
import logging
import requests
from datetime import datetime
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
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID and not TELEGRAM_BOT_TOKEN.startswith('your_'))

class TelegramNotifier:
    def __init__(self):
        """Initialize the Telegram notifier."""
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.command_handlers = {}
        self.polling_active = False
        self.polling_thread = None
        self.trading_bot = None
        
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

def send_telegram_message(message):
    """
    Send a message to Telegram
    
    Args:
        message: The message to send
        
    Returns:
        Boolean indicating success
    """
    if not TELEGRAM_ENABLED:
        logger.warning("Telegram notifications disabled: Missing configuration")
        return False
    
    try:
        # Telegram API URL
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # Prepare message
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        
        # Send message
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            logger.info("Telegram message sent successfully")
            return True
        else:
            logger.error(f"Error sending Telegram message: {response.status_code} - {response.reason}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

def send_telegram_photo(photo_path, caption=None):
    """
    Send a photo to Telegram
    
    Args:
        photo_path: Path to the photo file
        caption: Optional caption for the photo
        
    Returns:
        Boolean indicating success
    """
    if not TELEGRAM_ENABLED:
        logger.warning("Telegram notifications disabled: Missing configuration")
        return False
    
    try:
        # Telegram API URL
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        # Prepare files and data
        files = {
            "photo": open(photo_path, "rb")
        }
        
        data = {
            "chat_id": TELEGRAM_CHAT_ID
        }
        
        if caption:
            data["caption"] = caption
        
        # Send photo
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            logger.info(f"Telegram photo sent successfully: {photo_path}")
            return True
        else:
            logger.error(f"Error sending Telegram photo: {response.status_code} - {response.reason}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram photo: {e}")
        return False

def send_trade_notification(symbol, side, quantity, price, strategy=None, profit=None):
    """
    Send a notification about a trade execution
    
    Args:
        symbol: The trading symbol (e.g., 'AAPL')
        side: The trade side ('buy' or 'sell')
        quantity: The quantity traded
        price: The execution price
        strategy: Optional strategy name
        profit: Optional profit/loss amount (for sell trades)
        
    Returns:
        Boolean indicating success
    """
    try:
        # Format the message
        message = f"🔔 *Trade Executed*\n\n"
        message += f"*Symbol:* {symbol}\n"
        message += f"*Side:* {'🟢 BUY' if side.lower() == 'buy' else '🔴 SELL'}\n"
        message += f"*Quantity:* {quantity}\n"
        message += f"*Price:* ${price:.2f}\n"
        
        if strategy:
            message += f"*Strategy:* {strategy}\n"
        
        if profit is not None:
            emoji = "✅" if profit > 0 else "❌" if profit < 0 else "➖"
            message += f"*Profit/Loss:* {emoji} ${profit:.2f}\n"
        
        message += f"\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send the message
        return send_telegram_message(message)
        
    except Exception as e:
        logger.error(f"Error sending trade notification: {e}")
        return False

def send_position_update(symbol, side, quantity, entry_price, current_price, unrealized_profit, strategy=None):
    """
    Send a notification about a position update
    
    Args:
        symbol: The trading symbol (e.g., 'AAPL')
        side: The position side ('long' or 'short')
        quantity: The position quantity
        entry_price: The entry price
        current_price: The current price
        unrealized_profit: The unrealized profit/loss
        strategy: Optional strategy name
        
    Returns:
        Boolean indicating success
    """
    try:
        # Format the message
        message = f"📊 *Position Update*\n\n"
        message += f"*Symbol:* {symbol}\n"
        message += f"*Side:* {'🟢 LONG' if side.lower() == 'long' else '🔴 SHORT'}\n"
        message += f"*Quantity:* {quantity}\n"
        message += f"*Entry Price:* ${entry_price:.2f}\n"
        message += f"*Current Price:* ${current_price:.2f}\n"
        
        emoji = "✅" if unrealized_profit > 0 else "❌" if unrealized_profit < 0 else "➖"
        message += f"*Unrealized P/L:* {emoji} ${unrealized_profit:.2f}\n"
        
        if strategy:
            message += f"*Strategy:* {strategy}\n"
        
        message += f"\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send the message
        return send_telegram_message(message)
        
    except Exception as e:
        logger.error(f"Error sending position update: {e}")
        return False

def send_system_alert(alert_type, message):
    """
    Send a system alert
    
    Args:
        alert_type: The type of alert ('info', 'warning', 'error')
        message: The alert message
        
    Returns:
        Boolean indicating success
    """
    try:
        # Choose emoji based on alert type
        emoji = "ℹ️" if alert_type.lower() == 'info' else "⚠️" if alert_type.lower() == 'warning' else "🚨"
        
        # Format the message
        formatted_message = f"{emoji} *System Alert*\n\n"
        formatted_message += f"*Type:* {alert_type.upper()}\n"
        formatted_message += f"*Message:* {message}\n"
        formatted_message += f"\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send the message
        return send_telegram_message(formatted_message)
        
    except Exception as e:
        logger.error(f"Error sending system alert: {e}")
        return False

def send_today_summary():
    """
    Send a summary of today's activity
    
    Returns:
        Boolean indicating success
    """
    try:
        from check_trades import load_trade_history, check_trades_today, check_active_positions
        from datetime import datetime
        
        # Load trade history
        trade_history = load_trade_history()
        
        # Check today's trades
        today_trades = check_trades_today(trade_history)
        
        # Check active positions
        positions = check_active_positions()
        
        # Format the message
        message = f"📈 *KryptoBot Daily Summary*\n\n"
        message += f"*Date:* {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Add trade summary
        if today_trades.empty:
            message += "*Trades:* No trades executed today.\n\n"
        else:
            message += f"*Trades:* {len(today_trades)} trades executed today.\n\n"
            
            # Calculate summary statistics
            if 'profit' in today_trades.columns:
                total_profit = today_trades['profit'].sum()
                profitable_trades = len(today_trades[today_trades['profit'] > 0])
                losing_trades = len(today_trades[today_trades['profit'] < 0])
                
                message += "*Trade Summary:*\n"
                message += f"- Total Trades: {len(today_trades)}\n"
                message += f"- Profitable Trades: {profitable_trades}\n"
                message += f"- Losing Trades: {losing_trades}\n"
                
                emoji = "✅" if total_profit > 0 else "❌" if total_profit < 0 else "➖"
                message += f"- Total P/L: {emoji} ${total_profit:.2f}\n\n"
            
            # Add trade details
            message += "*Trade Details:*\n"
            for _, trade in today_trades.iterrows():
                timestamp = trade.get('timestamp', 'Unknown')
                symbol = trade.get('symbol', 'Unknown')
                side = trade.get('side', 'Unknown')
                quantity = trade.get('quantity', 0)
                entry_price = trade.get('entry_price', 0)
                exit_price = trade.get('exit_price', 0)
                profit = trade.get('profit', 0)
                
                emoji = "✅" if profit > 0 else "❌" if profit < 0 else "➖"
                
                message += f"- {timestamp.strftime('%H:%M:%S')}: {symbol} {'🟢 BUY' if side.lower() == 'buy' else '🔴 SELL'} {quantity} @ ${entry_price:.2f}, Exit @ ${exit_price:.2f}, P/L: {emoji} ${profit:.2f}\n"
            
            message += "\n"
        
        # Add position summary
        if not positions:
            message += "*Positions:* No active positions.\n"
        else:
            message += f"*Active Positions:* {len(positions)} positions\n\n"
            
            # Add position details
            for symbol, position in positions.items():
                side = position.get('side', 'Unknown')
                quantity = position.get('quantity', 0)
                entry_price = position.get('entry_price', 0)
                current_price = position.get('current_price', 0)
                unrealized_profit = position.get('unrealized_profit', 0)
                
                emoji = "✅" if unrealized_profit > 0 else "❌" if unrealized_profit < 0 else "➖"
                
                message += f"- {symbol}: {'🟢 LONG' if side.lower() == 'long' else '🔴 SHORT'} {quantity} @ ${entry_price:.2f}, Current: ${current_price:.2f}, P/L: {emoji} ${unrealized_profit:.2f}\n"
        
        # Send the message
        return send_telegram_message(message)
        
    except Exception as e:
        logger.error(f"Error sending today's summary: {e}")
        return False

# For testing
if __name__ == "__main__":
    from datetime import datetime
    
    # Test sending a message
    print("Testing Telegram notifications...")
    
    if TELEGRAM_ENABLED:
        print("Telegram is configured correctly.")
        
        # Send a test message
        test_message = f"This is a test message from KryptoBot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if send_telegram_message(test_message):
            print("Test message sent successfully!")
        else:
            print("Failed to send test message.")
            
        # Send today's summary
        print("Sending today's summary...")
        if send_today_summary():
            print("Today's summary sent successfully!")
        else:
            print("Failed to send today's summary.")
    else:
        print("Telegram is not configured. Please check your .env file.") 