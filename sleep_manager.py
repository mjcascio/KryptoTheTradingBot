import logging
from datetime import datetime, time, timedelta
import pytz
from typing import Optional
from config import SLEEP_MODE, TIMEZONE

logger = logging.getLogger(__name__)

class SleepManager:
    """Manages the bot's sleep mode functionality"""
    
    def __init__(self):
        """Initialize the sleep manager"""
        self.enabled = SLEEP_MODE["enabled"]
        self.night_mode = SLEEP_MODE["night"]
        self.weekend_mode = SLEEP_MODE["weekend"]
        self.timezone = pytz.timezone(TIMEZONE)
        self.is_sleeping = False
        self.sleep_reason = None
        
    def should_sleep(self) -> bool:
        """Check if the bot should be in sleep mode"""
        if not self.enabled:
            return False
            
        now = datetime.now(self.timezone)
        current_time = now.time()
        
        # Check weekend sleep mode
        if self.weekend_mode["enabled"]:
            if self._is_weekend_sleep_time(now):
                self.sleep_reason = "weekend"
                return True
        
        # Check night sleep mode
        if self.night_mode["enabled"]:
            if self._is_night_sleep_time(current_time):
                self.sleep_reason = "night"
                return True
        
        self.sleep_reason = None
        return False
    
    def _is_weekend_sleep_time(self, now: datetime) -> bool:
        """Check if current time falls within weekend sleep period"""
        current_day = now.weekday()
        current_time = now.time()
        
        sleep_day = self.weekend_mode["sleep_day"]
        wake_day = self.weekend_mode["wake_day"]
        sleep_time = self._parse_time(self.weekend_mode["sleep_time"])
        wake_time = self._parse_time(self.weekend_mode["wake_time"])
        
        # Friday after sleep_time until Monday before wake_time
        if current_day == sleep_day and current_time >= sleep_time:
            return True
        if current_day > sleep_day or current_day < wake_day:
            return True
        if current_day == wake_day and current_time < wake_time:
            return True
            
        return False
    
    def _is_night_sleep_time(self, current_time: time) -> bool:
        """Check if current time falls within night sleep period"""
        sleep_time = self._parse_time(self.night_mode["sleep_time"])
        wake_time = self._parse_time(self.night_mode["wake_time"])
        
        # Handle overnight periods
        if sleep_time > wake_time:
            return current_time >= sleep_time or current_time < wake_time
        else:
            return current_time >= sleep_time and current_time < wake_time
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string in HH:MM format to time object"""
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)
    
    def enter_sleep_mode(self) -> None:
        """Actions to perform when entering sleep mode"""
        if not self.is_sleeping:
            self.is_sleeping = True
            if SLEEP_MODE["logging"]["sleep_events"]:
                logger.info(f"Entering sleep mode. Reason: {self.sleep_reason}")
    
    def exit_sleep_mode(self) -> None:
        """Actions to perform when exiting sleep mode"""
        if self.is_sleeping:
            self.is_sleeping = False
            if SLEEP_MODE["logging"]["sleep_events"]:
                logger.info("Exiting sleep mode")
    
    def get_next_wake_time(self) -> Optional[datetime]:
        """Calculate the next wake time based on current sleep state"""
        if not self.is_sleeping:
            return None
            
        now = datetime.now(self.timezone)
        
        if self.sleep_reason == "weekend":
            # Calculate next Monday wake time
            days_until_monday = (7 - now.weekday() + self.weekend_mode["wake_day"]) % 7
            wake_time = self._parse_time(self.weekend_mode["wake_time"])
            next_wake = now.replace(
                hour=wake_time.hour,
                minute=wake_time.minute,
                second=0,
                microsecond=0
            ) + timedelta(days=days_until_monday)
            
        else:  # night sleep
            # Calculate next wake time
            wake_time = self._parse_time(self.night_mode["wake_time"])
            next_wake = now.replace(
                hour=wake_time.hour,
                minute=wake_time.minute,
                second=0,
                microsecond=0
            )
            
            # If wake time is earlier today, move to tomorrow
            if next_wake <= now:
                next_wake = next_wake + timedelta(days=1)
        
        return next_wake
    
    def get_sleep_status(self) -> dict:
        """Get current sleep mode status"""
        return {
            "is_sleeping": self.is_sleeping,
            "reason": self.sleep_reason,
            "next_wake_time": self.get_next_wake_time() if self.is_sleeping else None
        } 