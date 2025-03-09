import os
import time
import logging
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
from dotenv import load_dotenv
from functools import wraps

from brokers.base_broker import BaseBroker

# Configure logging
logger = logging.getLogger(__name__)

def retry_on_exception(retries=3, delay=5):
    """Decorator for retrying operations that may fail"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == retries:
                        logger.error(f"Failed after {retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempts} failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
        return wrapper
    return decorator

class MetaTraderBroker(BaseBroker):
    """
    MetaTrader broker implementation for forex trading.
    This implementation uses a REST API bridge to communicate with MetaTrader.
    """
    
    def __init__(self):
        """Initialize the MetaTrader broker"""
        load_dotenv()
        self.api_url = os.getenv('MT_API_URL', 'http://localhost:5000')
        self.api_key = os.getenv('MT_API_KEY', '')
        self.account_number = os.getenv('MT_ACCOUNT_NUMBER', '')
        self.connected = False
        self.timezone = pytz.timezone('UTC')  # MetaTrader uses UTC
        
        # Forex market hours (24/5)
        self.market_open_weekday = 0  # Monday
        self.market_close_weekday = 4  # Friday
        self.market_open_hour = 22  # Sunday 22:00 UTC
        self.market_close_hour = 22  # Friday 22:00 UTC
    
    def connect(self) -> bool:
        """Connect to MetaTrader API"""
        try:
            # Test connection by getting account info
            response = self._make_request('GET', '/connect', {
                'account': self.account_number
            })
            
            if response.get('connected', False):
                self.connected = True
                logger.info(f"Connected to MetaTrader API. Account: {self.account_number}")
                return True
            else:
                logger.error(f"Failed to connect to MetaTrader API: {response.get('message', 'Unknown error')}")
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MetaTrader API: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from MetaTrader API"""
        try:
            response = self._make_request('GET', '/disconnect', {
                'account': self.account_number
            })
            
            self.connected = False
            logger.info("Disconnected from MetaTrader API")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from MetaTrader API: {e}")
            self.connected = False
            return False
    
    @retry_on_exception(retries=3, delay=5)
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return {}
        
        try:
            response = self._make_request('GET', '/account', {
                'account': self.account_number
            })
            
            if 'error' in response:
                logger.error(f"Error getting account info: {response['error']}")
                return {}
            
            return {
                'equity': float(response.get('equity', 0)),
                'balance': float(response.get('balance', 0)),
                'margin': float(response.get('margin', 0)),
                'free_margin': float(response.get('free_margin', 0)),
                'margin_level': float(response.get('margin_level', 0)),
                'leverage': float(response.get('leverage', 1)),
                'currency': response.get('currency', 'USD')
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return {}
        
        try:
            response = self._make_request('GET', '/positions', {
                'account': self.account_number
            })
            
            if 'error' in response:
                logger.error(f"Error getting positions: {response['error']}")
                return {}
            
            positions = response.get('positions', [])
            positions_dict = {}
            
            for position in positions:
                symbol = position.get('symbol', '')
                positions_dict[symbol] = {
                    'ticket': position.get('ticket', 0),
                    'symbol': symbol,
                    'type': position.get('type', ''),  # 0=buy, 1=sell
                    'lots': float(position.get('volume', 0)),
                    'open_price': float(position.get('open_price', 0)),
                    'open_time': position.get('open_time', ''),
                    'sl': float(position.get('sl', 0)),
                    'tp': float(position.get('tp', 0)),
                    'profit': float(position.get('profit', 0)),
                    'swap': float(position.get('swap', 0)),
                    'comment': position.get('comment', '')
                }
            
            return positions_dict
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def place_order(self, symbol: str, qty: float, side: str, order_type: str, 
                   time_in_force: str = 'GTC', limit_price: float = None, 
                   stop_price: float = None) -> Dict[str, Any]:
        """Place an order"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return {}
        
        try:
            # Convert side to MT order type
            mt_order_type = 0  # OP_BUY
            if side.lower() == 'sell':
                mt_order_type = 1  # OP_SELL
            
            # Convert order_type to MT order type
            if order_type.lower() == 'limit':
                if side.lower() == 'buy':
                    mt_order_type = 2  # OP_BUYLIMIT
                else:
                    mt_order_type = 3  # OP_SELLLIMIT
            elif order_type.lower() == 'stop':
                if side.lower() == 'buy':
                    mt_order_type = 4  # OP_BUYSTOP
                else:
                    mt_order_type = 5  # OP_SELLSTOP
            
            # Prepare request data
            request_data = {
                'account': self.account_number,
                'symbol': symbol,
                'volume': qty,  # In lots
                'type': mt_order_type,
                'price': limit_price if limit_price else 0,
                'slippage': 3,  # Default slippage
                'stoploss': stop_price if stop_price else 0,
                'takeprofit': 0,  # No take profit by default
                'comment': 'KryptoBot'
            }
            
            response = self._make_request('POST', '/order', request_data)
            
            if 'error' in response:
                logger.error(f"Error placing order for {symbol}: {response['error']}")
                return {}
            
            return {
                'id': str(response.get('ticket', 0)),
                'symbol': symbol,
                'qty': qty,
                'side': side,
                'type': order_type,
                'time_in_force': time_in_force,
                'limit_price': limit_price,
                'stop_price': stop_price,
                'status': 'open',
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return False
        
        try:
            response = self._make_request('DELETE', '/order', {
                'account': self.account_number,
                'ticket': int(order_id)
            })
            
            if 'error' in response:
                logger.error(f"Error cancelling order {order_id}: {response['error']}")
                return False
            
            logger.info(f"Order {order_id} cancelled successfully")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    @retry_on_exception(retries=3, delay=5)
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order information by ID"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return {}
        
        try:
            response = self._make_request('GET', '/order', {
                'account': self.account_number,
                'ticket': int(order_id)
            })
            
            if 'error' in response:
                logger.error(f"Error getting order {order_id}: {response['error']}")
                return {}
            
            order = response.get('order', {})
            
            # Convert MT order type to side and order_type
            mt_order_type = order.get('type', 0)
            side = 'buy'
            order_type = 'market'
            
            if mt_order_type == 1:  # OP_SELL
                side = 'sell'
            elif mt_order_type == 2:  # OP_BUYLIMIT
                side = 'buy'
                order_type = 'limit'
            elif mt_order_type == 3:  # OP_SELLLIMIT
                side = 'sell'
                order_type = 'limit'
            elif mt_order_type == 4:  # OP_BUYSTOP
                side = 'buy'
                order_type = 'stop'
            elif mt_order_type == 5:  # OP_SELLSTOP
                side = 'sell'
                order_type = 'stop'
            
            return {
                'id': str(order.get('ticket', 0)),
                'symbol': order.get('symbol', ''),
                'qty': float(order.get('volume', 0)),
                'side': side,
                'type': order_type,
                'time_in_force': 'GTC',  # MetaTrader default
                'limit_price': float(order.get('open_price', 0)),
                'stop_price': float(order.get('stoploss', 0)),
                'status': order.get('status', 'unknown'),
                'created_at': order.get('open_time', ''),
                'filled_qty': float(order.get('volume', 0)) if order.get('status') == 'filled' else 0,
                'filled_avg_price': float(order.get('close_price', 0)) if order.get('status') == 'filled' else 0
            }
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def get_orders(self, status: str = 'open') -> List[Dict[str, Any]]:
        """Get all orders with the specified status"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return []
        
        try:
            endpoint = '/orders'
            if status.lower() == 'closed':
                endpoint = '/history_orders'
            
            response = self._make_request('GET', endpoint, {
                'account': self.account_number
            })
            
            if 'error' in response:
                logger.error(f"Error getting {status} orders: {response['error']}")
                return []
            
            orders = response.get('orders', [])
            orders_list = []
            
            for order in orders:
                # Convert MT order type to side and order_type
                mt_order_type = order.get('type', 0)
                side = 'buy'
                order_type = 'market'
                
                if mt_order_type == 1:  # OP_SELL
                    side = 'sell'
                elif mt_order_type == 2:  # OP_BUYLIMIT
                    side = 'buy'
                    order_type = 'limit'
                elif mt_order_type == 3:  # OP_SELLLIMIT
                    side = 'sell'
                    order_type = 'limit'
                elif mt_order_type == 4:  # OP_BUYSTOP
                    side = 'buy'
                    order_type = 'stop'
                elif mt_order_type == 5:  # OP_SELLSTOP
                    side = 'sell'
                    order_type = 'stop'
                
                orders_list.append({
                    'id': str(order.get('ticket', 0)),
                    'symbol': order.get('symbol', ''),
                    'qty': float(order.get('volume', 0)),
                    'side': side,
                    'type': order_type,
                    'time_in_force': 'GTC',  # MetaTrader default
                    'limit_price': float(order.get('open_price', 0)),
                    'stop_price': float(order.get('stoploss', 0)),
                    'status': order.get('status', 'unknown'),
                    'created_at': order.get('open_time', '')
                })
            
            return orders_list
        except Exception as e:
            logger.error(f"Error getting {status} orders: {e}")
            return []
    
    @retry_on_exception(retries=3, delay=5)
    def get_market_data(self, symbol: str, timeframe: str = '15Min', 
                       limit: int = 100) -> Optional[pd.DataFrame]:
        """Get market data for a symbol"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return None
        
        try:
            # Convert timeframe to MT format
            mt_timeframe = self._convert_timeframe(timeframe)
            
            response = self._make_request('GET', '/rates', {
                'account': self.account_number,
                'symbol': symbol,
                'timeframe': mt_timeframe,
                'count': limit
            })
            
            if 'error' in response:
                logger.error(f"Error getting market data for {symbol}: {response['error']}")
                return None
            
            rates = response.get('rates', [])
            
            if len(rates) == 0:
                logger.warning(f"No data returned for {symbol} with timeframe {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            
            # Rename columns to match expected format
            df.rename(columns={
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            }, inplace=True)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    @retry_on_exception(retries=3, delay=5)
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get the current price of a symbol"""
        if not self.connected:
            logger.warning("Not connected to MetaTrader API")
            return None
        
        try:
            response = self._make_request('GET', '/tick', {
                'account': self.account_number,
                'symbol': symbol
            })
            
            if 'error' in response:
                logger.error(f"Error getting current price for {symbol}: {response['error']}")
                return None
            
            tick = response.get('tick', {})
            
            # Return the bid price (for selling) and ask price (for buying)
            bid = float(tick.get('bid', 0))
            ask = float(tick.get('ask', 0))
            
            # Return the average of bid and ask
            return (bid + ask) / 2
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def check_market_hours(self) -> bool:
        """Check if the market is currently open"""
        # Forex market is open 24/5
        now = datetime.now(self.timezone)
        weekday = now.weekday()
        
        # Check if current day is between Monday and Friday
        if weekday < self.market_open_weekday or weekday > self.market_close_weekday:
            return False
        
        # If it's Friday, check if it's before market close
        if weekday == self.market_close_weekday:
            return now.hour < self.market_close_hour
        
        # If it's Monday, check if it's after market open
        if weekday == self.market_open_weekday:
            return now.hour >= 0  # Market is open all day Monday
        
        # For other weekdays, market is open 24 hours
        return True
    
    def get_next_market_times(self) -> tuple:
        """Get the next market open and close times"""
        now = datetime.now(self.timezone)
        weekday = now.weekday()
        
        # Calculate next market open time
        if weekday >= self.market_close_weekday and now.hour >= self.market_close_hour:
            # If it's Friday after market close or weekend, next open is Monday
            days_to_monday = (7 - weekday + self.market_open_weekday) % 7
            next_open_date = now.date() + timedelta(days=days_to_monday)
            next_open = datetime.combine(next_open_date, datetime.min.time()).replace(tzinfo=self.timezone)
        else:
            # Market is currently open or will open today
            next_open = now
        
        # Calculate next market close time
        if weekday < self.market_close_weekday:
            # If it's before Friday, next close is Friday
            days_to_friday = self.market_close_weekday - weekday
            next_close_date = now.date() + timedelta(days=days_to_friday)
        elif weekday == self.market_close_weekday and now.hour < self.market_close_hour:
            # If it's Friday before market close, next close is today
            next_close_date = now.date()
        else:
            # If it's Friday after market close or weekend, next close is next Friday
            days_to_next_friday = (7 - weekday + self.market_close_weekday) % 7
            next_close_date = now.date() + timedelta(days=days_to_next_friday)
        
        next_close = datetime.combine(
            next_close_date, 
            datetime.min.time().replace(hour=self.market_close_hour)
        ).replace(tzinfo=self.timezone)
        
        return (next_open, next_close)
    
    def get_platform_name(self) -> str:
        """Get the name of the trading platform"""
        return "MetaTrader"
    
    def get_platform_type(self) -> str:
        """Get the type of the trading platform"""
        return "forex"
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the MetaTrader API bridge"""
        url = f"{self.api_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=params, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, json=params, headers=headers, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return {'error': f"Unsupported HTTP method: {method}"}
            
            if response.status_code != 200:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return {'error': f"API request failed with status code {response.status_code}: {response.text}"}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {'error': f"Request error: {e}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {'error': f"JSON decode error: {e}"}
    
    def _convert_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to MetaTrader timeframe value"""
        # Parse the timeframe (e.g., '15Min', '1H', '1D')
        number = int(''.join(filter(str.isdigit, timeframe)))
        unit = ''.join(filter(str.isalpha, timeframe)).lower()
        
        # Convert to MetaTrader timeframe
        if unit in ['min', 'm']:
            if number == 1:
                return 1  # PERIOD_M1
            elif number == 5:
                return 5  # PERIOD_M5
            elif number == 15:
                return 15  # PERIOD_M15
            elif number == 30:
                return 30  # PERIOD_M30
            else:
                logger.warning(f"Unsupported minute timeframe: {timeframe}. Using M15 instead.")
                return 15  # Default to M15
        elif unit in ['hour', 'h']:
            if number == 1:
                return 60  # PERIOD_H1
            elif number == 4:
                return 240  # PERIOD_H4
            else:
                logger.warning(f"Unsupported hour timeframe: {timeframe}. Using H1 instead.")
                return 60  # Default to H1
        elif unit in ['day', 'd']:
            return 1440  # PERIOD_D1
        elif unit in ['week', 'w']:
            return 10080  # PERIOD_W1
        elif unit in ['month', 'mo']:
            return 43200  # PERIOD_MN1
        else:
            logger.warning(f"Unsupported timeframe unit: {timeframe}. Using H1 instead.")
            return 60  # Default to H1 