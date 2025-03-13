"""
Trade Notifications Module - Handles sending trade notifications.

This module extends the notification system to support SMS alerts for trades.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from kryptobot.utils.notifications import NotificationSystem, SMSNotificationChannel

# Configure logging
logger = logging.getLogger(__name__)

class TradeNotificationHandler:
    """
    Handler for trade notifications.
    
    This class extends the notification system to support SMS alerts for trades.
    """
    
    def __init__(self):
        """Initialize the trade notification handler."""
        # Load environment variables
        load_dotenv()
        
        # Initialize notification system
        self.notification_system = NotificationSystem()
        
        # Check if SMS notifications are enabled
        if os.getenv('KRYPTOBOT_SMS_ENABLED', 'false').lower() == 'true':
            # Get SMS configuration
            account_sid = os.getenv('KRYPTOBOT_SMS_ACCOUNT_SID')
            auth_token = os.getenv('KRYPTOBOT_SMS_AUTH_TOKEN')
            from_number = os.getenv('KRYPTOBOT_SMS_FROM_NUMBER')
            to_numbers = os.getenv('KRYPTOBOT_SMS_TO_NUMBERS', '').split(',')
            
            # Add SMS channel if configuration is valid
            if account_sid and auth_token and from_number and to_numbers:
                self.notification_system.add_channel(SMSNotificationChannel(
                    account_sid, auth_token, from_number, to_numbers
                ))
                logger.info("SMS notifications enabled for trades")
    
    def send_trade_notification(self, symbol: str, side: str, quantity: float, price: float, strategy: str = None):
        """
        Send a trade notification.
        
        Args:
            symbol (str): Symbol being traded
            side (str): Trade side ('buy' or 'sell')
            quantity (float): Trade quantity
            price (float): Trade price
            strategy (str, optional): Trading strategy used
        """
        # Create notification subject and message
        subject = f"Trade Alert: {side.upper()} {symbol}"
        
        message = f"""
Trade Details:
-------------
Symbol: {symbol}
Side: {side.upper()}
Quantity: {quantity}
Price: ${price:.2f}
"""
        
        if strategy:
            message += f"Strategy: {strategy}\n"
        
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send notification through all enabled channels
        self.notification_system.send_notification(subject, message)
        logger.info(f"Trade notification sent for {symbol}")
    
    def send_position_closed_notification(self, symbol: str, side: str, quantity: float, 
                                         entry_price: float, exit_price: float, profit_loss: float):
        """
        Send a position closed notification.
        
        Args:
            symbol (str): Symbol being traded
            side (str): Position side ('long' or 'short')
            quantity (float): Position quantity
            entry_price (float): Entry price
            exit_price (float): Exit price
            profit_loss (float): Profit/loss amount
        """
        # Calculate ROI
        roi = (profit_loss / (entry_price * quantity)) * 100
        
        # Create notification subject and message
        subject = f"Position Closed: {symbol}"
        
        message = f"""
Position Closed:
---------------
Symbol: {symbol}
Side: {side.upper()}
Quantity: {quantity}
Entry Price: ${entry_price:.2f}
Exit Price: ${exit_price:.2f}
Profit/Loss: ${profit_loss:.2f} ({roi:.2f}%)
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Send notification through all enabled channels
        self.notification_system.send_notification(subject, message)
        logger.info(f"Position closed notification sent for {symbol}")

# Create a singleton instance
trade_notification_handler = TradeNotificationHandler()

# Export the send_trade_notification function for easy access
def send_trade_notification(symbol: str, side: str, quantity: float, price: float, strategy: str = None):
    """
    Send a trade notification.
    
    Args:
        symbol (str): Symbol being traded
        side (str): Trade side ('buy' or 'sell')
        quantity (float): Trade quantity
        price (float): Trade price
        strategy (str, optional): Trading strategy used
    """
    trade_notification_handler.send_trade_notification(symbol, side, quantity, price, strategy)

# Export the send_position_closed_notification function for easy access
def send_position_closed_notification(symbol: str, side: str, quantity: float, 
                                     entry_price: float, exit_price: float, profit_loss: float):
    """
    Send a position closed notification.
    
    Args:
        symbol (str): Symbol being traded
        side (str): Position side ('long' or 'short')
        quantity (float): Position quantity
        entry_price (float): Entry price
        exit_price (float): Exit price
        profit_loss (float): Profit/loss amount
    """
    trade_notification_handler.send_position_closed_notification(symbol, side, quantity, 
                                                               entry_price, exit_price, profit_loss) 