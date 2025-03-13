"""
Sleep Manager Module - Manages the bot's sleep state.

This module is responsible for determining when the bot should sleep
based on various conditions such as market hours, daily loss limits,
and lack of trading opportunities.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from kryptobot.utils.config import SLEEP_MODE

# Configure logging
logger = logging.getLogger(__name__)

class SleepManager:
    """
    Manager for the bot's sleep state.
    
    This class is responsible for determining when the bot should sleep
    based on various conditions such as market hours, daily loss limits,
    and lack of trading opportunities.
    
    Attributes:
        sleeping (bool): Whether the bot is currently sleeping
        reason (str): Reason for sleeping
        next_wake_time (datetime): Next time the bot should wake up
        sleep_mode (Dict[str, bool]): Sleep mode configuration
    """
    
    def __init__(self, sleep_mode: Dict[str, bool] = None):
        """
        Initialize the sleep manager.
        
        Args:
            sleep_mode (Dict[str, bool], optional): Sleep mode configuration
        """
        self.sleeping = False
        self.reason = None
        self.next_wake_time = None
        self.sleep_mode = sleep_mode or SLEEP_MODE
        
        logger.info("Sleep manager initialized")
    
    def update(self, is_market_open: bool, next_market_open: Optional[datetime] = None,
              next_market_close: Optional[datetime] = None, daily_loss: float = 0.0,
              max_daily_loss: float = 0.05, has_opportunities: bool = True):
        """
        Update the sleep state based on current conditions.
        
        Args:
            is_market_open (bool): Whether the market is currently open
            next_market_open (datetime, optional): Next market open time
            next_market_close (datetime, optional): Next market close time
            daily_loss (float, optional): Current daily loss as a percentage
            max_daily_loss (float, optional): Maximum daily loss as a percentage
            has_opportunities (bool, optional): Whether there are trading opportunities
        """
        # Check if sleep mode is enabled
        if not self.sleep_mode.get('enabled', True):
            self.sleeping = False
            self.reason = None
            self.next_wake_time = None
            return
        
        # Check if we should sleep outside market hours
        if self.sleep_mode.get('sleep_outside_market_hours', True) and not is_market_open:
            self.sleeping = True
            self.reason = "Market is closed"
            self.next_wake_time = next_market_open
            logger.info(f"Bot is sleeping because market is closed. Next wake time: {self.next_wake_time}")
            return
        
        # Check if we should sleep when daily loss limit is reached
        if self.sleep_mode.get('max_daily_loss_sleep', True) and daily_loss >= max_daily_loss:
            self.sleeping = True
            self.reason = f"Daily loss limit reached ({daily_loss:.2%} >= {max_daily_loss:.2%})"
            
            # Sleep until next market open
            self.next_wake_time = next_market_open
            logger.info(f"Bot is sleeping because daily loss limit reached. Next wake time: {self.next_wake_time}")
            return
        
        # Check if we should sleep when there are no opportunities
        if self.sleep_mode.get('sleep_when_no_opportunities', True) and not has_opportunities:
            self.sleeping = True
            self.reason = "No trading opportunities"
            
            # Sleep for 30 minutes
            self.next_wake_time = datetime.now() + timedelta(minutes=30)
            logger.info(f"Bot is sleeping because there are no trading opportunities. Next wake time: {self.next_wake_time}")
            return
        
        # If we get here, we should not be sleeping
        self.sleeping = False
        self.reason = None
        self.next_wake_time = None
    
    def is_sleeping(self) -> bool:
        """
        Check if the bot is currently sleeping.
        
        Returns:
            bool: True if the bot is sleeping, False otherwise
        """
        return self.sleeping
    
    def get_reason(self) -> Optional[str]:
        """
        Get the reason for sleeping.
        
        Returns:
            Optional[str]: Reason for sleeping, or None if not sleeping
        """
        return self.reason
    
    def get_next_wake_time(self) -> Optional[datetime]:
        """
        Get the next time the bot should wake up.
        
        Returns:
            Optional[datetime]: Next wake time, or None if not sleeping
        """
        return self.next_wake_time
    
    def set_sleep_mode(self, sleep_mode: Dict[str, bool]):
        """
        Set the sleep mode configuration.
        
        Args:
            sleep_mode (Dict[str, bool]): Sleep mode configuration
        """
        self.sleep_mode = sleep_mode
        logger.info(f"Sleep mode updated: {sleep_mode}")
    
    def force_sleep(self, reason: str, duration_minutes: int = 60):
        """
        Force the bot to sleep for a specified duration.
        
        Args:
            reason (str): Reason for sleeping
            duration_minutes (int, optional): Sleep duration in minutes
        """
        self.sleeping = True
        self.reason = reason
        self.next_wake_time = datetime.now() + timedelta(minutes=duration_minutes)
        logger.info(f"Bot forced to sleep: {reason}. Next wake time: {self.next_wake_time}")
    
    def wake_up(self):
        """
        Force the bot to wake up.
        """
        self.sleeping = False
        self.reason = None
        self.next_wake_time = None
        logger.info("Bot forced to wake up") 