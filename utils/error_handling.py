"""Error handling utilities for the KryptoBot Trading System."""

import logging
import functools
import traceback
from typing import Callable, Dict, Type, Any, Optional, Coroutine
import asyncio
import time

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Error handling system for the KryptoBot Trading System."""
    
    def __init__(self, logger_instance=None):
        """Initialize the error handler.
        
        Args:
            logger_instance: Logger instance to use (uses module logger if None)
        """
        self.logger = logger_instance or logger
        self.error_callbacks = {}
        self.error_counts = {}
        self.max_retries = 3
        
    def register_callback(self, error_type: Type[Exception], callback: Callable):
        """Register a callback for a specific error type.
        
        Args:
            error_type: Type of exception to handle
            callback: Callback function to execute when the error occurs
        """
        self.error_callbacks[error_type] = callback
        self.logger.debug(f"Registered callback for {error_type.__name__}")
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle an error by executing the appropriate callback.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            True if the error was handled, False otherwise
        """
        error_type = type(error)
        context = context or {}
        
        # Log the error
        self.logger.error(f"Error occurred: {error}")
        if 'traceback' not in context:
            context['traceback'] = traceback.format_exc()
            
        # Update error counts
        error_name = error_type.__name__
        self.error_counts[error_name] = self.error_counts.get(error_name, 0) + 1
        
        # Find and execute the appropriate callback
        for err_type, callback in self.error_callbacks.items():
            if isinstance(error, err_type):
                try:
                    callback(error, context)
                    self.logger.info(f"Executed callback for {error_name}")
                    return True
                except Exception as callback_error:
                    self.logger.error(f"Error in callback for {error_name}: {callback_error}")
                    return False
                
        self.logger.warning(f"No callback registered for {error_name}")
        return False
        
    def wrap(self, func: Callable) -> Callable:
        """Wrap a function with error handling.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function with error handling
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                self.handle_error(e, context)
                raise
                
        return wrapper
        
    def wrap_async(self, func: Callable) -> Callable:
        """Wrap an async function with error handling.
        
        Args:
            func: Async function to wrap
            
        Returns:
            Wrapped async function with error handling
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                self.handle_error(e, context)
                raise
                
        return wrapper
        
    def retry(self, max_retries: int = None, retry_delay: float = 1.0):
        """Decorator to retry a function on failure.
        
        Args:
            max_retries: Maximum number of retries (uses instance default if None)
            retry_delay: Delay between retries in seconds
            
        Returns:
            Decorator function
        """
        max_retries = max_retries if max_retries is not None else self.max_retries
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries:
                            self.logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__} after error: {e}"
                            )
                            time.sleep(retry_delay)
                        else:
                            context = {
                                'function': func.__name__,
                                'args': args,
                                'kwargs': kwargs,
                                'attempts': attempt + 1
                            }
                            self.handle_error(last_error, context)
                            raise
                
                # This should never be reached
                raise last_error
                
            return wrapper
            
        return decorator
        
    def retry_async(self, max_retries: int = None, retry_delay: float = 1.0):
        """Decorator to retry an async function on failure.
        
        Args:
            max_retries: Maximum number of retries (uses instance default if None)
            retry_delay: Delay between retries in seconds
            
        Returns:
            Decorator function
        """
        max_retries = max_retries if max_retries is not None else self.max_retries
        
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries:
                            self.logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__} after error: {e}"
                            )
                            await asyncio.sleep(retry_delay)
                        else:
                            context = {
                                'function': func.__name__,
                                'args': args,
                                'kwargs': kwargs,
                                'attempts': attempt + 1
                            }
                            self.handle_error(last_error, context)
                            raise
                
                # This should never be reached
                raise last_error
                
            return wrapper
            
        return decorator
        
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics.
        
        Returns:
            Dictionary with error counts by type
        """
        return self.error_counts.copy() 