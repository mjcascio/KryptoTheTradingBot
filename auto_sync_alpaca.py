#!/usr/bin/env python3
"""
Auto Sync Alpaca

This script automatically synchronizes local data with Alpaca at regular intervals.
It can be run as a background service to keep data in sync.
"""

import os
import sys
import time
import logging
import argparse
import schedule
from datetime import datetime
from sync_alpaca_data import main as sync_data
from alpaca_integration import AlpacaIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alpaca_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def sync_and_update():
    """Sync data and update positions"""
    try:
        # Log start
        logger.info("Starting Alpaca data synchronization...")
        
        # Sync data
        sync_data()
        
        # Initialize Alpaca integration
        alpaca = AlpacaIntegration()
        
        # Update positions without sending notifications
        positions = alpaca.get_positions(suppress_notifications=True)
        
        # Only log position status at debug level
        for position in positions:
            symbol = position['symbol']
            side = position['side']
            quantity = float(position['qty'])
            entry_price = float(position['avg_entry_price'])
            current_price = float(position['current_price'])
            unrealized_profit = float(position['unrealized_pl'])
            
            # Log at debug level only
            logger.debug(f"Position status: {symbol} {side.upper()} {quantity} @ {entry_price:.2f}, Current: {current_price:.2f}, P/L: {unrealized_profit:.2f}")
        
        # Log completion
        logger.info("Alpaca data synchronization completed")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in sync_and_update: {e}")
        return False

def run_scheduler(interval=15):
    """
    Run the scheduler to sync data at regular intervals
    
    Args:
        interval: Sync interval in minutes
    """
    # Schedule sync job
    schedule.every(interval).minutes.do(sync_and_update)
    
    # Also sync at market open and close
    schedule.every().day.at("09:30").do(sync_and_update)  # Market open
    schedule.every().day.at("16:00").do(sync_and_update)  # Market close
    
    # Initial sync
    sync_and_update()
    
    # Run scheduler
    logger.info(f"Scheduler started. Syncing every {interval} minutes.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Auto sync local data with Alpaca")
    parser.add_argument("--interval", type=int, default=30, help="Sync interval in minutes")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    if args.once:
        # Run once
        return 0 if sync_and_update() else 1
    else:
        # Run scheduler
        run_scheduler(args.interval)
        return 0

if __name__ == "__main__":
    sys.exit(main()) 