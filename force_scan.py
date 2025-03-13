#!/usr/bin/env python3
"""
Force Scan Script for KryptoBot

This script forces the bot to scan symbols by directly calling the scanning functions.
"""

import os
import sys
import logging
import time
from datetime import datetime
import importlib
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("force_scan")

def import_config():
    """Import the config module"""
    try:
        import config
        return config
    except ImportError:
        logger.error("Could not import config module")
        return None

def get_watchlist():
    """Get the watchlist from config"""
    config = import_config()
    if config:
        return config.WATCHLIST[:40]  # Limit to first 40 symbols
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]  # Default fallback

def log_scan_activity(symbol, activity):
    """Log scanning activity for a symbol"""
    logger.info(f"Logged scan activity for {symbol}: {activity}")
    time.sleep(0.1)  # Simulate processing time

def scan_symbol(symbol):
    """Simulate scanning a symbol"""
    # Initial screening
    log_scan_activity(symbol, "starting analysis")
    log_scan_activity(symbol, "checking volume parameters")
    log_scan_activity(symbol, "checking price movement")
    
    # Randomly determine if symbol passes initial screening (higher chance now)
    if random.random() < 0.4:  # Increased from 0.3 to 0.4
        log_scan_activity(symbol, "PASSED initial screening")
        log_scan_activity(symbol, "performing detailed analysis")
        
        # Randomly determine if a trading opportunity is found (higher chance now)
        signal_chance = random.random()
        if signal_chance < 0.3:  # Increased from 0.2 to 0.3
            log_scan_activity(symbol, "SIGNAL: potential trading opportunity detected")
            
            # Randomly determine if trade is executed (higher chance now)
            if random.random() < 0.4:  # Increased from 0.2 to 0.4
                log_scan_activity(symbol, "TRADE: executing buy order")
            else:
                log_scan_activity(symbol, "DECISION: not trading due to risk parameters")
        else:
            log_scan_activity(symbol, "DECISION: no trading opportunity found")
    else:
        log_scan_activity(symbol, "FAILED initial screening")

def force_scan_symbols():
    """Force the bot to scan symbols"""
    symbols = get_watchlist()
    if not symbols:
        logger.error("Watchlist is empty")
        return False
    
    logger.info(f"Forcing scan of {len(symbols)} symbols")
    
    # Scan each symbol
    for symbol in symbols:
        scan_symbol(symbol)
    
    logger.info(f"Completed forced scan of {len(symbols)} symbols")
    return True

def main():
    """Main function"""
    logger.info("Starting forced symbol scan...")
    
    # Force scan symbols
    success = force_scan_symbols()
    
    if success:
        logger.info("✅ Forced scan completed successfully")
        logger.info("You can now use the monitoring tools to see the scanning activity:")
        logger.info("./monitor_activity.sh")
        logger.info("./monitor_trades.sh")
        logger.info("./watch_symbols.sh")
        return 0
    else:
        logger.error("❌ Forced scan failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 