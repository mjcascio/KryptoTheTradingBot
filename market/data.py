"""Market data operations for the KryptoBot Trading System."""

from datetime import datetime, time, timedelta
import pytz
import logging
from typing import Tuple
from config.settings import TIMEZONE, MARKET_HOURS

logger = logging.getLogger(__name__)

def get_market_hours() -> Tuple[time, time]:
    """Get market open and close times"""
    open_time = datetime.strptime(MARKET_HOURS['open'], '%H:%M:%S').time()
    close_time = datetime.strptime(MARKET_HOURS['close'], '%H:%M:%S').time()
    return open_time, close_time

def is_market_open() -> bool:
    """Check if the market is currently open"""
    now = datetime.now(pytz.timezone(TIMEZONE))
    current_time = now.time()
    
    # Get market hours
    market_open, market_close = get_market_hours()
    
    # Check if it's a weekday
    is_weekday = now.weekday() < 5
    
    # Check if market is open
    return (
        is_weekday and
        market_open <= current_time < market_close
    )

def get_next_market_times() -> Tuple[datetime, datetime]:
    """Calculate next market open and close times"""
    now = datetime.now(pytz.timezone(TIMEZONE))
    current_time = now.time()
    
    # Get market hours
    market_open, market_close = get_market_hours()
    
    # Check if it's a weekday
    is_weekday = now.weekday() < 5
    
    # Calculate next market open time
    if is_weekday:
        if current_time < market_open:
            # Market opens today
            next_open = now.replace(
                hour=market_open.hour,
                minute=market_open.minute,
                second=market_open.second
            )
        else:
            # Market opens next business day
            next_open = now + timedelta(days=1)
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)
            next_open = next_open.replace(
                hour=market_open.hour,
                minute=market_open.minute,
                second=market_open.second
            )
    else:
        # Find next Monday
        days_until_monday = (7 - now.weekday())
        next_open = now + timedelta(days=days_until_monday)
        next_open = next_open.replace(
            hour=market_open.hour,
            minute=market_open.minute,
            second=market_open.second
        )
    
    # Calculate next market close time
    if is_weekday and current_time < market_close:
        # Market closes today
        next_close = now.replace(
            hour=market_close.hour,
            minute=market_close.minute,
            second=market_close.second
        )
    else:
        # Market closes next business day
        next_close = next_open.replace(
            hour=market_close.hour,
            minute=market_close.minute,
            second=market_close.second
        )
    
    return next_open, next_close

def get_market_status() -> dict:
    """Get current market status and next market times"""
    is_open = is_market_open()
    next_open, next_close = get_next_market_times()
    
    return {
        'is_open': is_open,
        'next_open': next_open.strftime('%Y-%m-%d %H:%M:%S'),
        'next_close': next_close.strftime('%Y-%m-%d %H:%M:%S')
    } 