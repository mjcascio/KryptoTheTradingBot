#!/usr/bin/env python3
"""
Dashboard Connector for KryptoBot
Bridges the real-time logger with the dashboard for real-time updates
"""

import os
import sys
import json
import logging
import threading
import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to import dashboard
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard_connector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DashboardConnector:
    """
    Connects the real-time logger with the dashboard.
    Monitors the log file and updates the dashboard with new events.
    """
    
    def __init__(self, log_file: str = 'logs/trading_bot.out'):
        """
        Initialize the dashboard connector.
        
        Args:
            log_file: Path to the log file to monitor
        """
        self.log_file = log_file
        self.running = False
        self.thread = None
        self.dashboard_module = None
        
        # Try to import the dashboard module
        try:
            import dashboard
            self.dashboard_module = dashboard
            logger.info("Dashboard connector initialized and connected to dashboard")
        except ImportError:
            logger.warning("Dashboard module not found. Dashboard updates will be disabled.")
    
    def start(self):
        """Start monitoring the log file."""
        if self.running or not self.dashboard_module:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_log_file, daemon=True)
        self.thread.start()
        logger.info("Dashboard connector started")
    
    def stop(self):
        """Stop monitoring the log file."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.info("Dashboard connector stopped")
    
    def _monitor_log_file(self):
        """Monitor the log file for new events."""
        # Ensure log file exists
        if not os.path.exists(self.log_file):
            open(self.log_file, 'a').close()
        
        # Get current file size
        file_size = os.path.getsize(self.log_file)
        
        # Compile regex patterns for parsing log lines
        scan_pattern = re.compile(r'\[SCAN\] Analyzing symbol: (\w+)(?:\s*-\s*(.+))?')
        signal_pattern = re.compile(r'\[SIGNAL\] (\w+) - Action: (\w+), Confidence: ([\d.]+)(?:\s*-\s*(.+))?')
        trade_pattern = re.compile(r'\[TRADE\] (\w+) - (\w+) ([\d.]+) @ ([\d.]+)(?:\s*-\s*(.+))?')
        decision_pattern = re.compile(r'\[DECISION\] (.+?)(?:\s*-\s*(.+))?')
        
        while self.running:
            try:
                # Check if file has grown
                current_size = os.path.getsize(self.log_file)
                if current_size > file_size:
                    # Read new lines
                    with open(self.log_file, 'r') as f:
                        f.seek(file_size)
                        new_lines = f.read()
                    
                    # Update file size
                    file_size = current_size
                    
                    # Process new lines
                    for line in new_lines.splitlines():
                        # Parse timestamp
                        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                        timestamp = datetime.now().isoformat()
                        if timestamp_match:
                            try:
                                dt = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S,%f')
                                timestamp = dt.isoformat()
                            except ValueError:
                                pass
                        
                        # Check for scan events
                        scan_match = scan_pattern.search(line)
                        if scan_match:
                            symbol = scan_match.group(1)
                            status = scan_match.group(2) if scan_match.group(2) else "in progress"
                            self._handle_scan_event(symbol, status, timestamp)
                            continue
                        
                        # Check for signal events
                        signal_match = signal_pattern.search(line)
                        if signal_match:
                            symbol = signal_match.group(1)
                            action = signal_match.group(2)
                            confidence = float(signal_match.group(3))
                            details = signal_match.group(4) if signal_match.group(4) else None
                            self._handle_signal_event(symbol, action, confidence, details, timestamp)
                            continue
                        
                        # Check for trade events
                        trade_match = trade_pattern.search(line)
                        if trade_match:
                            symbol = trade_match.group(1)
                            side = trade_match.group(2)
                            quantity = float(trade_match.group(3))
                            price = float(trade_match.group(4))
                            details = trade_match.group(5) if trade_match.group(5) else None
                            self._handle_trade_event(symbol, side, quantity, price, details, timestamp)
                            continue
                        
                        # Check for decision events
                        decision_match = decision_pattern.search(line)
                        if decision_match:
                            message = decision_match.group(1)
                            details = decision_match.group(2) if decision_match.group(2) else None
                            self._handle_decision_event(message, details, timestamp)
                            continue
                
                # Sleep a bit to avoid high CPU usage
                time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error monitoring log file: {e}")
                time.sleep(1)  # Sleep longer on error
    
    def _handle_scan_event(self, symbol: str, status: str, timestamp: str):
        """
        Handle a scan event.
        
        Args:
            symbol: Symbol being scanned
            status: Scan status
            timestamp: Event timestamp
        """
        if not self.dashboard_module:
            return
        
        try:
            # Add to bot activity
            self.dashboard_module.add_bot_activity({
                'timestamp': timestamp,
                'message': f"Scanning {symbol} - {status}",
                'level': 'info',
                'type': 'scan'
            })
        except Exception as e:
            logger.error(f"Error handling scan event: {e}")
    
    def _handle_signal_event(self, symbol: str, action: str, confidence: float, details: Optional[str], timestamp: str):
        """
        Handle a signal event.
        
        Args:
            symbol: Symbol for the signal
            action: Signal action
            confidence: Signal confidence
            details: Additional signal details
            timestamp: Event timestamp
        """
        if not self.dashboard_module:
            return
        
        try:
            # Add to bot activity
            self.dashboard_module.add_bot_activity({
                'timestamp': timestamp,
                'message': f"Signal for {symbol}: {action} (confidence: {confidence:.2f})",
                'level': 'info',
                'type': 'signal'
            })
            
            # Add to ML predictions if confidence is high enough
            if confidence >= 0.6:
                self.dashboard_module.add_ml_prediction({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'prediction': action,
                    'confidence': confidence,
                    'features': {}
                })
        except Exception as e:
            logger.error(f"Error handling signal event: {e}")
    
    def _handle_trade_event(self, symbol: str, side: str, quantity: float, price: float, details: Optional[str], timestamp: str):
        """
        Handle a trade event.
        
        Args:
            symbol: Symbol being traded
            side: Trade side
            quantity: Trade quantity
            price: Trade price
            details: Additional trade details
            timestamp: Event timestamp
        """
        if not self.dashboard_module:
            return
        
        try:
            # Add to trades
            self.dashboard_module.add_trade({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'status': 'executed',
                'id': f"trade-{int(time.time())}"
            })
            
            # Add to bot activity
            self.dashboard_module.add_bot_activity({
                'timestamp': timestamp,
                'message': f"Trade executed: {side} {quantity} {symbol} @ {price}",
                'level': 'success',
                'type': 'trade'
            })
        except Exception as e:
            logger.error(f"Error handling trade event: {e}")
    
    def _handle_decision_event(self, message: str, details: Optional[str], timestamp: str):
        """
        Handle a decision event.
        
        Args:
            message: Decision message
            details: Additional decision details
            timestamp: Event timestamp
        """
        if not self.dashboard_module:
            return
        
        try:
            # Add to bot activity
            self.dashboard_module.add_bot_activity({
                'timestamp': timestamp,
                'message': message,
                'level': 'info',
                'type': 'decision'
            })
        except Exception as e:
            logger.error(f"Error handling decision event: {e}")

# Singleton instance
_instance = None

def get_connector():
    """
    Get the singleton dashboard connector instance.
    
    Returns:
        DashboardConnector: The dashboard connector instance
    """
    global _instance
    if _instance is None:
        _instance = DashboardConnector()
        _instance.start()
    return _instance

# Initialize the connector when this module is imported
get_connector() 