#!/usr/bin/env python3
"""
Execute Trade Script for KryptoBot

This script allows you to execute real trades with Alpaca directly.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import importlib
import time
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("execute_trade")

def load_alpaca_api():
    """Load Alpaca API from environment variables"""
    load_dotenv()
    
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY', 'dummy_secret_key_not_used')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    
    if not api_key:
        logger.error("ALPACA_API_KEY not found in environment variables")
        return None
    
    try:
        api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        return api
    except Exception as e:
        logger.error(f"Error initializing Alpaca API: {e}")
        return None

def get_account_info(api):
    """Get account information from Alpaca"""
    try:
        account = api.get_account()
        logger.info(f"Account ID: {account.id}")
        logger.info(f"Account Status: {account.status}")
        logger.info(f"Buying Power: ${float(account.buying_power):.2f}")
        logger.info(f"Cash: ${float(account.cash):.2f}")
        logger.info(f"Portfolio Value: ${float(account.portfolio_value):.2f}")
        return account
    except Exception as e:
        logger.error(f"Error getting account information: {e}")
        return None

def execute_trade(api, symbol, qty, side, order_type='market', time_in_force='day'):
    """Execute a trade with Alpaca"""
    try:
        logger.info(f"Executing {side} order for {qty} shares of {symbol}")
        
        # Submit the order
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force
        )
        
        logger.info(f"Order placed successfully: {order.id}")
        logger.info(f"Order Status: {order.status}")
        
        # Wait for order to be filled
        if order_type == 'market':
            logger.info("Waiting for order to be filled...")
            for _ in range(10):  # Try for 10 seconds
                time.sleep(1)
                updated_order = api.get_order(order.id)
                if updated_order.status == 'filled':
                    logger.info(f"Order filled at ${float(updated_order.filled_avg_price):.2f}")
                    break
            else:
                logger.warning("Order not filled within timeout period. Check Alpaca dashboard for status.")
        
        return order
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Execute a trade with Alpaca')
    parser.add_argument('symbol', help='Stock symbol (e.g., AAPL)')
    parser.add_argument('side', choices=['buy', 'sell'], help='Trade side (buy or sell)')
    parser.add_argument('quantity', type=float, help='Number of shares to trade')
    parser.add_argument('--type', choices=['market', 'limit'], default='market', help='Order type (default: market)')
    parser.add_argument('--price', type=float, help='Limit price (required for limit orders)')
    parser.add_argument('--time-in-force', choices=['day', 'gtc', 'ioc'], default='day', help='Time in force (default: day)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.type == 'limit' and args.price is None:
        logger.error("Limit price is required for limit orders")
        return 1
    
    # Load Alpaca API
    api = load_alpaca_api()
    if not api:
        return 1
    
    # Get account information
    account = get_account_info(api)
    if not account:
        return 1
    
    # Execute trade
    order = execute_trade(api, args.symbol, args.quantity, args.side, args.type, args.time_in_force)
    if not order:
        return 1
    
    logger.info("✅ Trade executed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 