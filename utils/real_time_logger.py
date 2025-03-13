#!/usr/bin/env python3
"""
Real-Time Logger for KryptoBot
Ensures immediate log output for monitoring
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

class RealTimeLogger:
    """
    Real-time logger that ensures immediate log output.
    This is useful for monitoring the bot's activity in real-time.
    """
    
    def __init__(self, log_file: str = 'logs/trading_bot.out', level=logging.INFO):
        """
        Initialize the real-time logger.
        
        Args:
            log_file: Path to the log file
            level: Logging level
        """
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('kryptobot')
        self.logger.setLevel(level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add file handler with immediate flushing
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        
        # Set propagate to False to avoid duplicate logs
        self.logger.propagate = False
    
    def log(self, level: int, message: str):
        """
        Log a message with the specified level.
        
        Args:
            level: Logging level
            message: Message to log
        """
        self.logger.log(level, message)
        
        # Force flush all handlers
        for handler in self.logger.handlers:
            handler.flush()
    
    def debug(self, message: str):
        """Log a debug message."""
        self.log(logging.DEBUG, message)
    
    def info(self, message: str):
        """Log an info message."""
        self.log(logging.INFO, message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self.log(logging.WARNING, message)
    
    def error(self, message: str):
        """Log an error message."""
        self.log(logging.ERROR, message)
    
    def critical(self, message: str):
        """Log a critical message."""
        self.log(logging.CRITICAL, message)
    
    def scan(self, symbol: str, status: str = None, details: Dict[str, Any] = None):
        """
        Log a scan event.
        
        Args:
            symbol: Symbol being scanned
            status: Scan status (e.g., 'started', 'completed', 'failed')
            details: Additional scan details
        """
        message = f"[SCAN] Analyzing symbol: {symbol}"
        if status:
            message += f" - {status}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def signal(self, symbol: str, action: str, confidence: float, details: Dict[str, Any] = None):
        """
        Log a signal event.
        
        Args:
            symbol: Symbol for the signal
            action: Signal action (e.g., 'buy', 'sell', 'hold')
            confidence: Signal confidence (0.0 to 1.0)
            details: Additional signal details
        """
        message = f"[SIGNAL] {symbol} - Action: {action}, Confidence: {confidence:.2f}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def trade(self, symbol: str, side: str, quantity: float, price: float, details: Dict[str, Any] = None):
        """
        Log a trade event.
        
        Args:
            symbol: Symbol being traded
            side: Trade side (e.g., 'buy', 'sell')
            quantity: Trade quantity
            price: Trade price
            details: Additional trade details
        """
        message = f"[TRADE] {symbol} - {side} {quantity} @ {price}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def decision(self, message: str, details: Dict[str, Any] = None):
        """
        Log a decision event.
        
        Args:
            message: Decision message
            details: Additional decision details
        """
        full_message = f"[DECISION] {message}"
        if details:
            full_message += f" - {details}"
        self.info(full_message)

# Singleton instance
_instance = None

def get_logger() -> RealTimeLogger:
    """
    Get the singleton real-time logger instance.
    
    Returns:
        RealTimeLogger: The real-time logger instance
    """
    global _instance
    if _instance is None:
        _instance = RealTimeLogger()
    return _instance

# Convenience functions
def log_scan(symbol: str, status: str = None, details: Dict[str, Any] = None):
    """Log a scan event."""
    get_logger().scan(symbol, status, details)

def log_signal(symbol: str, action: str, confidence: float, details: Dict[str, Any] = None):
    """Log a signal event."""
    get_logger().signal(symbol, action, confidence, details)

def log_trade(symbol: str, side: str, quantity: float, price: float, details: Dict[str, Any] = None):
    """Log a trade event."""
    get_logger().trade(symbol, side, quantity, price, details)

def log_decision(message: str, details: Dict[str, Any] = None):
    """Log a decision event."""
    get_logger().decision(message, details)

def log_debug(message: str):
    """Log a debug message."""
    get_logger().debug(message)

def log_info(message: str):
    """Log an info message."""
    get_logger().info(message)

def log_warning(message: str):
    """Log a warning message."""
    get_logger().warning(message)

def log_error(message: str):
    """Log an error message."""
    get_logger().error(message)

def log_critical(message: str):
    """Log a critical message."""
    get_logger().critical(message) 