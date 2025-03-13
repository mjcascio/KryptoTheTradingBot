#!/usr/bin/env python3
"""
Run Daily Summary

This script sets the Telegram environment variables directly and runs the daily summary.
"""

import os
import sys
import subprocess

def run_daily_summary():
    """Set environment variables and run daily summary"""
    
    # Set environment variables
    os.environ['TELEGRAM_BOT_TOKEN'] = "8078241360:AAE3KoFYSUhV7uKSDaTBuWuCWtTRHkw4dyk"
    os.environ['TELEGRAM_CHAT_ID'] = "7924393886"
    
    # Print environment variables
    print(f"TELEGRAM_BOT_TOKEN: {os.environ.get('TELEGRAM_BOT_TOKEN')}")
    print(f"TELEGRAM_CHAT_ID: {os.environ.get('TELEGRAM_CHAT_ID')}")
    
    # Run daily summary
    print("\nRunning daily summary...")
    subprocess.run([sys.executable, "daily_summary.py", "--now"])

if __name__ == "__main__":
    run_daily_summary() 