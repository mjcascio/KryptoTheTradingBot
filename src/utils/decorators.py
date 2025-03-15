"""Utility decorators for the trading bot."""

import functools
import logging
import time
from typing import Any, Callable, Type, Union, Tuple

logger = logging.getLogger(__name__)


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
) -> Callable:
    """
    Decorator that retries a function call on exception.
    
    Args:
        max_retries: Maximum number of retries before giving up
        delay: Initial delay between retries in seconds
        backoff: Multiplier applied to delay between retries
        exceptions: Exception or tuple of exceptions to catch
        
    Returns:
        Decorated function that will retry on specified exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Failed after {max_retries} retries: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} "
                        f"failed: {str(e)}. Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached due to the raise in the loop
            raise last_exception if last_exception else RuntimeError("Unknown error")
            
        return wrapper
    return decorator


def rate_limited(
    calls: int = 1,
    period: float = 1.0,
    raise_on_limit: bool = False
) -> Callable:
    """
    Decorator that rate limits function calls.
    
    Args:
        calls: Number of calls allowed per period
        period: Time period in seconds
        raise_on_limit: Whether to raise an exception when rate limited
        
    Returns:
        Decorated function that is rate limited
    """
    def decorator(func: Callable) -> Callable:
        # Store last call timestamps
        last_calls = []
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()
            
            # Remove timestamps older than the period
            while last_calls and now - last_calls[0] > period:
                last_calls.pop(0)
            
            if len(last_calls) >= calls:
                wait_time = period - (now - last_calls[0])
                if raise_on_limit:
                    raise RuntimeError(
                        f"Rate limit exceeded. Try again in {wait_time:.1f}s"
                    )
                time.sleep(wait_time)
                # Recalculate now after sleeping
                now = time.time()
            
            last_calls.append(now)
            return func(*args, **kwargs)
            
        return wrapper
    return decorator 