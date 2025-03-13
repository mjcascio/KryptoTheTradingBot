#!/usr/bin/env python3
"""
Dashboard Bridge for KryptoBot
Connects the event emitter to the dashboard for real-time updates
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to import dashboard
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import event emitter
from utils.event_emitter import get_emitter

# Configure logging
logger = logging.getLogger(__name__)

class DashboardBridge:
    """
    Bridge between the event emitter and the dashboard.
    Listens for events from the event emitter and updates the dashboard.
    """
    
    def __init__(self):
        """Initialize the dashboard bridge."""
        self.emitter = get_emitter()
        self.dashboard_module = None
        self.connected = False
        
        # Try to import the dashboard module
        try:
            import dashboard
            self.dashboard_module = dashboard
            self.connected = True
            logger.info("Dashboard bridge initialized and connected to dashboard")
        except ImportError:
            logger.warning("Dashboard module not found. Dashboard updates will be disabled.")
    
    def connect(self):
        """Connect to the event emitter."""
        if not self.connected or not self.dashboard_module:
            logger.warning("Dashboard module not available. Cannot connect bridge.")
            return False
        
        # Register event listener
        self.emitter.add_listener(self.handle_event)
        logger.info("Dashboard bridge connected to event emitter")
        return True
    
    def disconnect(self):
        """Disconnect from the event emitter."""
        if not self.connected:
            return
        
        # Remove event listener
        self.emitter.remove_listener(self.handle_event)
        logger.info("Dashboard bridge disconnected from event emitter")
    
    def handle_event(self, event):
        """
        Handle an event from the event emitter.
        
        Args:
            event: Event to handle
        """
        if not self.connected or not self.dashboard_module:
            return
        
        try:
            event_type = event['type'].lower()
            data = event['data']
            
            # Update dashboard based on event type
            if event_type == 'scan':
                self._handle_scan_event(data)
            elif event_type == 'signal':
                self._handle_signal_event(data)
            elif event_type == 'trade':
                self._handle_trade_event(data)
            elif event_type == 'decision':
                self._handle_decision_event(data)
            elif event_type == 'market_status':
                self._handle_market_status_event(data)
            elif event_type == 'sleep_status':
                self._handle_sleep_status_event(data)
            elif event_type == 'account':
                self._handle_account_event(data)
            elif event_type == 'position':
                self._handle_position_event(data)
            elif event_type == 'equity':
                self._handle_equity_event(data)
            elif event_type == 'ml_prediction':
                self._handle_ml_prediction_event(data)
            else:
                # Generic event handling
                self._handle_generic_event(event_type, data)
        
        except Exception as e:
            logger.error(f"Error handling event in dashboard bridge: {e}")
    
    def _handle_scan_event(self, data):
        """Handle a scan event."""
        # Add to bot activity
        self.dashboard_module.add_bot_activity({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'message': f"Scanning {data.get('symbol', 'UNKNOWN')} - {data.get('status', 'in progress')}",
            'level': 'info',
            'type': 'scan'
        })
    
    def _handle_signal_event(self, data):
        """Handle a signal event."""
        # Add to bot activity
        self.dashboard_module.add_bot_activity({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'message': f"Signal for {data.get('symbol', 'UNKNOWN')}: {data.get('action', 'UNKNOWN')} (confidence: {data.get('confidence', 0.0):.2f})",
            'level': 'info',
            'type': 'signal'
        })
        
        # Add to ML predictions if confidence is high enough
        if data.get('confidence', 0.0) >= 0.6:
            self.dashboard_module.add_ml_prediction({
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'symbol': data.get('symbol', 'UNKNOWN'),
                'prediction': data.get('action', 'UNKNOWN'),
                'confidence': data.get('confidence', 0.0),
                'features': data.get('features', {})
            })
    
    def _handle_trade_event(self, data):
        """Handle a trade event."""
        # Add to trades
        self.dashboard_module.add_trade({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'symbol': data.get('symbol', 'UNKNOWN'),
            'side': data.get('side', 'UNKNOWN'),
            'quantity': data.get('quantity', 0),
            'price': data.get('price', 0.0),
            'status': data.get('status', 'executed'),
            'id': data.get('id', f"trade-{int(time.time())}")
        })
        
        # Add to bot activity
        self.dashboard_module.add_bot_activity({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'message': f"Trade executed: {data.get('side', 'UNKNOWN')} {data.get('quantity', 0)} {data.get('symbol', 'UNKNOWN')} @ {data.get('price', 0.0)}",
            'level': 'success',
            'type': 'trade'
        })
    
    def _handle_decision_event(self, data):
        """Handle a decision event."""
        # Add to bot activity
        self.dashboard_module.add_bot_activity({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'message': data.get('message', 'Decision made'),
            'level': data.get('level', 'info'),
            'type': 'decision'
        })
    
    def _handle_market_status_event(self, data):
        """Handle a market status event."""
        self.dashboard_module.update_market_status(
            data.get('is_open', False),
            data.get('next_open'),
            data.get('next_close')
        )
    
    def _handle_sleep_status_event(self, data):
        """Handle a sleep status event."""
        self.dashboard_module.update_sleep_status(data)
    
    def _handle_account_event(self, data):
        """Handle an account event."""
        self.dashboard_module.update_account(data)
    
    def _handle_position_event(self, data):
        """Handle a position event."""
        self.dashboard_module.update_position(
            data.get('symbol', 'UNKNOWN'),
            {
                'quantity': data.get('quantity', 0),
                'avg_price': data.get('avg_price', 0.0),
                'current_price': data.get('current_price', 0.0),
                'market_value': data.get('market_value', 0.0),
                'unrealized_pl': data.get('unrealized_pl', 0.0),
                'unrealized_plpc': data.get('unrealized_plpc', 0.0),
                'side': data.get('side', 'long')
            }
        )
    
    def _handle_equity_event(self, data):
        """Handle an equity event."""
        self.dashboard_module.update_equity(data.get('equity', 0.0))
    
    def _handle_ml_prediction_event(self, data):
        """Handle an ML prediction event."""
        self.dashboard_module.add_ml_prediction(data)
    
    def _handle_generic_event(self, event_type, data):
        """Handle a generic event."""
        # Add to bot activity
        self.dashboard_module.add_bot_activity({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'message': f"{event_type.upper()}: {json.dumps(data)}",
            'level': 'info',
            'type': event_type
        })

# Singleton instance
_instance = None

def get_bridge():
    """
    Get the singleton dashboard bridge instance.
    
    Returns:
        DashboardBridge: The dashboard bridge instance
    """
    global _instance
    if _instance is None:
        _instance = DashboardBridge()
        _instance.connect()
    return _instance

# Initialize the bridge when this module is imported
get_bridge() 