#!/usr/bin/env python3
"""
Trade Hooks Module

This module provides hooks for trade execution events.
These hooks are called when trades are executed, positions are opened/closed, etc.
"""

import logging
from datetime import datetime
from telegram_notifications import (
    send_trade_notification,
    send_position_update,
    send_system_alert,
    TELEGRAM_ENABLED
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def on_trade_executed(symbol, side, quantity, price, strategy=None, profit=None):
    """
    Hook called when a trade is executed
    
    Args:
        symbol: Trading symbol
        side: Trade side ('buy' or 'sell')
        quantity: Trade quantity
        price: Trade price
        strategy: Trading strategy
        profit: Profit/loss amount (for sell trades)
    """
    logger.info(f"Trade executed: {side.upper()} {quantity} {symbol} @ ${price:.2f}")
    
    # Send notification
    if TELEGRAM_ENABLED:
        success = send_trade_notification(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            strategy=strategy,
            profit=profit
        )
        
        if success:
            logger.info("Trade notification sent successfully")
        else:
            logger.error("Failed to send trade notification")

def on_position_opened(symbol, side, quantity, price, strategy=None):
    """
    Hook called when a position is opened
    
    Args:
        symbol: Trading symbol
        side: Position side ('long' or 'short')
        quantity: Position quantity
        price: Entry price
        strategy: Trading strategy
    """
    logger.info(f"Position opened: {side.upper()} {quantity} {symbol} @ ${price:.2f}")
    
    # Send notification
    if TELEGRAM_ENABLED:
        success = send_position_update(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=price,
            current_price=price,
            unrealized_profit=0,
            strategy=strategy
        )
        
        if success:
            logger.info("Position update notification sent successfully")
        else:
            logger.error("Failed to send position update notification")

def on_position_closed(symbol, side, quantity, entry_price, exit_price, profit, strategy=None):
    """
    Hook called when a position is closed
    
    Args:
        symbol: Trading symbol
        side: Position side ('long' or 'short')
        quantity: Position quantity
        entry_price: Entry price
        exit_price: Exit price
        profit: Profit/loss amount
        strategy: Trading strategy
    """
    logger.info(f"Position closed: {side.upper()} {quantity} {symbol}, Profit: ${profit:.2f}")
    
    # Send notification
    if TELEGRAM_ENABLED:
        success = send_trade_notification(
            symbol=symbol,
            side="sell" if side.lower() == "long" else "buy",
            quantity=quantity,
            price=exit_price,
            strategy=strategy,
            profit=profit
        )
        
        if success:
            logger.info("Position closed notification sent successfully")
        else:
            logger.error("Failed to send position closed notification")

def on_position_updated(symbol, side, quantity, entry_price, current_price, unrealized_profit, strategy=None, suppress_notifications=True):
    """
    Hook called when a position is updated
    
    Args:
        symbol: Trading symbol
        side: Position side ('long' or 'short')
        quantity: Position quantity
        entry_price: Entry price
        current_price: Current price
        unrealized_profit: Unrealized profit/loss
        strategy: Trading strategy
        suppress_notifications: Whether to suppress notifications for routine updates
    """
    # Only log the update, don't send notification for routine updates
    logger.info(f"Position updated: {side.upper()} {quantity} {symbol}, Unrealized P/L: ${unrealized_profit:.2f}")
    
    # Only send notification for significant changes and when not suppressed
    if not suppress_notifications and (
        abs(unrealized_profit) > quantity * entry_price * 0.02  # 2% P/L change
        or current_price < entry_price * 0.98  # Near stop loss
        or current_price > entry_price * 1.02  # Near take profit
    ):
        success = send_position_update(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_profit=unrealized_profit,
            strategy=strategy
        )
        
        if success:
            logger.info("Position update notification sent successfully")
        else:
            logger.error("Failed to send position update notification")

def on_system_event(event_type, message):
    """
    Hook called when a system event occurs
    
    Args:
        event_type: Event type ('info', 'warning', 'error')
        message: Event message
    """
    logger.info(f"System event: {event_type.upper()} - {message}")
    
    # Send notification
    if TELEGRAM_ENABLED:
        success = send_system_alert(
            alert_type=event_type,
            message=message
        )
        
        if success:
            logger.info("System alert notification sent successfully")
        else:
            logger.error("Failed to send system alert notification") 