#!/usr/bin/env python3
"""
Test Log Writer

This script continuously writes to the log file for testing real-time monitoring.
"""

import os
import sys
import time
from datetime import datetime
import random

# Log file path
LOG_FILE = "logs/trading_bot.out"

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

def write_log_entry(message, color=NC):
    """Write a log entry to the log file and print with color."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - trading.bot - INFO - {message}"
    
    # Write to file (without color)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")
        f.flush()
        os.fsync(f.fileno())  # Force OS to write to disk
    
    # Print to terminal (with color)
    print(f"{color}Wrote: {message}{NC}")

def main():
    """Main function."""
    print(f"Writing test log entries to {LOG_FILE}")
    print("Press Ctrl+C to stop")
    print("\nColor Legend:")
    print(f"{RED}Failed Scans{NC}")
    print(f"{GREEN}Passed Scans{NC}")
    print(f"{YELLOW}Signals{NC}")
    print(f"{PURPLE}Trades{NC}")
    print(f"{BLUE}Decisions{NC}")
    print(f"{CYAN}Checking Steps{NC}\n")
    
    count = 0
    try:
        while True:
            count += 1
            symbol = random.choice(["AAPL", "MSFT", "GOOGL", "AMZN", "META"])
            
            # Write a sequence of related log entries
            write_log_entry(f"SCAN: starting analysis {symbol}")
            time.sleep(0.2)
            
            write_log_entry(f"SCAN: checking volume parameters {symbol}", CYAN)
            time.sleep(0.2)
            
            write_log_entry(f"SCAN: checking price movement {symbol}", CYAN)
            time.sleep(0.2)
            
            # Randomly pass or fail
            if random.random() > 0.5:
                write_log_entry(f"SCAN: PASSED initial screening {symbol}", GREEN)
                time.sleep(0.2)
                
                write_log_entry(f"SCAN: performing detailed analysis {symbol}", CYAN)
                time.sleep(0.2)
                
                if random.random() > 0.7:
                    write_log_entry(f"SCAN: SIGNAL: potential trading opportunity detected {symbol}", YELLOW)
                    time.sleep(0.2)
                    
                    if random.random() > 0.5:
                        side = random.choice(["buy", "sell"])
                        write_log_entry(f"SCAN: TRADE: executing {side} order {symbol}", PURPLE)
                    else:
                        write_log_entry(f"SCAN: DECISION: not trading due to risk parameters {symbol}", BLUE)
                else:
                    write_log_entry(f"SCAN: DECISION: no trading opportunity found {symbol}", BLUE)
            else:
                write_log_entry(f"SCAN: FAILED initial screening {symbol}", RED)
            
            # Pause between symbols
            time.sleep(1)
            
            # Print status every 5 symbols
            if count % 5 == 0:
                print(f"\n{CYAN}Wrote {count} symbol scans{NC}\n")
                
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopped by user{NC}")

if __name__ == "__main__":
    main() 