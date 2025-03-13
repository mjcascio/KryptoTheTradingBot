#!/usr/bin/env python3
"""
Execute trades through Alpaca API.

This script allows you to execute trades directly through the Alpaca API.
It supports market, limit, stop, and stop-limit orders.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/alpaca_trades.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("alpaca_trade")

# Load environment variables
load_dotenv()

# Alpaca API credentials
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Check if credentials are available
if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    logger.error("Alpaca API credentials not found in .env file")
    sys.exit(1)

# Headers for Alpaca API requests
HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    "Content-Type": "application/json"
}

def place_order(symbol, side, quantity, order_type="market", limit_price=None, 
                stop_price=None, time_in_force="day", strategy=None):
    """
    Place an order through Alpaca API.
    
    Args:
        symbol (str): Stock symbol
        side (str): 'buy' or 'sell'
        quantity (float): Number of shares
        order_type (str): 'market', 'limit', 'stop', 'stop_limit'
        limit_price (float): Limit price for limit and stop-limit orders
        stop_price (float): Stop price for stop and stop-limit orders
        time_in_force (str): 'day', 'gtc', 'opg', 'cls', 'ioc', 'fok'
        strategy (str): Trading strategy used for this trade
        
    Returns:
        dict: Order details if successful, None otherwise
    """
    # Validate inputs
    if side not in ["buy", "sell"]:
        logger.error(f"Invalid side: {side}. Must be 'buy' or 'sell'")
        return None
        
    if order_type not in ["market", "limit", "stop", "stop_limit"]:
        logger.error(f"Invalid order type: {order_type}")
        return None
        
    if order_type in ["limit", "stop_limit"] and limit_price is None:
        logger.error(f"Limit price required for {order_type} orders")
        return None
        
    if order_type in ["stop", "stop_limit"] and stop_price is None:
        logger.error(f"Stop price required for {order_type} orders")
        return None
    
    # Prepare order data
    order_data = {
        "symbol": symbol,
        "qty": quantity,
        "side": side,
        "type": order_type,
        "time_in_force": time_in_force
    }
    
    # Add limit price if applicable
    if limit_price is not None and order_type in ["limit", "stop_limit"]:
        order_data["limit_price"] = str(limit_price)
    
    # Add stop price if applicable
    if stop_price is not None and order_type in ["stop", "stop_limit"]:
        order_data["stop_price"] = str(stop_price)
    
    # Add client order ID with strategy if provided
    if strategy:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        order_data["client_order_id"] = f"{strategy}_{timestamp}"
    
    # Send request to Alpaca API
    try:
        response = requests.post(
            f"{ALPACA_BASE_URL}/v2/orders",
            headers=HEADERS,
            data=json.dumps(order_data)
        )
        
        # Check if request was successful
        if response.status_code == 200 or response.status_code == 201:
            order = response.json()
            logger.info(f"Order placed successfully: {order['id']}")
            
            # Save order to trade history
            save_to_trade_history(order, strategy)
            
            return order
        else:
            logger.error(f"Failed to place order: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return None

def save_to_trade_history(order, strategy=None):
    """
    Save order to local trade history.
    
    Args:
        order (dict): Order details from Alpaca API
        strategy (str): Trading strategy used for this trade
    """
    try:
        # Create trade history file if it doesn't exist
        if not os.path.exists("data"):
            os.makedirs("data")
            
        trade_history_file = "data/trade_history.json"
        
        # Load existing trade history
        if os.path.exists(trade_history_file):
            with open(trade_history_file, "r") as f:
                trade_history = json.load(f)
        else:
            trade_history = []
        
        # Create new trade entry
        trade_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": order["symbol"],
            "side": order["side"],
            "quantity": float(order["qty"]),
            "order_type": order["type"],
            "order_id": order["id"],
            "status": order["status"]
        }
        
        # Add strategy if provided
        if strategy:
            trade_entry["strategy"] = strategy
            
        # Add prices if available
        if "limit_price" in order:
            trade_entry["limit_price"] = float(order["limit_price"])
            
        if "stop_price" in order:
            trade_entry["stop_price"] = float(order["stop_price"])
            
        if "filled_avg_price" in order and order["filled_avg_price"]:
            trade_entry["filled_price"] = float(order["filled_avg_price"])
        
        # Add trade to history
        trade_history.append(trade_entry)
        
        # Save updated trade history
        with open(trade_history_file, "w") as f:
            json.dump(trade_history, f, indent=2)
            
        logger.info(f"Trade saved to history: {order['symbol']} {order['side']}")
        
    except Exception as e:
        logger.error(f"Error saving trade to history: {str(e)}")

def main():
    """Main function to parse arguments and execute trades."""
    parser = argparse.ArgumentParser(description="Execute trades through Alpaca API")
    
    # Required arguments
    parser.add_argument("symbol", help="Stock symbol")
    parser.add_argument("side", choices=["buy", "sell"], help="Order side (buy or sell)")
    parser.add_argument("quantity", type=float, help="Number of shares")
    
    # Optional arguments
    parser.add_argument("--type", choices=["market", "limit", "stop", "stop_limit"], 
                        default="market", help="Order type")
    parser.add_argument("--limit-price", type=float, help="Limit price for limit and stop-limit orders")
    parser.add_argument("--stop-price", type=float, help="Stop price for stop and stop-limit orders")
    parser.add_argument("--time-in-force", choices=["day", "gtc", "opg", "cls", "ioc", "fok"], 
                        default="day", help="Time in force")
    parser.add_argument("--strategy", help="Trading strategy used for this trade")
    
    args = parser.parse_args()
    
    # Execute trade
    order = place_order(
        symbol=args.symbol,
        side=args.side,
        quantity=args.quantity,
        order_type=args.type,
        limit_price=args.limit_price,
        stop_price=args.stop_price,
        time_in_force=args.time_in_force,
        strategy=args.strategy
    )
    
    if order:
        print(json.dumps(order, indent=2))
        return 0
    else:
        return 1

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    sys.exit(main()) 