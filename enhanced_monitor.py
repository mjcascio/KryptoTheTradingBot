#!/usr/bin/env python3
"""
Enhanced Real-Time Monitor for KryptoBot
Provides a rich terminal interface for monitoring bot activity in real-time
"""

import os
import sys
import time
import json
import argparse
import threading
import curses
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add utils directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))

# Import event emitter
from utils.event_emitter import get_emitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedMonitor:
    """
    Enhanced real-time monitor for KryptoBot.
    Provides a rich terminal interface for monitoring bot activity.
    """
    
    def __init__(self, filter_type=None, symbols=None):
        """
        Initialize the monitor.
        
        Args:
            filter_type: Type of events to filter (e.g., 'scan', 'signal', 'trade')
            symbols: List of symbols to filter
        """
        self.filter_type = filter_type
        self.symbols = symbols or []
        self.events = []
        self.max_events = 100
        self.running = False
        self.emitter = get_emitter()
        self.lock = threading.Lock()
        
        # Check if bot is running
        self._check_bot_running()
    
    def _check_bot_running(self):
        """Check if the bot is running."""
        pid_file = os.path.join(os.path.dirname(__file__), 'bot.pid')
        if not os.path.exists(pid_file):
            logger.warning("Bot PID file not found. Bot may not be running.")
            return False
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)
            logger.info(f"Bot is running with PID {pid}")
            return True
        except (OSError, ValueError):
            logger.warning("Bot PID file exists but bot is not running.")
            return False
    
    def start(self):
        """Start the monitor."""
        if self.running:
            return
        
        self.running = True
        
        # Register event listener
        self.emitter.add_listener(self.handle_event)
        
        # Start curses interface
        curses.wrapper(self._run_interface)
    
    def stop(self):
        """Stop the monitor."""
        self.running = False
        
        # Remove event listener
        self.emitter.remove_listener(self.handle_event)
    
    def handle_event(self, event):
        """
        Handle an event from the event emitter.
        
        Args:
            event: Event to handle
        """
        # Apply filters
        if self.filter_type and event['type'].lower() != self.filter_type.lower():
            return
        
        if self.symbols and event['data'].get('symbol') not in self.symbols:
            return
        
        # Add to events list
        with self.lock:
            self.events.append(event)
            
            # Keep only the last N events
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
    
    def _run_interface(self, stdscr):
        """
        Run the curses interface.
        
        Args:
            stdscr: Curses standard screen
        """
        # Set up colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)  # Success
        curses.init_pair(2, curses.COLOR_RED, -1)    # Error
        curses.init_pair(3, curses.COLOR_YELLOW, -1) # Warning
        curses.init_pair(4, curses.COLOR_CYAN, -1)   # Info
        curses.init_pair(5, curses.COLOR_BLUE, -1)   # Scan
        curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Signal
        
        # Hide cursor
        curses.curs_set(0)
        
        # Enable keypad
        stdscr.keypad(True)
        
        # Set non-blocking input
        stdscr.nodelay(True)
        
        # Main loop
        while self.running:
            try:
                # Check for key press
                key = stdscr.getch()
                if key == ord('q'):
                    self.running = False
                    break
                
                # Clear screen
                stdscr.clear()
                
                # Get terminal size
                max_y, max_x = stdscr.getmaxyx()
                
                # Draw header
                header = "KryptoBot Real-Time Monitor"
                filter_info = ""
                if self.filter_type:
                    filter_info += f" | Filter: {self.filter_type.upper()}"
                if self.symbols:
                    filter_info += f" | Symbols: {', '.join(self.symbols)}"
                
                stdscr.addstr(0, 0, header, curses.A_BOLD)
                stdscr.addstr(0, len(header), filter_info)
                
                # Draw help
                help_text = " | Press 'q' to quit"
                stdscr.addstr(0, max_x - len(help_text) - 1, help_text)
                
                # Draw separator
                stdscr.addstr(1, 0, "=" * (max_x - 1))
                
                # Draw events
                y = 2
                with self.lock:
                    for event in reversed(self.events):
                        if y >= max_y - 1:
                            break
                        
                        # Format event
                        event_type = event['type'].upper()
                        timestamp = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')
                        data = event['data']
                        
                        # Determine color
                        color = 0
                        if event_type == 'TRADE':
                            color = curses.color_pair(1)  # Green
                        elif event_type == 'ERROR':
                            color = curses.color_pair(2)  # Red
                        elif event_type == 'WARNING':
                            color = curses.color_pair(3)  # Yellow
                        elif event_type == 'SCAN':
                            color = curses.color_pair(5)  # Blue
                        elif event_type == 'SIGNAL':
                            color = curses.color_pair(6)  # Magenta
                        else:
                            color = curses.color_pair(4)  # Cyan
                        
                        # Format message based on event type
                        if event_type == 'SCAN':
                            message = f"Scanning {data.get('symbol', 'UNKNOWN')}"
                            if 'status' in data:
                                message += f" - {data['status']}"
                        
                        elif event_type == 'SIGNAL':
                            message = f"{data.get('symbol', 'UNKNOWN')}: {data.get('action', 'UNKNOWN')}"
                            message += f" (confidence: {data.get('confidence', 0.0):.2f})"
                        
                        elif event_type == 'TRADE':
                            message = f"{data.get('symbol', 'UNKNOWN')}: {data.get('side', 'UNKNOWN')}"
                            message += f" {data.get('quantity', 0)} @ {data.get('price', 0.0)}"
                        
                        elif event_type == 'DECISION':
                            message = data.get('message', 'Decision made')
                        
                        else:
                            # Generic format for other event types
                            message = json.dumps(data)
                        
                        # Truncate message if too long
                        if len(message) > max_x - 20:
                            message = message[:max_x - 23] + "..."
                        
                        # Draw event
                        stdscr.addstr(y, 0, f"[{timestamp}]", curses.A_BOLD)
                        stdscr.addstr(y, 11, f"[{event_type}]", color | curses.A_BOLD)
                        stdscr.addstr(y, 20, message)
                        
                        y += 1
                
                # Draw footer
                stdscr.addstr(max_y - 1, 0, "=" * (max_x - 1))
                status = f"Events: {len(self.events)}"
                if self.filter_type or self.symbols:
                    status += " (filtered)"
                stdscr.addstr(max_y - 1, 0, status)
                
                # Refresh screen
                stdscr.refresh()
                
                # Sleep a bit
                time.sleep(0.1)
            
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                # Log error and continue
                logger.error(f"Error in monitor interface: {e}")
                time.sleep(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Enhanced Real-Time Monitor for KryptoBot')
    parser.add_argument('-t', '--type', help='Filter by event type (e.g., scan, signal, trade)')
    parser.add_argument('-s', '--symbols', help='Filter by symbols (comma-separated)')
    args = parser.parse_args()
    
    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',')]
    
    # Create and start monitor
    monitor = EnhancedMonitor(filter_type=args.type, symbols=symbols)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()

if __name__ == '__main__':
    main() 