"""Caching system for frequently accessed data."""

import time
from typing import Dict, Any, Optional, TypeVar, Generic, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with value and metadata."""
    
    value: T
    timestamp: float
    expiry: float

class Cache:
    """Thread-safe cache with automatic expiration."""
    
    def __init__(self, cleanup_interval: float = 300):
        """Initialize cache.
        
        Args:
            cleanup_interval: Interval for cleanup task in seconds
        """
        self._data: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start cache cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop cache cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """Periodic cleanup of expired entries."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")
    
    async def cleanup(self):
        """Remove expired entries."""
        current_time = time.time()
        async with self._lock:
            expired = [
                key for key, entry in self._data.items()
                if current_time > entry.expiry
            ]
            for key in expired:
                del self._data[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        current_time = time.time()
        async with self._lock:
            if key in self._data:
                entry = self._data[key]
                if current_time <= entry.expiry:
                    return entry.value
                del self._data[key]
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: float
    ) -> None:
        """Set cache value with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        current_time = time.time()
        entry = CacheEntry(
            value=value,
            timestamp=current_time,
            expiry=current_time + ttl
        )
        async with self._lock:
            self._data[key] = entry
    
    async def delete(self, key: str) -> None:
        """Delete cache entry.
        
        Args:
            key: Cache key
        """
        async with self._lock:
            if key in self._data:
                del self._data[key]

def cached(ttl: float):
    """Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func):
        cache = Cache()
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

class DataCache:
    """Specialized cache for market data."""
    
    def __init__(self):
        """Initialize data cache."""
        self.ohlcv_cache = Cache()
        self.orderbook_cache = Cache()
        self.ticker_cache = Cache()
    
    async def start(self):
        """Start all cache instances."""
        await self.ohlcv_cache.start()
        await self.orderbook_cache.start()
        await self.ticker_cache.start()
    
    async def stop(self):
        """Stop all cache instances."""
        await self.ohlcv_cache.stop()
        await self.orderbook_cache.stop()
        await self.ticker_cache.stop()
    
    def get_cache_key(
        self,
        symbol: str,
        data_type: str,
        **params
    ) -> str:
        """Generate cache key.
        
        Args:
            symbol: Trading pair symbol
            data_type: Type of data
            **params: Additional parameters
            
        Returns:
            Cache key
        """
        key_parts = [symbol, data_type]
        key_parts.extend(f"{k}={v}" for k, v in sorted(params.items()))
        return ":".join(key_parts)
    
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[Any]:
        """Get cached OHLCV data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            limit: Number of candles
            
        Returns:
            Cached OHLCV data or None
        """
        key = self.get_cache_key(
            symbol,
            "ohlcv",
            timeframe=timeframe,
            limit=limit
        )
        return await self.ohlcv_cache.get(key)
    
    async def set_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        data: Any,
        ttl: float = 60
    ) -> None:
        """Cache OHLCV data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            limit: Number of candles
            data: OHLCV data
            ttl: Cache TTL in seconds
        """
        key = self.get_cache_key(
            symbol,
            "ohlcv",
            timeframe=timeframe,
            limit=limit
        )
        await self.ohlcv_cache.set(key, data, ttl)
    
    async def get_orderbook(
        self,
        symbol: str,
        limit: int
    ) -> Optional[Any]:
        """Get cached order book.
        
        Args:
            symbol: Trading pair symbol
            limit: Order book depth
            
        Returns:
            Cached order book or None
        """
        key = self.get_cache_key(symbol, "orderbook", limit=limit)
        return await self.orderbook_cache.get(key)
    
    async def set_orderbook(
        self,
        symbol: str,
        limit: int,
        data: Any,
        ttl: float = 1
    ) -> None:
        """Cache order book.
        
        Args:
            symbol: Trading pair symbol
            limit: Order book depth
            data: Order book data
            ttl: Cache TTL in seconds
        """
        key = self.get_cache_key(symbol, "orderbook", limit=limit)
        await self.orderbook_cache.set(key, data, ttl)
    
    async def get_ticker(self, symbol: str) -> Optional[Any]:
        """Get cached ticker.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Cached ticker or None
        """
        key = self.get_cache_key(symbol, "ticker")
        return await self.ticker_cache.get(key)
    
    async def set_ticker(
        self,
        symbol: str,
        data: Any,
        ttl: float = 1
    ) -> None:
        """Cache ticker.
        
        Args:
            symbol: Trading pair symbol
            data: Ticker data
            ttl: Cache TTL in seconds
        """
        key = self.get_cache_key(symbol, "ticker")
        await self.ticker_cache.set(key, data, ttl) 