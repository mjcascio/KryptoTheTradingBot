#!/usr/bin/env python3
"""
Options Trading Module for KryptoBot

This module provides functionality for trading options through the Alpaca API.
It includes methods for fetching option chains, placing option orders,
and managing option positions.

Note: As of April 2024, Alpaca supports options trading in paper environment,
with live trading coming soon.
"""

import os
import logging
import json
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Import Alpaca modules
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest, LimitOrderRequest, 
        OptionOrderRequest, OptionPositionCloseRequest
    )
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderType, PositionSide
    from alpaca.data.historical import OptionHistoricalDataClient
    from alpaca.data.requests import OptionSnapshotRequest, OptionChainRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.common.exceptions import APIError
except ImportError:
    logging.error("Alpaca modules not found. Please install with: pip install alpaca-py")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/options_trading.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OptionsTrading:
    """
    Class for options trading functionality using Alpaca API.
    """
    
    def __init__(self, paper=True):
        """
        Initialize the OptionsTrading class.
        
        Args:
            paper (bool): Whether to use paper trading (default: True)
        """
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        self.paper = paper
        
        # Initialize trading client
        self.trading_client = TradingClient(self.api_key, self.api_secret, paper=self.paper)
        
        # Initialize data client for options
        self.data_client = OptionHistoricalDataClient(self.api_key, self.api_secret)
        
        # Check if options trading is enabled
        self._check_options_enabled()
        
        logger.info(f"Options Trading initialized (Paper: {paper})")
    
    def _check_options_enabled(self):
        """
        Check if options trading is enabled for the account.
        
        Raises:
            ValueError: If options trading is not enabled
        """
        account = self.trading_client.get_account()
        
        # Check if options trading is enabled
        if not hasattr(account, 'option_level') or not account.option_level:
            logger.warning("Options trading may not be enabled for this account")
        else:
            logger.info(f"Options trading level: {account.option_level}")
    
    def get_option_chain(self, symbol, expiration_date=None, option_type=None, strike_price=None):
        """
        Get option chain for a symbol.
        
        Args:
            symbol (str): The underlying symbol (e.g., 'SPY')
            expiration_date (str, optional): Expiration date in format 'YYYY-MM-DD'
            option_type (str, optional): 'call' or 'put'
            strike_price (float, optional): Strike price filter
            
        Returns:
            dict: Option chain data
        """
        try:
            # Create request parameters
            request_params = {
                "underlying_symbols": symbol
            }
            
            # Add optional filters
            if expiration_date:
                # Convert to datetime if string
                if isinstance(expiration_date, str):
                    expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                request_params["expiration_date"] = expiration_date
            
            if option_type:
                request_params["option_type"] = option_type.lower()
            
            if strike_price:
                request_params["strike_price"] = float(strike_price)
            
            # Create request object
            request = OptionChainRequest(**request_params)
            
            # Get option chain
            option_chain = self.data_client.get_option_chain(request)
            
            logger.info(f"Retrieved option chain for {symbol}")
            return option_chain
        
        except Exception as e:
            logger.error(f"Error getting option chain for {symbol}: {e}")
            raise
    
    def get_option_snapshot(self, option_symbol):
        """
        Get snapshot data for a specific option contract.
        
        Args:
            option_symbol (str): The option symbol (e.g., 'SPY230616C00420000')
            
        Returns:
            dict: Option snapshot data
        """
        try:
            request = OptionSnapshotRequest(symbols=option_symbol)
            snapshot = self.data_client.get_option_snapshot(request)
            
            logger.info(f"Retrieved snapshot for option {option_symbol}")
            return snapshot
        
        except Exception as e:
            logger.error(f"Error getting option snapshot for {option_symbol}: {e}")
            raise
    
    def place_option_order(self, option_symbol, qty, side, order_type="market", 
                          limit_price=None, time_in_force="day"):
        """
        Place an option order.
        
        Args:
            option_symbol (str): The option symbol (e.g., 'SPY230616C00420000')
            qty (int): Quantity of contracts
            side (str): 'buy' or 'sell'
            order_type (str, optional): 'market' or 'limit'
            limit_price (float, optional): Limit price (required for limit orders)
            time_in_force (str, optional): Time in force ('day', 'gtc', 'ioc', 'opg')
            
        Returns:
            dict: Order information
        """
        try:
            # Validate side
            if side.lower() not in ['buy', 'sell']:
                raise ValueError("Side must be 'buy' or 'sell'")
            
            # Validate order type
            if order_type.lower() not in ['market', 'limit']:
                raise ValueError("Order type must be 'market' or 'limit'")
            
            # Validate time in force
            if time_in_force.lower() not in ['day', 'gtc', 'ioc', 'opg']:
                raise ValueError("Time in force must be 'day', 'gtc', 'ioc', or 'opg'")
            
            # Create order data
            order_data = {
                "symbol": option_symbol,
                "qty": str(qty),
                "side": side.lower(),
                "time_in_force": time_in_force.lower()
            }
            
            # Create appropriate order request based on type
            if order_type.lower() == 'market':
                order_request = MarketOrderRequest(**order_data)
            else:  # limit order
                if limit_price is None:
                    raise ValueError("Limit price is required for limit orders")
                
                order_data["limit_price"] = float(limit_price)
                order_request = LimitOrderRequest(**order_data)
            
            # Submit order
            order = self.trading_client.submit_order(order_data=order_request)
            
            logger.info(f"Placed {order_type} {side} order for {qty} {option_symbol} contracts")
            return order
        
        except Exception as e:
            logger.error(f"Error placing option order for {option_symbol}: {e}")
            raise
    
    def place_multi_leg_option_order(self, legs, qty, order_type="market", 
                                    limit_price=None, time_in_force="day"):
        """
        Place a multi-leg option order (e.g., spreads, straddles, etc.).
        
        Args:
            legs (list): List of dictionaries with leg details:
                         [{"symbol": "SPY230616C00420000", "side": "buy", "ratio": 1}, ...]
            qty (int): Quantity of the strategy (multiplied by ratio for each leg)
            order_type (str, optional): 'market' or 'limit'
            limit_price (float, optional): Net limit price for the entire strategy
            time_in_force (str, optional): Time in force ('day', 'gtc', 'ioc', 'opg')
            
        Returns:
            dict: Order information
        """
        try:
            # Validate legs
            if not legs or not isinstance(legs, list):
                raise ValueError("Legs must be a non-empty list")
            
            # Prepare legs for the order
            order_legs = []
            for leg in legs:
                if not all(k in leg for k in ["symbol", "side", "ratio"]):
                    raise ValueError("Each leg must contain 'symbol', 'side', and 'ratio'")
                
                # Determine position intent based on side
                position_intent = "buy_to_open" if leg["side"].lower() == "buy" else "sell_to_open"
                
                order_legs.append({
                    "symbol": leg["symbol"],
                    "side": leg["side"].lower(),
                    "position_intent": position_intent,
                    "ratio_qty": str(leg["ratio"])
                })
            
            # Create order data
            order_data = {
                "order_class": "mleg",
                "legs": order_legs,
                "qty": str(qty),
                "type": order_type.lower(),
                "time_in_force": time_in_force.lower()
            }
            
            # Add limit price if applicable
            if order_type.lower() == "limit":
                if limit_price is None:
                    raise ValueError("Limit price is required for limit orders")
                order_data["limit_price"] = float(limit_price)
            
            # Submit order
            order = self.trading_client.submit_order(order_data=order_data)
            
            logger.info(f"Placed multi-leg option order with {len(legs)} legs, qty: {qty}")
            return order
        
        except Exception as e:
            logger.error(f"Error placing multi-leg option order: {e}")
            raise
    
    def close_option_position(self, option_symbol, qty=None):
        """
        Close an option position.
        
        Args:
            option_symbol (str): The option symbol (e.g., 'SPY230616C00420000')
            qty (int, optional): Quantity to close (if None, closes entire position)
            
        Returns:
            dict: Order information
        """
        try:
            # Get current position
            position = self.trading_client.get_position(option_symbol)
            
            # Determine side for closing
            side = "sell" if position.side == "long" else "buy"
            
            # Determine quantity
            if qty is None:
                qty = abs(float(position.qty))
            
            # Place order to close position
            return self.place_option_order(
                option_symbol=option_symbol,
                qty=qty,
                side=side,
                order_type="market",
                time_in_force="day"
            )
        
        except Exception as e:
            logger.error(f"Error closing option position for {option_symbol}: {e}")
            raise
    
    def get_option_positions(self):
        """
        Get all current option positions.
        
        Returns:
            list: List of option positions
        """
        try:
            positions = self.trading_client.get_all_positions()
            
            # Filter for option positions
            option_positions = [p for p in positions if self._is_option_symbol(p.symbol)]
            
            logger.info(f"Retrieved {len(option_positions)} option positions")
            return option_positions
        
        except Exception as e:
            logger.error(f"Error getting option positions: {e}")
            raise
    
    def _is_option_symbol(self, symbol):
        """
        Check if a symbol is an option symbol.
        
        Args:
            symbol (str): Symbol to check
            
        Returns:
            bool: True if it's an option symbol, False otherwise
        """
        # Option symbols typically have format like SPY230616C00420000
        # This is a simple heuristic check
        if len(symbol) > 15 and ('C' in symbol or 'P' in symbol):
            return True
        return False
    
    def get_option_orders(self, status="open"):
        """
        Get option orders.
        
        Args:
            status (str, optional): Order status ('open', 'closed', 'all')
            
        Returns:
            list: List of option orders
        """
        try:
            orders = self.trading_client.get_orders(status=status)
            
            # Filter for option orders
            option_orders = [o for o in orders if self._is_option_symbol(o.symbol)]
            
            logger.info(f"Retrieved {len(option_orders)} {status} option orders")
            return option_orders
        
        except Exception as e:
            logger.error(f"Error getting option orders: {e}")
            raise
    
    def calculate_option_greeks(self, option_snapshot):
        """
        Extract option Greeks from a snapshot.
        
        Args:
            option_snapshot (dict): Option snapshot data
            
        Returns:
            dict: Option Greeks (delta, gamma, theta, vega, rho)
        """
        try:
            greeks = {
                'delta': option_snapshot.get('delta', None),
                'gamma': option_snapshot.get('gamma', None),
                'theta': option_snapshot.get('theta', None),
                'vega': option_snapshot.get('vega', None),
                'rho': option_snapshot.get('rho', None),
                'implied_volatility': option_snapshot.get('implied_volatility', None)
            }
            
            return greeks
        
        except Exception as e:
            logger.error(f"Error calculating option Greeks: {e}")
            return {}
    
    def find_options_by_criteria(self, symbol, criteria):
        """
        Find options that match specific criteria.
        
        Args:
            symbol (str): The underlying symbol (e.g., 'SPY')
            criteria (dict): Criteria for filtering options, e.g.,
                            {'max_dte': 30, 'min_delta': 0.3, 'max_delta': 0.7}
            
        Returns:
            list: List of option contracts matching the criteria
        """
        try:
            # Get expiration dates within DTE range
            max_dte = criteria.get('max_dte', 45)
            min_dte = criteria.get('min_dte', 0)
            
            today = datetime.now().date()
            max_date = today + timedelta(days=max_dte)
            min_date = today + timedelta(days=min_dte)
            
            # Get option chain
            option_chain = self.get_option_chain(symbol)
            
            # Filter options based on criteria
            matching_options = []
            
            for option in option_chain:
                # Extract expiration date
                expiration = datetime.strptime(option.expiration_date, '%Y-%m-%d').date()
                
                # Check DTE
                if not (min_date <= expiration <= max_date):
                    continue
                
                # Get snapshot for Greeks
                snapshot = self.get_option_snapshot(option.symbol)
                greeks = self.calculate_option_greeks(snapshot)
                
                # Check delta criteria
                min_delta = criteria.get('min_delta', 0)
                max_delta = criteria.get('max_delta', 1)
                
                if greeks.get('delta') is None:
                    continue
                
                delta = abs(greeks['delta'])  # Use absolute value for puts
                
                if not (min_delta <= delta <= max_delta):
                    continue
                
                # Check other criteria as needed
                # ...
                
                # Add to matching options
                matching_options.append({
                    'symbol': option.symbol,
                    'expiration': option.expiration_date,
                    'strike': option.strike_price,
                    'option_type': option.option_type,
                    'delta': greeks.get('delta'),
                    'gamma': greeks.get('gamma'),
                    'theta': greeks.get('theta'),
                    'vega': greeks.get('vega'),
                    'implied_volatility': greeks.get('implied_volatility')
                })
            
            logger.info(f"Found {len(matching_options)} options matching criteria for {symbol}")
            return matching_options
        
        except Exception as e:
            logger.error(f"Error finding options by criteria for {symbol}: {e}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize options trading
    options = OptionsTrading(paper=True)
    
    # Get option chain for SPY
    chain = options.get_option_chain("SPY")
    
    # Print first few options
    for i, option in enumerate(chain[:5]):
        print(f"Option {i+1}: {option.symbol}, Strike: {option.strike_price}, Type: {option.option_type}")
    
    print("\nOptions Trading module loaded successfully!") 