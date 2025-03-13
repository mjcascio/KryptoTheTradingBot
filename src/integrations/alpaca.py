#!/usr/bin/env python3
"""
Alpaca Integration Module

This module handles integration with the Alpaca trading platform.
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Union
import requests
import yfinance as yf
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

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
    
    def __init__(self, api_key: str, api_secret: str, paper_trading: bool = True):
        """Initialize Alpaca integration
        
        Args:
            api_key (str): Alpaca API key
            api_secret (str): Alpaca API secret
            paper_trading (bool): Whether to use paper trading (default: True)
            
        Raises:
            ValueError: If API credentials are not found
        """
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        }
        
        # Set base URLs
        if paper_trading:
            self.base_url = 'https://paper-api.alpaca.markets'
        else:
            self.base_url = 'https://api.alpaca.markets'
        
        # Data API URL is different from trading API
        self.data_url = 'https://data.alpaca.markets'
        
        # Initialize trading client
        self.api = TradingClient(api_key, api_secret, paper=paper_trading)
        
        self.logger.info(f"Alpaca integration initialized (Paper Trading: {paper_trading})")

    def get_positions(self, suppress_notifications: bool = True) -> List[Dict]:
        """Get current positions.
        
        Args:
            suppress_notifications (bool): Whether to suppress position update notifications
            
        Returns:
            List of position dictionaries
        """
        try:
            positions = self.api.get_all_positions()
            
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
            
            return positions_list
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """Place a market order.
        
        Args:
            symbol (str): Trading symbol
            side (str): 'buy' or 'sell'
            quantity (float): Number of shares
            
        Returns:
            Order details if successful, None otherwise
        """
        try:
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.api.submit_order(order_request)
            logger.info(f"Market order placed: {symbol} {side.upper()} {quantity} shares")
            
            return {
                'id': order.id,
                'symbol': order.symbol,
                'side': order.side.value,
                'quantity': float(order.qty),
                'status': order.status.value
            }
            
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id (str): Order ID to cancel
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.api.cancel_order(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    def get_account_info(self) -> Optional[Dict]:
        """Get account information.
        
        Returns:
            Account details if successful, None otherwise
        """
        try:
            account = self.api.get_account()
            return {
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'initial_margin': float(account.initial_margin),
                'maintenance_margin': float(account.maintenance_margin),
                'last_equity': float(account.last_equity),
                'status': account.status.value
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_option_chain(self, symbol: str) -> List[Dict]:
        """Get option chain for a symbol
        
        Args:
            symbol (str): The trading symbol
            
        Returns:
            List of option contracts
        """
        try:
            # First try Alpaca
            try:
                # Get current date
                today = datetime.now().date()
                
                # Get expiration dates (next 4 monthly expirations)
                expirations = []
                current_date = today
                count = 0
                while count < 4:
                    # Move to next month
                    if current_date.month == 12:
                        next_month = datetime(current_date.year + 1, 1, 1).date()
                    else:
                        next_month = datetime(current_date.year, current_date.month + 1, 1).date()
                    
                    # Find third Friday
                    third_friday = next_month
                    while third_friday.weekday() != 4:  # 4 is Friday
                        third_friday = third_friday + timedelta(days=1)
                    third_friday = third_friday + timedelta(days=14)
                    
                    if third_friday > today:
                        expirations.append(third_friday.strftime('%Y-%m-%d'))
                        count += 1
                    current_date = next_month
                
                # Get option chain for each expiration
                all_options = []
                for expiration in expirations:
                    url = f"{self.data_url}/v2/stocks/options/{symbol}"
                    params = {
                        'expiration': expiration
                    }
                    
                    response = requests.get(url, headers=self.headers, params=params)
                    
                    # Handle 404 error specifically for options data access
                    if response.status_code == 404:
                        raise Exception("Options data not available through Alpaca")
                    
                    response.raise_for_status()
                    data = response.json()
                    options = data.get('options', [])
                    
                    # Format each option contract
                    for option in options:
                        formatted_option = {
                            'symbol': option['symbol'],
                            'expiry': option['expiration_date'],
                            'strike': float(option['strike_price']),
                            'option_type': 'call' if option['type'] == 'c' else 'put',
                            'last_price': float(option['last_price']) if option.get('last_price') else None,
                            'bid': float(option['bid']) if option.get('bid') else None,
                            'ask': float(option['ask']) if option.get('ask') else None,
                            'volume': int(option['volume']) if option.get('volume') else 0,
                            'open_interest': int(option['open_interest']) if option.get('open_interest') else 0,
                            'implied_volatility': float(option['implied_volatility']) if option.get('implied_volatility') else None,
                            'delta': float(option['greeks']['delta']) if option.get('greeks', {}).get('delta') else None,
                            'gamma': float(option['greeks']['gamma']) if option.get('greeks', {}).get('gamma') else None,
                            'theta': float(option['greeks']['theta']) if option.get('greeks', {}).get('theta') else None,
                            'vega': float(option['greeks']['vega']) if option.get('greeks', {}).get('vega') else None
                        }
                        all_options.append(formatted_option)
                
                return all_options
                
            except Exception as e:
                self.logger.warning(f"Alpaca options data not available: {str(e)}")
                self.logger.info("Falling back to Yahoo Finance for options data")
                
                # Use Yahoo Finance as fallback
                ticker = yf.Ticker(symbol)
                options = ticker.option_chain()
                
                all_options = []
                
                # Process calls
                for _, row in options.calls.iterrows():
                    option = {
                        'symbol': f"{symbol}_{row['expiration'].strftime('%Y-%m-%d')}_C{row['strike']}",
                        'expiry': row['expiration'].strftime('%Y-%m-%d'),
                        'strike': float(row['strike']),
                        'option_type': 'call',
                        'last_price': float(row['lastPrice']) if row['lastPrice'] > 0 else None,
                        'bid': float(row['bid']) if row['bid'] > 0 else None,
                        'ask': float(row['ask']) if row['ask'] > 0 else None,
                        'volume': int(row['volume']) if row['volume'] > 0 else 0,
                        'open_interest': int(row['openInterest']) if row['openInterest'] > 0 else 0,
                        'implied_volatility': float(row['impliedVolatility']) if row['impliedVolatility'] > 0 else None,
                        'delta': float(row['delta']) if 'delta' in row and row['delta'] > 0 else None,
                        'gamma': float(row['gamma']) if 'gamma' in row and row['gamma'] > 0 else None,
                        'theta': float(row['theta']) if 'theta' in row and row['theta'] > 0 else None,
                        'vega': float(row['vega']) if 'vega' in row and row['vega'] > 0 else None
                    }
                    all_options.append(option)
                
                # Process puts
                for _, row in options.puts.iterrows():
                    option = {
                        'symbol': f"{symbol}_{row['expiration'].strftime('%Y-%m-%d')}_P{row['strike']}",
                        'expiry': row['expiration'].strftime('%Y-%m-%d'),
                        'strike': float(row['strike']),
                        'option_type': 'put',
                        'last_price': float(row['lastPrice']) if row['lastPrice'] > 0 else None,
                        'bid': float(row['bid']) if row['bid'] > 0 else None,
                        'ask': float(row['ask']) if row['ask'] > 0 else None,
                        'volume': int(row['volume']) if row['volume'] > 0 else 0,
                        'open_interest': int(row['openInterest']) if row['openInterest'] > 0 else 0,
                        'implied_volatility': float(row['impliedVolatility']) if row['impliedVolatility'] > 0 else None,
                        'delta': float(row['delta']) if 'delta' in row and row['delta'] > 0 else None,
                        'gamma': float(row['gamma']) if 'gamma' in row and row['gamma'] > 0 else None,
                        'theta': float(row['theta']) if 'theta' in row and row['theta'] > 0 else None,
                        'vega': float(row['vega']) if 'vega' in row and row['vega'] > 0 else None
                    }
                    all_options.append(option)
                
                return all_options
                
        except Exception as e:
            self.logger.error(f"Error getting option chain for {symbol}: {str(e)}")
            return []

    def place_option_order(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        expiry: str,
        side: str,
        quantity: int,
        order_type: str = 'market',
        time_in_force: str = 'day',
        limit_price: Optional[float] = None
    ) -> Optional[Dict]:
        """Place an option order.
        
        Args:
            symbol (str): The underlying symbol
            option_type (str): 'call' or 'put'
            strike (float): Strike price
            expiry (str): Expiration date in ISO format
            side (str): 'buy' or 'sell'
            quantity (int): Number of contracts
            order_type (str): 'market' or 'limit'
            time_in_force (str): Time in force ('day', 'gtc', 'ioc', 'fok')
            limit_price (float, optional): Limit price for limit orders
            
        Returns:
            Order details if successful, None otherwise
        """
        try:
            # Construct the option symbol
            option_symbol = f"{symbol}{expiry.replace('-', '')}{'C' if option_type.lower() == 'call' else 'P'}{int(strike*1000):08d}"
            
            # Prepare order data
            order_data = {
                'symbol': option_symbol,
                'qty': quantity,
                'side': side.lower(),
                'type': order_type.lower(),
                'time_in_force': time_in_force.lower(),
                'order_class': 'simple'
            }
            
            if order_type.lower() == 'limit' and limit_price is not None:
                order_data['limit_price'] = limit_price
            
            # Place order via REST API
            url = f"{self.base_url}/v2/options/orders"
            response = requests.post(url, headers=self.headers, json=order_data)
            response.raise_for_status()
            
            order = response.json()
            
            logger.info(
                f"Option order placed: {quantity} {symbol} {option_type.upper()} "
                f"${strike} {expiry} {side.upper()}"
            )
            
            return {
                'id': order['id'],
                'symbol': order['symbol'],
                'option_type': option_type,
                'strike': strike,
                'expiry': expiry,
                'side': order['side'],
                'quantity': quantity,
                'status': order['status'],
                'filled_qty': float(order.get('filled_qty', 0)),
                'filled_avg_price': float(order.get('filled_avg_price', 0))
            }
            
        except Exception as e:
            logger.error(f"Error placing option order: {e}")
            return None

    def get_option_positions(self) -> List[Dict]:
        """Get all option positions.
        
        Returns:
            List of option position dictionaries
        """
        try:
            # Get positions via REST API
            url = f"{self.base_url}/v2/options/positions"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            positions = response.json()
            
            # Process and format the positions
            option_positions = []
            for position in positions:
                pos_dict = {
                    'symbol': position['symbol'],
                    'option_type': 'call' if position['option_type'] == 'call' else 'put',
                    'strike': float(position['strike_price']),
                    'expiry': position['expiration_date'],
                    'quantity': abs(float(position['qty'])),
                    'side': 'long' if float(position['qty']) > 0 else 'short',
                    'avg_entry_price': float(position['avg_entry_price']),
                    'current_price': float(position['current_price']),
                    'unrealized_pl': float(position['unrealized_pl']),
                    'unrealized_plpc': float(position['unrealized_plpc']),
                    'market_value': float(position['market_value'])
                }
                option_positions.append(pos_dict)
            
            return option_positions
            
        except Exception as e:
            logger.error(f"Error getting option positions: {e}")
            return []

    def get_option_position(self, symbol: str, option_type: str, strike: float, expiry: str) -> Optional[Dict]:
        """Get specific option position details.
        
        Args:
            symbol (str): The underlying symbol
            option_type (str): 'call' or 'put'
            strike (float): Strike price
            expiry (str): Expiration date in ISO format
            
        Returns:
            Position details if found, None otherwise
        """
        try:
            # Construct the option symbol
            option_symbol = f"{symbol}{expiry.replace('-', '')}{'C' if option_type.lower() == 'call' else 'P'}{int(strike*1000):08d}"
            
            # Get position via REST API
            url = f"{self.base_url}/v2/options/positions/{option_symbol}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            position = response.json()
            
            return {
                'symbol': position['symbol'],
                'option_type': 'call' if position['option_type'] == 'call' else 'put',
                'strike': float(position['strike_price']),
                'expiry': position['expiration_date'],
                'quantity': abs(float(position['qty'])),
                'side': 'long' if float(position['qty']) > 0 else 'short',
                'avg_entry_price': float(position['avg_entry_price']),
                'current_price': float(position['current_price']),
                'unrealized_pl': float(position['unrealized_pl']),
                'unrealized_plpc': float(position['unrealized_plpc']),
                'market_value': float(position['market_value'])
            }
            
        except Exception as e:
            logger.error(f"Error getting option position: {e}")
            return None

    def get_bars(
        self,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        timeframe: str = '1D'
    ) -> List[Dict]:
        """
        Get historical price bars for a symbol.
        
        Args:
            symbol (str): The trading symbol
            start_dt (datetime): Start date for historical data
            end_dt (datetime): End date for historical data
            timeframe (str): Timeframe for the bars (e.g., '1D', '1H', '5Min')
            
        Returns:
            List[Dict]: List of price bars with timestamp and OHLCV data
        """
        try:
            # Ensure end date is not in the future
            current_time = datetime.now()
            if end_dt > current_time:
                end_dt = current_time
            
            # Ensure start date is not after end date
            if start_dt > end_dt:
                start_dt = end_dt - timedelta(days=30)  # Default to last 30 days
            
            timeframe_map = {
                '1D': '1day',
                '1H': '1hour',
                '5Min': '5min',
                '1Min': '1min'
            }
            api_timeframe = timeframe_map.get(timeframe, '1day')
            
            # Format dates as ISO 8601 strings
            start_str = start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_str = end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Use data_url instead of base_url for market data
            url = f"{self.data_url}/v2/stocks/{symbol}/bars"
            params = {
                'start': start_str,
                'end': end_str,
                'timeframe': api_timeframe,
                'adjustment': 'raw'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            bars = data.get('bars', [])
            
            formatted_bars = []
            for bar in bars:
                formatted_bars.append({
                    'timestamp': bar['t'],
                    'open': float(bar['o']),
                    'high': float(bar['h']),
                    'low': float(bar['l']),
                    'close': float(bar['c']),
                    'volume': int(bar['v'])
                })
            
            return formatted_bars
            
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {str(e)}")
            return [] 