#!/usr/bin/env python3
"""
Send Today's Summary

This script sends a summary of today's trading activity via Telegram.
"""

import os
import sys
import logging
from telegram_notifications import send_today_summary, TELEGRAM_ENABLED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Send today's summary via Telegram"""
    
    # Check if Telegram is enabled
    if not TELEGRAM_ENABLED:
        logger.error("Telegram notifications are not enabled. Please check your .env file.")
        print("Error: Telegram notifications are not enabled. Please check your .env file.")
        return 1
    
    print("Sending today's trading activity summary via Telegram...")
    
    # Send today's summary
    success = send_today_summary()
    
    if success:
        logger.info("Today's summary sent successfully!")
        print("Today's summary sent successfully!")
        return 0
    else:
        logger.error("Failed to send today's summary.")
        print("Error: Failed to send today's summary.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 