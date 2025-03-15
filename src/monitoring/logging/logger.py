"""
Centralized logging configuration for KryptoTheTradingBot.
Provides standardized logging across all modules with different handlers and formatters.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any


class KryptoLogger:
    """Centralized logging configuration for the trading bot."""
    
    def __init__(self, name: str, log_dir: str = "logs") -> None:
        """
        Initialize the logger with the given name and log directory.
        
        Args:
            name: The name of the logger (usually __name__ of the module)
            log_dir: Directory to store log files
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create the logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        self.logger.handlers.clear()
        
        # Add handlers
        self._add_file_handler()
        self._add_console_handler()
        self._add_error_handler()
        
    def _add_file_handler(self) -> None:
        """Add a rotating file handler for all logs."""
        log_file = self.log_dir / f"{self.name}.log"
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _add_console_handler(self) -> None:
        """Add a console handler for INFO and above."""
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _add_error_handler(self) -> None:
        """Add a separate handler for ERROR and above."""
        error_file = self.log_dir / f"{self.name}_error.log"
        handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5_000_000,  # 5MB
            backupCount=3
        )
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'Exception Info: %(exc_info)s\n'
            'Additional Data: %(extra)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    def log_with_context(self, level: int, msg: str, context: Dict[str, Any]) -> None:
        """
        Log a message with additional context.
        
        Args:
            level: The logging level (e.g., logging.INFO)
            msg: The message to log
            context: Dictionary of additional context to include
        """
        extra = {'extra': context}
        self.logger.log(level, msg, extra=extra)


# Create a default logger instance
default_logger = KryptoLogger("krypto_bot").get_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with the given name."""
    if name is None:
        return default_logger
    return KryptoLogger(name).get_logger()


def log_with_context(level: int, msg: str, context: Dict[str, Any],
                    logger: Optional[logging.Logger] = None) -> None:
    """
    Log a message with additional context using the specified or default logger.
    
    Args:
        level: The logging level (e.g., logging.INFO)
        msg: The message to log
        context: Dictionary of additional context to include
        logger: Optional logger instance to use (uses default if None)
    """
    if logger is None:
        logger = default_logger
    extra = {'extra': context}
    logger.log(level, msg, extra=extra) 