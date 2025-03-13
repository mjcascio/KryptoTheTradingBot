"""Logging utilities for the KryptoBot Trading System."""

import os
import sys
import logging
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any
from functools import wraps
from config.settings import DASHBOARD_LOG_DIR, TRADING_BOT_LOG

# Custom log levels
TRADE = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(TRADE, 'TRADE')

class KryptoLogger(logging.Logger):
    """Custom logger class with additional trading-specific methods."""
    
    def trade(self, msg: str, *args, **kwargs):
        """Log a trade-related message."""
        if self.isEnabledFor(TRADE):
            self._log(TRADE, msg, args, **kwargs)
    
    def exception_context(self, msg: str, exc_info: Exception, context: Dict[str, Any] = None):
        """Log an exception with additional context."""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Format the error message with context
        error_msg = f"{msg}\nException: {str(exc_info)}"
        if context:
            error_msg += f"\nContext: {context}"
        
        # Add traceback information
        if exc_traceback:
            error_msg += f"\nTraceback:\n{''.join(traceback.format_tb(exc_traceback))}"
        
        self.error(error_msg)

# Register the custom logger class
logging.setLoggerClass(KryptoLogger)

def setup_logging(
    name: str,
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    max_bytes: int = 10*1024*1024,  # 10MB
    backup_count: int = 5,
    include_time_rotation: bool = True
) -> logging.Logger:
    """Set up logging configuration for a module
    
    Args:
        name: Name of the logger
        log_file: Optional log file path. If not provided, uses the default trading bot log
        log_level: Logging level (default: INFO)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        include_time_rotation: Whether to also rotate logs based on time
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Create file handlers
    if log_file is None:
        log_file = os.path.join(DASHBOARD_LOG_DIR, TRADING_BOT_LOG)
    
    # Size-based rotation handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    
    # Time-based rotation handler (if enabled)
    if include_time_rotation:
        time_handler = TimedRotatingFileHandler(
            log_file + '.daily',
            when='midnight',
            interval=1,
            backupCount=30  # Keep 30 days of logs
        )
        time_handler.setLevel(log_level)
        time_handler.setFormatter(detailed_formatter)
        logger.addHandler(time_handler)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_exception(logger: logging.Logger):
    """Decorator to log exceptions with context
    
    Args:
        logger: Logger instance to use for logging
    
    Example:
        @log_exception(logger)
        def risky_operation():
            # This function will have exceptions logged
            result = perform_risky_task()
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create context dictionary
                context = {
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Log the exception with context
                logger.exception_context(
                    f"Error in {func.__name__}",
                    e,
                    context
                )
                raise  # Re-raise the exception after logging
        return wrapper
    return decorator

def setup_trade_logging(symbol: str) -> logging.Logger:
    """Set up specialized logging for trade operations
    
    Args:
        symbol: Trading symbol to create logger for
        
    Returns:
        Logger configured for trade logging
    """
    # Create trade-specific log file
    trade_log_file = os.path.join(
        DASHBOARD_LOG_DIR,
        f"trades_{symbol.lower()}_{datetime.now().strftime('%Y%m')}.log"
    )
    
    # Set up logger with trade-specific configuration
    logger = setup_logging(
        f"trades.{symbol}",
        trade_log_file,
        log_level=TRADE,
        include_time_rotation=True
    )
    
    return logger 