"""Market time utility for managing market hours and time-based operations."""

import logging
from datetime import datetime, time
from typing import Dict, Any, Optional
import pytz

logger = logging.getLogger(__name__)


class MarketTime:
    """Utility class for managing market hours and time-based operations."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the market time utility.
        
        Args:
            config: Configuration dictionary containing:
                - timezone: Market timezone (default: 'US/Eastern')
                - open_time: Market open time (default: '09:30')
                - close_time: Market close time (default: '16:00')
                - pre_market_start: Pre-market start time (default: '04:00')
                - after_market_end: After-market end time (default: '20:00')
        """
        self.timezone = pytz.timezone(config.get('timezone', 'US/Eastern'))
        
        # Parse market hours
        self.market_open = self._parse_time(
            config.get('open_time', '09:30')
        )
        self.market_close = self._parse_time(
            config.get('close_time', '16:00')
        )
        self.pre_market_start = self._parse_time(
            config.get('pre_market_start', '04:00')
        )
        self.after_market_end = self._parse_time(
            config.get('after_market_end', '20:00')
        )
        
        logger.info(
            f"Market hours initialized: "
            f"Open {self.market_open.strftime('%H:%M')}, "
            f"Close {self.market_close.strftime('%H:%M')}"
        )

    def _parse_time(self, time_str: str) -> time:
        """Parse time string in HH:MM format."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid time format {time_str}: {e}")
            # Return default values if parsing fails
            return time(9, 30) if 'open' in time_str else time(16, 0)

    def get_current_time(self) -> datetime:
        """Get current time in market timezone."""
        return datetime.now(self.timezone)

    def is_market_open(self, check_time: Optional[datetime] = None) -> bool:
        """Check if market is open.
        
        Args:
            check_time: Time to check (default: current time)
            
        Returns:
            bool: True if market is open
        """
        current = check_time or self.get_current_time()
        current_time = current.time()
        
        # Check if it's a weekday
        if current.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
            
        return self.market_open <= current_time <= self.market_close

    def is_pre_market(self, check_time: Optional[datetime] = None) -> bool:
        """Check if it's pre-market hours.
        
        Args:
            check_time: Time to check (default: current time)
            
        Returns:
            bool: True if it's pre-market hours
        """
        current = check_time or self.get_current_time()
        current_time = current.time()
        
        # Check if it's a weekday
        if current.weekday() >= 5:
            return False
            
        return self.pre_market_start <= current_time < self.market_open

    def is_after_market(self, check_time: Optional[datetime] = None) -> bool:
        """Check if it's after-market hours.
        
        Args:
            check_time: Time to check (default: current time)
            
        Returns:
            bool: True if it's after-market hours
        """
        current = check_time or self.get_current_time()
        current_time = current.time()
        
        # Check if it's a weekday
        if current.weekday() >= 5:
            return False
            
        return self.market_close < current_time <= self.after_market_end

    def is_trading_hours(self, check_time: Optional[datetime] = None) -> bool:
        """Check if it's any trading hours (pre, regular, or after).
        
        Args:
            check_time: Time to check (default: current time)
            
        Returns:
            bool: True if it's trading hours
        """
        return (
            self.is_pre_market(check_time) or
            self.is_market_open(check_time) or
            self.is_after_market(check_time)
        )

    def time_to_market_open(self, check_time: Optional[datetime] = None) -> float:
        """Get time until market open in seconds.
        
        Args:
            check_time: Time to check (default: current time)
            
        Returns:
            float: Seconds until market open, 0 if market is open
        """
        current = check_time or self.get_current_time()
        
        if self.is_market_open(current):
            return 0.0
            
        # If after market close, check next day
        if current.time() >= self.market_close:
            next_day = current.date() + pytz.timedelta(days=1)
            next_open = datetime.combine(
                next_day,
                self.market_open,
                tzinfo=self.timezone
            )
        else:
            next_open = datetime.combine(
                current.date(),
                self.market_open,
                tzinfo=self.timezone
            )
            
        return (next_open - current).total_seconds()

    def time_to_market_close(self, check_time: Optional[datetime] = None) -> float:
        """Get time until market close in seconds.
        
        Args:
            check_time: Time to check (default: current time)
            
        Returns:
            float: Seconds until market close, 0 if market is closed
        """
        current = check_time or self.get_current_time()
        
        if not self.is_market_open(current):
            return 0.0
            
        market_close = datetime.combine(
            current.date(),
            self.market_close,
            tzinfo=self.timezone
        )
        return (market_close - current).total_seconds() 