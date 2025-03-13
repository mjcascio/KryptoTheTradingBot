"""Rate limiting and backoff strategies for API calls."""

import time
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, TypeVar, Callable, Any, Awaitable
from functools import wraps
import random

T = TypeVar('T')

@dataclass
class RateLimit:
    """Rate limit configuration."""
    calls: int  # Number of calls allowed
    period: int  # Time period in seconds
    retry_after: int = 60  # Time to wait after limit is hit

class RateLimiter:
    """Rate limiter with backoff strategies."""
    
    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self.limits: Dict[str, RateLimit] = {
            'alpaca': RateLimit(calls=200, period=60),  # 200 calls per minute
            'binance': RateLimit(calls=1200, period=60),  # 1200 calls per minute
            'coinbase': RateLimit(calls=100, period=60)  # 100 calls per minute
        }
        self.call_history: Dict[str, list[float]] = {}
        self._backoff_multiplier = 1.5
        self._max_backoff = 300  # 5 minutes

    def _cleanup_history(self, source: str, now: float) -> None:
        """Clean up old call history.
        
        Args:
            source: API source
            now: Current timestamp
        """
        if source in self.call_history:
            period = self.limits[source].period
            self.call_history[source] = [
                ts for ts in self.call_history[source]
                if now - ts <= period
            ]

    def _calculate_backoff(self, attempts: int) -> float:
        """Calculate backoff time using exponential strategy.
        
        Args:
            attempts: Number of retry attempts
            
        Returns:
            Backoff time in seconds
        """
        backoff = min(
            self._max_backoff,
            (self._backoff_multiplier ** attempts)
        )
        # Add jitter to prevent thundering herd
        return backoff * (0.9 + 0.2 * random.random())

    async def acquire(self, source: str) -> None:
        """Acquire a rate limit slot.
        
        Args:
            source: API source
        """
        now = time.time()
        self._cleanup_history(source, now)
        
        if source not in self.call_history:
            self.call_history[source] = []
        
        limit = self.limits[source]
        history = self.call_history[source]
        
        if len(history) >= limit.calls:
            # Calculate wait time
            oldest_call = min(history)
            wait_time = limit.period - (now - oldest_call)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # Recursive call after waiting
                await self.acquire(source)
                return
        
        # Add current call
        history.append(now)

    def rate_limited(self, source: str) -> Callable:
        """Decorator for rate limiting async functions.
        
        Args:
            source: API source
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                await self.acquire(source)
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    async def with_backoff(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        max_attempts: int = 3,
        **kwargs: Any
    ) -> T:
        """Execute function with exponential backoff.
        
        Args:
            func: Async function to execute
            max_attempts: Maximum number of retry attempts
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        attempt = 0
        last_error = None
        
        while attempt < max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                last_error = e
                
                if attempt < max_attempts:
                    backoff = self._calculate_backoff(attempt)
                    await asyncio.sleep(backoff)
        
        raise last_error or Exception("All retry attempts failed")

# Create global instance
rate_limiter = RateLimiter() 