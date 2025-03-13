#!/usr/bin/env python3
"""
Test script for real-time monitoring
Generates sample trading activity to verify monitoring functionality
"""

import os
import sys
import time
import random
import argparse
from datetime import datetime, timedelta
import threading

# Add utils directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))

# Import real-time logger
from utils.real_time_logger import log_scan, log_signal, log_trade, log_decision, log_info

# Sample symbols
SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "TSLA",
    "JPM", "V", "BAC", "MA", "WFC", "GS", "MS", "BLK"
]

def generate_random_price():
    """Generate a random price between 50 and 500."""
    return round(random.uniform(50, 500), 2)

def generate_random_quantity():
    """Generate a random quantity between 1 and 100."""
    return round(random.uniform(1, 100), 2)

def generate_random_confidence():
    """Generate a random confidence between 0.5 and 1.0."""
    return round(random.uniform(0.5, 1.0), 2)

def simulate_scanning(interval=5, duration=60):
    """
    Simulate scanning activity.
    
    Args:
        interval: Interval between scans in seconds
        duration: Duration of simulation in seconds
    """
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Select a random symbol
        symbol = random.choice(SYMBOLS)
        
        # Log scan
        log_scan(symbol, "started")
        
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.5))
        
        # Log scan completion
        status = random.choice(["completed", "failed"])
        details = {
            "duration": f"{random.uniform(0.1, 2.0):.2f}s",
            "data_points": random.randint(10, 100)
        }
        log_scan(symbol, status, details)
        
        # Wait for next scan
        time.sleep(interval)

def simulate_signals(interval=10, duration=60):
    """
    Simulate trading signals.
    
    Args:
        interval: Interval between signals in seconds
        duration: Duration of simulation in seconds
    """
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Select a random symbol
        symbol = random.choice(SYMBOLS)
        
        # Generate signal
        action = random.choice(["buy", "sell", "hold"])
        confidence = generate_random_confidence()
        details = {
            "reason": random.choice([
                "price breakout", 
                "volume spike", 
                "trend reversal",
                "support level",
                "resistance level"
            ]),
            "indicators": {
                "rsi": round(random.uniform(0, 100), 2),
                "macd": round(random.uniform(-10, 10), 2)
            }
        }
        
        # Log signal
        log_signal(symbol, action, confidence, details)
        
        # Wait for next signal
        time.sleep(interval)

def simulate_trades(interval=15, duration=60):
    """
    Simulate trades.
    
    Args:
        interval: Interval between trades in seconds
        duration: Duration of simulation in seconds
    """
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Select a random symbol
        symbol = random.choice(SYMBOLS)
        
        # Generate trade
        side = random.choice(["buy", "sell"])
        quantity = generate_random_quantity()
        price = generate_random_price()
        details = {
            "order_id": f"order-{int(time.time())}",
            "status": "filled",
            "timestamp": datetime.now().isoformat()
        }
        
        # Log trade
        log_trade(symbol, side, quantity, price, details)
        
        # Wait for next trade
        time.sleep(interval)

def simulate_decisions(interval=20, duration=60):
    """
    Simulate trading decisions.
    
    Args:
        interval: Interval between decisions in seconds
        duration: Duration of simulation in seconds
    """
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Generate decision
        decision_type = random.choice([
            "market_open", 
            "market_close", 
            "position_limit", 
            "risk_limit",
            "strategy_change"
        ])
        
        message = f"Decision made: {decision_type}"
        details = {
            "reason": random.choice([
                "scheduled event",
                "market conditions",
                "risk management",
                "portfolio rebalancing"
            ]),
            "timestamp": datetime.now().isoformat()
        }
        
        # Log decision
        log_decision(message, details)
        
        # Wait for next decision
        time.sleep(interval)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test real-time monitoring with simulated trading activity')
    parser.add_argument('-d', '--duration', type=int, default=300, help='Duration of simulation in seconds')
    parser.add_argument('-s', '--scan-interval', type=float, default=5, help='Interval between scans in seconds')
    parser.add_argument('-g', '--signal-interval', type=float, default=10, help='Interval between signals in seconds')
    parser.add_argument('-t', '--trade-interval', type=float, default=15, help='Interval between trades in seconds')
    parser.add_argument('-c', '--decision-interval', type=float, default=20, help='Interval between decisions in seconds')
    args = parser.parse_args()
    
    # Create a PID file to simulate a running bot
    with open('bot.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    try:
        log_info("Starting test monitoring simulation")
        log_info(f"Duration: {args.duration} seconds")
        log_info(f"Scan interval: {args.scan_interval} seconds")
        log_info(f"Signal interval: {args.signal_interval} seconds")
        log_info(f"Trade interval: {args.trade_interval} seconds")
        log_info(f"Decision interval: {args.decision_interval} seconds")
        
        # Start simulation threads
        threads = []
        
        scan_thread = threading.Thread(
            target=simulate_scanning, 
            args=(args.scan_interval, args.duration)
        )
        scan_thread.daemon = True
        threads.append(scan_thread)
        
        signal_thread = threading.Thread(
            target=simulate_signals, 
            args=(args.signal_interval, args.duration)
        )
        signal_thread.daemon = True
        threads.append(signal_thread)
        
        trade_thread = threading.Thread(
            target=simulate_trades, 
            args=(args.trade_interval, args.duration)
        )
        trade_thread.daemon = True
        threads.append(trade_thread)
        
        decision_thread = threading.Thread(
            target=simulate_decisions, 
            args=(args.decision_interval, args.duration)
        )
        decision_thread.daemon = True
        threads.append(decision_thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        log_info("Test monitoring simulation completed")
    
    finally:
        # Remove PID file
        if os.path.exists('bot.pid'):
            os.remove('bot.pid')

if __name__ == '__main__':
    main() 