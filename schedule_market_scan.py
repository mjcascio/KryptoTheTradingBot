#!/usr/bin/env python3
"""
Schedule Market Scan

This script schedules the market scanner to run after hours and send a summary
at 8:00 AM the next morning.
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from market_scanner import MarketScanner
from telegram_notifications import send_telegram_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market_scan_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_market_scan():
    """Run the market scanner"""
    try:
        logger.info("Running after-hours market scan")
        
        # Create scanner
        scanner = MarketScanner()
        
        # Scan market
        potential_trades = scanner.scan_market()
        
        # Log results
        logger.info(f"Market scan completed. Found {len(potential_trades)} potential trades.")
        
        # Save results for morning summary
        return True
        
    except Exception as e:
        logger.error(f"Error running market scan: {e}")
        return False

def send_morning_summary():
    """Send morning summary to Telegram"""
    try:
        logger.info("Sending morning trade summary")
        
        # Get the latest scan results
        scanner = MarketScanner()
        
        # Find the latest scan results file
        scan_dir = "data/scanner"
        if not os.path.exists(scan_dir):
            logger.error(f"Scan directory {scan_dir} does not exist")
            return False
            
        files = [f for f in os.listdir(scan_dir) if f.startswith("scan_results_")]
        if not files:
            logger.error("No scan results found")
            return False
            
        # Sort by date (newest first)
        files.sort(reverse=True)
        latest_file = os.path.join(scan_dir, files[0])
        
        # Load results
        import json
        with open(latest_file, 'r') as f:
            scanner.potential_trades = json.load(f)
        
        # Send summary
        success = scanner.send_telegram_summary()
        
        if success:
            logger.info("Morning trade summary sent successfully")
        else:
            logger.error("Failed to send morning trade summary")
            
        return success
        
    except Exception as e:
        logger.error(f"Error sending morning summary: {e}")
        return False

def run_scheduler():
    """Run the scheduler"""
    try:
        logger.info("Starting market scan scheduler")
        
        # Schedule after-hours scan (4:30 PM Eastern Time)
        schedule.every().monday.at("16:30").do(run_market_scan)
        schedule.every().tuesday.at("16:30").do(run_market_scan)
        schedule.every().wednesday.at("16:30").do(run_market_scan)
        schedule.every().thursday.at("16:30").do(run_market_scan)
        schedule.every().friday.at("16:30").do(run_market_scan)
        
        # Schedule morning summary (8:00 AM Eastern Time)
        schedule.every().monday.at("08:00").do(send_morning_summary)
        schedule.every().tuesday.at("08:00").do(send_morning_summary)
        schedule.every().wednesday.at("08:00").do(send_morning_summary)
        schedule.every().thursday.at("08:00").do(send_morning_summary)
        schedule.every().friday.at("08:00").do(send_morning_summary)
        
        # Log next runs
        next_scan = schedule.next_run()
        logger.info(f"Next market scan scheduled for: {next_scan}")
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Handle command-line arguments
        if sys.argv[1] == "--scan-now":
            # Run market scan immediately
            return 0 if run_market_scan() else 1
        elif sys.argv[1] == "--summary-now":
            # Send summary immediately
            return 0 if send_morning_summary() else 1
        elif sys.argv[1] == "--help":
            print("Usage: python schedule_market_scan.py [OPTIONS]")
            print("Options:")
            print("  --scan-now      Run market scan immediately")
            print("  --summary-now   Send morning summary immediately")
            print("  --help          Show this help message")
            return 0
    else:
        # Run scheduler
        run_scheduler()
        return 0

if __name__ == "__main__":
    sys.exit(main()) 