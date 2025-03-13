"""Connection management utilities."""

import asyncio
import logging
import time
from typing import Optional, Callable, Awaitable, Dict, Any
import aiohttp
from .exceptions import ConnectionError, RateLimitError

logger = logging.getLogger(__name__)

class ConnectionManager:
    """API connection manager with retry and rate limiting."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_secret: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_second: int = 10
    ) -> None:
        """Initialize connection manager.
        
        Args:
            base_url: API base URL
            api_key: API key
            api_secret: API secret
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            rate_limit_per_second: Maximum requests per second
        """
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit_per_second
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0.0
        self._request_count = 0
    
    async def __aenter__(self):
        """Enter async context."""
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _wait_for_rate_limit(self):
        """Wait if rate limit is exceeded."""
        current_time = time.time()
        if current_time - self._last_request_time < 1.0:
            self._request_count += 1
            if self._request_count >= self.rate_limit:
                wait_time = 1.0 - (current_time - self._last_request_time)
                await asyncio.sleep(wait_time)
                self._request_count = 0
        else:
            self._last_request_time = current_time
            self._request_count = 1
    
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            API response
            
        Raises:
            ConnectionError: Connection failed
            RateLimitError: Rate limit exceeded
        """
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        retries = 0
        
        while retries < self.max_retries:
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                        logger.warning(f"Rate limit exceeded, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        retries += 1
                        continue
                    
                    if response.status >= 500:
                        logger.error(f"Server error: {response.status}")
                        retries += 1
                        await asyncio.sleep(self.retry_delay * (2 ** retries))
                        continue
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        raise ConnectionError(f"API error: {error_text}")
                    
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {str(e)}")
                retries += 1
                if retries < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** retries))
                else:
                    raise ConnectionError(f"Max retries exceeded: {str(e)}")
        
        raise ConnectionError("Max retries exceeded") 