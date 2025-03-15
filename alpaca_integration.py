#!/usr/bin/env python3
"""
Alpaca Integration Module

This module handles integration with the Alpaca trading platform.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from trade_hooks import on_position_updated

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AlpacaIntegration:
    """Class for integrating with Alpaca trading platform"""
    
    def __init__(self):
        """Initialize Alpaca integration"""
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not found in environment variables")
            
        self.paper_trading = True  # Always using paper trading for safety
        self.api = TradingClient(self.api_key, self.api_secret, paper=self.paper_trading)
        logger.info("Alpaca integration initialized in paper trading mode")

    def get_account_info(self):
        """Get account information
        
        Returns:
            dict: Account information including equity and buying power
        """
        try:
            account = self.api.get_account()
            return {
                'equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value)
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {
                'equity': 0.0,
                'buying_power': 0.0,
                'cash': 0.0,
                'portfolio_value': 0.0
            }

@staticmethod
def update_positions():
    """
    Update positions and log changes without sending notifications
    
    Returns:
        List of positions or empty list if error
    """
    try:
        positions = AlpacaIntegration.get_positions()
        
        for position in positions:
            symbol = position['symbol']
            side = position['side']
            quantity = float(position['qty'])
            entry_price = float(position['avg_entry_price'])
            current_price = float(position['current_price'])
            unrealized_profit = float(position['unrealized_pl'])
            
            # Only log the update at debug level, don't send notification
            logger.debug(f"Position status: {symbol} {side.upper()} {quantity} @ {entry_price:.2f}, Current: {current_price:.2f}, P/L: {unrealized_profit:.2f}")
        
        return positions
            
    except Exception as e:
        logger.error(f"Error updating positions: {e}")
        return []

def get_positions(self, suppress_notifications=True):
    """Get current positions.
    
    Args:
        suppress_notifications (bool): Whether to suppress position update notifications
        
    Returns:
        List of positions
    """
    try:
        positions = self.api.list_positions()
        
        # Convert to list of dictionaries
        positions_list = []
        for position in positions:
            position_dict = {
                'symbol': position.symbol,
                'side': 'long' if float(position.qty) > 0 else 'short',
                'qty': abs(float(position.qty)),
                'avg_entry_price': float(position.avg_entry_price),
                'current_price': float(position.current_price),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc),
                'market_value': float(position.market_value)
            }
            positions_list.append(position_dict)
            
            # Only log position updates, don't send notifications during regular updates
            if not suppress_notifications:
                logger.info(f"Position update for {position.symbol}: {position_dict}")
                
                # Call position update hook with notification suppression
                on_position_updated(
                    symbol=position.symbol,
                    side=position_dict['side'],
                    quantity=position_dict['qty'],
                    entry_price=position_dict['avg_entry_price'],
                    current_price=position_dict['current_price'],
                    unrealized_profit=position_dict['unrealized_pl'],
                    suppress_notifications=suppress_notifications
                )
        
        return positions_list
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return [] 