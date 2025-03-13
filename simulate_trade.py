#!/usr/bin/env python3
"""
Simulate Trade Execution

This script simulates a trade execution and sends a notification via Telegram.
It also updates the trade history file with the simulated trade.
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
from datetime import datetime
from telegram_notifications import send_trade_notification, TELEGRAM_ENABLED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_trade(symbol, side, quantity, price, strategy=None, profit=None):
    """
    Simulate a trade execution and send a notification
    
    Args:
        symbol: Trading symbol
        side: Trade side ('buy' or 'sell')
        quantity: Trade quantity
        price: Trade price
        strategy: Trading strategy
        profit: Profit/loss amount (for sell trades)
    
    Returns:
        Boolean indicating success
    """
    try:
        # Create trade data
        trade_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": price,
            "exit_price": price + (profit / quantity if profit else 0),
            "profit": profit if profit else 0,
            "strategy": strategy if strategy else "manual"
        }
        
        # Update trade history
        trade_history_file = "data/trade_history.json"
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Load existing trade history
        if os.path.exists(trade_history_file):
            with open(trade_history_file, "r") as f:
                trade_history = json.load(f)
        else:
            trade_history = []
        
        # Add new trade
        trade_history.append(trade_data)
        
        # Save updated trade history
        with open(trade_history_file, "w") as f:
            json.dump(trade_history, f, indent=4)
        
        logger.info(f"Trade simulated: {side.upper()} {quantity} {symbol} @ ${price:.2f}")
        
        # Send notification
        if TELEGRAM_ENABLED:
            success = send_trade_notification(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                strategy=strategy,
                profit=profit
            )
            
            if success:
                logger.info("Trade notification sent successfully")
            else:
                logger.error("Failed to send trade notification")
                
            return success
        else:
            logger.warning("Telegram notifications are not enabled")
            return False
            
    except Exception as e:
        logger.error(f"Error simulating trade: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Simulate a trade execution and send a notification")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol (e.g., AAPL)")
    parser.add_argument("--side", type=str, required=True, choices=["buy", "sell"], help="Trade side (buy or sell)")
    parser.add_argument("--quantity", type=float, required=True, help="Trade quantity")
    parser.add_argument("--price", type=float, required=True, help="Trade price")
    parser.add_argument("--strategy", type=str, help="Trading strategy")
    parser.add_argument("--profit", type=float, help="Profit/loss amount (for sell trades)")
    
    args = parser.parse_args()
    
    # Check if Telegram is enabled
    if not TELEGRAM_ENABLED:
        logger.warning("Telegram notifications are not enabled. The trade will be simulated but no notification will be sent.")
        print("Warning: Telegram notifications are not enabled. The trade will be simulated but no notification will be sent.")
    
    # Simulate trade
    success = simulate_trade(
        symbol=args.symbol,
        side=args.side,
        quantity=args.quantity,
        price=args.price,
        strategy=args.strategy,
        profit=args.profit
    )
    
    if success:
        print(f"Trade simulated and notification sent: {args.side.upper()} {args.quantity} {args.symbol} @ ${args.price:.2f}")
        return 0
    else:
        print("Trade simulated but failed to send notification")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 