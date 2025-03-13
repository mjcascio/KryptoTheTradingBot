#!/usr/bin/env python3
"""
Alpaca Data Synchronization

This script synchronizes local trade history and position data with Alpaca.
It fetches orders and positions from Alpaca API and updates local files.
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Alpaca credentials
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL')

# Check if Alpaca is configured
if not all([ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL]):
    logger.error("Alpaca API credentials not configured. Please check your .env file.")
    sys.exit(1)

# Alpaca API headers
HEADERS = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

def get_alpaca_orders(days_back=30, status='all'):
    """
    Get orders from Alpaca API
    
    Args:
        days_back: Number of days to look back
        status: Order status ('open', 'closed', 'all')
        
    Returns:
        List of orders
    """
    try:
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Get orders from Alpaca
        response = requests.get(
            f'{ALPACA_BASE_URL}/v2/orders',
            headers=HEADERS,
            params={
                'status': status,
                'limit': 500,
                'after': start_date
            }
        )
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting orders from Alpaca: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting orders from Alpaca: {e}")
        return []

def get_alpaca_positions():
    """
    Get positions from Alpaca API
    
    Returns:
        List of positions
    """
    try:
        # Get positions from Alpaca
        response = requests.get(
            f'{ALPACA_BASE_URL}/v2/positions',
            headers=HEADERS
        )
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting positions from Alpaca: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting positions from Alpaca: {e}")
        return []

def update_trade_history(orders):
    """
    Update local trade history with Alpaca orders
    
    Args:
        orders: List of orders from Alpaca API
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize trade history
        trade_history = []
        
        # Process filled orders
        for order in orders:
            # Skip orders that aren't filled
            if order['status'] != 'filled':
                continue
                
            # Get order details
            symbol = order['symbol']
            side = order['side']
            quantity = float(order['qty'])
            filled_price = float(order['filled_avg_price']) if order['filled_avg_price'] else 0
            
            # Calculate profit for sell orders
            profit = 0
            if side == 'sell' and order.get('position_intent') == 'sell_to_close':
                # Try to find the corresponding buy order
                for buy_order in orders:
                    if (buy_order['status'] == 'filled' and 
                        buy_order['symbol'] == symbol and 
                        buy_order['side'] == 'buy' and
                        buy_order.get('position_intent') == 'buy_to_open'):
                        
                        buy_price = float(buy_order['filled_avg_price']) if buy_order['filled_avg_price'] else 0
                        profit = (filled_price - buy_price) * quantity
                        break
            
            # Create trade entry
            trade_entry = {
                "timestamp": order['filled_at'].replace('Z', ''),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": filled_price,
                "exit_price": filled_price,  # For buy orders, entry and exit are the same
                "profit": profit,
                "strategy": order.get('subtag', 'unknown')
            }
            
            # Add to trade history
            trade_history.append(trade_entry)
        
        # Sort trade history by timestamp
        trade_history.sort(key=lambda x: x['timestamp'])
        
        # Save trade history
        with open('data/trade_history.json', 'w') as f:
            json.dump(trade_history, f, indent=4)
            
        logger.info(f"Trade history updated with {len(trade_history)} trades from Alpaca")
        
    except Exception as e:
        logger.error(f"Error updating trade history: {e}")

def update_positions(positions):
    """
    Update local positions with Alpaca positions
    
    Args:
        positions: List of positions from Alpaca API
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize positions dictionary
        positions_dict = {}
        
        # Process positions
        for position in positions:
            # Get position details
            symbol = position['symbol']
            side = position['side']
            quantity = float(position['qty'])
            entry_price = float(position['avg_entry_price'])
            current_price = float(position['current_price'])
            unrealized_profit = float(position['unrealized_pl'])
            
            # Create position entry
            positions_dict[symbol] = {
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
                "current_price": current_price,
                "unrealized_profit": unrealized_profit,
                "strategy": "unknown"  # Alpaca doesn't store strategy information
            }
        
        # Save positions
        with open('data/positions.json', 'w') as f:
            json.dump(positions_dict, f, indent=4)
            
        logger.info(f"Positions updated with {len(positions_dict)} positions from Alpaca")
        
    except Exception as e:
        logger.error(f"Error updating positions: {e}")

def main():
    """Main function"""
    logger.info("Starting Alpaca data synchronization...")
    
    # Get orders from Alpaca
    logger.info("Fetching orders from Alpaca...")
    orders = get_alpaca_orders()
    
    # Get positions from Alpaca
    logger.info("Fetching positions from Alpaca...")
    positions = get_alpaca_positions()
    
    # Update trade history
    logger.info("Updating trade history...")
    update_trade_history(orders)
    
    # Update positions
    logger.info("Updating positions...")
    update_positions(positions)
    
    logger.info("Alpaca data synchronization completed")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 