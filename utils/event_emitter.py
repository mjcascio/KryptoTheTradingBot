#!/usr/bin/env python3
"""
Event Emitter for KryptoBot
Handles real-time event emission for monitoring and dashboard updates
"""

import os
import json
import logging
import threading
import time
import socket
import queue
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class EventEmitter:
    """
    Event emitter for real-time monitoring of bot activities.
    Uses a combination of file-based logging and socket communication
    to ensure real-time updates across different components.
    """
    
    def __init__(self, log_file: str = 'logs/trading_bot.out'):
        """
        Initialize the event emitter.
        
        Args:
            log_file: Path to the log file
        """
        self.log_file = log_file
        self.event_queue = queue.Queue()
        self.listeners = []
        self.running = False
        self.thread = None
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Start the event processing thread
        self.start()
    
    def start(self):
        """Start the event processing thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_events, daemon=True)
        self.thread.start()
        logger.info("Event emitter started")
    
    def stop(self):
        """Stop the event processing thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.info("Event emitter stopped")
    
    def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event.
        
        Args:
            event_type: Type of event (e.g., 'scan', 'trade', 'signal')
            data: Event data
        """
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Create the event
        event = {
            'type': event_type,
            'data': data,
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        # Add to queue for processing
        self.event_queue.put(event)
    
    def add_listener(self, callback):
        """
        Add a listener for events.
        
        Args:
            callback: Function to call when an event is emitted
        """
        self.listeners.append(callback)
    
    def remove_listener(self, callback):
        """
        Remove a listener.
        
        Args:
            callback: Function to remove
        """
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def _process_events(self):
        """Process events from the queue."""
        while self.running:
            try:
                # Get event from queue (non-blocking)
                try:
                    event = self.event_queue.get(block=True, timeout=0.1)
                except queue.Empty:
                    continue
                
                # Log the event to file
                self._log_event(event)
                
                # Notify listeners
                for listener in self.listeners:
                    try:
                        listener(event)
                    except Exception as e:
                        logger.error(f"Error in event listener: {e}")
                
                # Mark as done
                self.event_queue.task_done()
            
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                time.sleep(0.1)  # Avoid tight loop on error
    
    def _log_event(self, event):
        """
        Log an event to the file.
        
        Args:
            event: Event to log
        """
        try:
            # Format the event for logging
            event_type = event['type'].upper()
            timestamp = datetime.fromisoformat(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # Format based on event type
            if event_type == 'SCAN':
                log_line = f"{timestamp} [SCAN] Analyzing symbol: {event['data'].get('symbol', 'UNKNOWN')}"
                if 'status' in event['data']:
                    log_line += f" - {event['data']['status']}"
            
            elif event_type == 'SIGNAL':
                log_line = f"{timestamp} [SIGNAL] {event['data'].get('symbol', 'UNKNOWN')} - "
                log_line += f"Action: {event['data'].get('action', 'UNKNOWN')}, "
                log_line += f"Confidence: {event['data'].get('confidence', 0.0):.2f}"
            
            elif event_type == 'TRADE':
                log_line = f"{timestamp} [TRADE] {event['data'].get('symbol', 'UNKNOWN')} - "
                log_line += f"{event['data'].get('side', 'UNKNOWN')} {event['data'].get('quantity', 0)} @ {event['data'].get('price', 0.0)}"
            
            elif event_type == 'DECISION':
                log_line = f"{timestamp} [DECISION] {event['data'].get('message', 'No message')}"
            
            else:
                # Generic format for other event types
                log_line = f"{timestamp} [{event_type}] {json.dumps(event['data'])}"
            
            # Write to log file
            with open(self.log_file, 'a') as f:
                f.write(log_line + '\n')
                f.flush()  # Ensure it's written immediately
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")

# Singleton instance
_instance = None

def get_emitter() -> EventEmitter:
    """
    Get the singleton event emitter instance.
    
    Returns:
        EventEmitter: The event emitter instance
    """
    global _instance
    if _instance is None:
        _instance = EventEmitter()
    return _instance

# Convenience functions
def emit_scan(symbol: str, status: str = None, details: Dict[str, Any] = None):
    """
    Emit a scan event.
    
    Args:
        symbol: Symbol being scanned
        status: Scan status (e.g., 'started', 'completed', 'failed')
        details: Additional scan details
    """
    data = {'symbol': symbol}
    if status:
        data['status'] = status
    if details:
        data.update(details)
    get_emitter().emit('scan', data)

def emit_signal(symbol: str, action: str, confidence: float, details: Dict[str, Any] = None):
    """
    Emit a signal event.
    
    Args:
        symbol: Symbol for the signal
        action: Signal action (e.g., 'buy', 'sell', 'hold')
        confidence: Signal confidence (0.0 to 1.0)
        details: Additional signal details
    """
    data = {
        'symbol': symbol,
        'action': action,
        'confidence': confidence
    }
    if details:
        data.update(details)
    get_emitter().emit('signal', data)

def emit_trade(symbol: str, side: str, quantity: float, price: float, details: Dict[str, Any] = None):
    """
    Emit a trade event.
    
    Args:
        symbol: Symbol being traded
        side: Trade side (e.g., 'buy', 'sell')
        quantity: Trade quantity
        price: Trade price
        details: Additional trade details
    """
    data = {
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'price': price
    }
    if details:
        data.update(details)
    get_emitter().emit('trade', data)

def emit_decision(message: str, details: Dict[str, Any] = None):
    """
    Emit a decision event.
    
    Args:
        message: Decision message
        details: Additional decision details
    """
    data = {'message': message}
    if details:
        data.update(details)
    get_emitter().emit('decision', data)

def emit_event(event_type: str, data: Dict[str, Any]):
    """
    Emit a custom event.
    
    Args:
        event_type: Type of event
        data: Event data
    """
    get_emitter().emit(event_type, data) 