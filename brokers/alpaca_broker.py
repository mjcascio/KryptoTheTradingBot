import os
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import certifi
from dotenv import load_dotenv
from functools import wraps
from ratelimit import limits, sleep_and_retry

# Import Alpaca SDK
try:
    import alpaca_trade_api as tradeapi
    from alpaca_trade_api.rest import REST
    from alpaca_trade_api.stream import Stream
    ALPACA_SDK_AVAILABLE = True
except ImportError:
    ALPACA_SDK_AVAILABLE = False
    logging.warning("Alpaca SDK not available. Install with: pip install alpaca-trade-api")

from brokers.base_broker import BaseBroker
from config import MARKET_OPEN, MARKET_CLOSE, TIMEZONE

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set SSL certificate path
ssl_cert_file = os.getenv('SSL_CERT_FILE', certifi.where())
requests_ca_bundle = os.getenv('REQUESTS_CA_BUNDLE', certifi.where())
os.environ['SSL_CERT_FILE'] = ssl_cert_file
os.environ['REQUESTS_CA_BUNDLE'] = requests_ca_bundle
logger.info(f"SSL_CERT_FILE set to: {os.environ.get('SSL_CERT_FILE', 'Not set')}")
logger.info(f"REQUESTS_CA_BUNDLE set to: {os.environ.get('REQUESTS_CA_BUNDLE', 'Not set')}")

# Configure rate limiting
CALLS_PER_SECOND = 5  # Alpaca's rate limit is 200 per minute
PERIOD = 1  # 1 second

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

@sleep_and_retry
@limits(calls=CALLS_PER_SECOND, period=PERIOD)
def rate_limited_api_call(func, *args, **kwargs):
    """Rate limit API calls to avoid hitting limits"""
    return func(*args, **kwargs)

class AlpacaBroker(BaseBroker):
    """
    Broker implementation for Alpaca Markets.
    """
    
    def __init__(self):
        """Initialize the Alpaca broker."""
        super().__init__()
        self.name = "Alpaca"
        self.api = None
        self.stream = None
        self.connected = False
        self.account_info = {}
        self.timezone = pytz.timezone(TIMEZONE)
        
        # Set SSL certificate path
        ssl_cert_file = os.getenv('SSL_CERT_FILE', certifi.where())
        requests_ca_bundle = os.getenv('REQUESTS_CA_BUNDLE', certifi.where())
        os.environ['SSL_CERT_FILE'] = ssl_cert_file
        os.environ['REQUESTS_CA_BUNDLE'] = requests_ca_bundle
        
        # Load environment variables
        load_dotenv()
    
    def connect(self) -> bool:
        """
        Connect to Alpaca API.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        if not ALPACA_SDK_AVAILABLE:
            logger.error("Cannot connect to Alpaca: SDK not available")
            return False
        
        try:
            # Get API credentials from environment variables
            api_key = os.getenv('ALPACA_API_KEY')
            base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
            endpoint_key = os.getenv('ALPACA_ENDPOINT_KEY', base_url + '/v2')
            
            # Check if API key is available
            if not api_key:
                logger.error("Alpaca API key not found in environment variables")
                return False
            
            logger.info(f"Connecting to Alpaca with API key: {api_key[:4]}...{api_key[-4:]}")
            logger.info(f"Using base URL: {base_url}")
            logger.info(f"Using endpoint key: {endpoint_key}")
            
            # Initialize REST API client
            self.api = REST(
                key_id=api_key,
                base_url=base_url,
                api_version='v2'
            )
            
            # Test connection by getting account info
            self.account_info = self.api.get_account()
            logger.info(f"Connected to Alpaca: Account ID {self.account_info.id}")
            logger.info(f"Account status: {self.account_info.status}")
            logger.info(f"Account equity: ${self.account_info.equity}")
            logger.info(f"Account cash: ${self.account_info.cash}")
            
            # Initialize stream for real-time data
            try:
                stream_url = base_url.replace('https://', 'wss://').replace('api', 'stream')
                self.stream = Stream(
                    key_id=api_key,
                    base_url=stream_url
                )
                logger.info(f"Initialized streaming connection to: {stream_url}")
            except Exception as e:
                logger.warning(f"Could not initialize streaming connection: {e}")
                logger.warning("Continuing without streaming data")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Alpaca: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Alpaca API"""
        # Alpaca REST API doesn't require explicit disconnection
        self.connected = False
        logger.info("Disconnected from Alpaca API")
        return True
    
    @retry_on_exception(retries=3, delay=5)
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return {}
        
        try:
            account = rate_limited_api_call(self.api.get_account)
            return {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'initial_margin': float(account.initial_margin),
                'regt_buying_power': float(account.regt_buying_power),
                'daytrading_buying_power': float(account.daytrading_buying_power),
                'maintenance_margin': float(account.maintenance_margin),
                'last_equity': float(account.last_equity),
                'status': account.status
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return {}
        
        try:
            positions = rate_limited_api_call(self.api.list_positions)
            positions_dict = {}
            
            for position in positions:
                positions_dict[position.symbol] = {
                    'qty': float(position.qty),
                    'avg_entry_price': float(position.avg_entry_price),
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'current_price': float(position.current_price),
                    'lastday_price': float(position.lastday_price),
                    'change_today': float(position.change_today)
                }
            
            return positions_dict
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def place_order(self, symbol: str, qty: float, side: str, order_type: str, 
                   time_in_force: str = 'day', limit_price: float = None, 
                   stop_price: float = None) -> Dict[str, Any]:
        """Place an order"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return {}
        
        try:
            order = rate_limited_api_call(
                self.api.submit_order,
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price
            )
            
            return {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'status': order.status,
                'created_at': order.created_at,
                'updated_at': order.updated_at
            }
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return False
        
        try:
            rate_limited_api_call(self.api.cancel_order, order_id)
            logger.info(f"Order {order_id} cancelled successfully")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    @retry_on_exception(retries=3, delay=5)
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order information by ID"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return {}
        
        try:
            order = rate_limited_api_call(self.api.get_order, order_id)
            
            return {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'status': order.status,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'filled_at': order.filled_at,
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0
            }
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return {}
    
    @retry_on_exception(retries=3, delay=5)
    def get_orders(self, status: str = 'open') -> List[Dict[str, Any]]:
        """Get all orders with the specified status"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return []
        
        try:
            if status == 'open':
                orders = rate_limited_api_call(self.api.list_orders, status='open')
            else:
                orders = rate_limited_api_call(self.api.list_orders, status='closed')
            
            orders_list = []
            for order in orders:
                orders_list.append({
                    'id': order.id,
                    'client_order_id': order.client_order_id,
                    'symbol': order.symbol,
                    'qty': float(order.qty),
                    'side': order.side,
                    'type': order.type,
                    'time_in_force': order.time_in_force,
                    'limit_price': float(order.limit_price) if order.limit_price else None,
                    'stop_price': float(order.stop_price) if order.stop_price else None,
                    'status': order.status,
                    'created_at': order.created_at,
                    'updated_at': order.updated_at
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
            logger.warning("Not connected to Alpaca API")
            return None
        
        try:
            # Calculate start and end times based on limit and timeframe
            end = datetime.now(self.timezone)
            
            # Parse the timeframe (e.g., '15Min', '1D')
            number = int(''.join(filter(str.isdigit, timeframe)))
            unit = ''.join(filter(str.isalpha, timeframe)).lower()
            
            if unit == 'min':
                delta = timedelta(minutes=number * limit)
            elif unit == 'hour':
                delta = timedelta(hours=number * limit)
            elif unit == 'day':
                delta = timedelta(days=number * limit)
            else:
                delta = timedelta(days=limit)
            
            start = end - delta
            
            bars = rate_limited_api_call(
                self.api.get_bars,
                symbol,
                timeframe,
                start=start.isoformat(),
                end=end.isoformat(),
                adjustment='raw'
            )
            
            if len(bars) == 0:
                logger.warning(f"No data returned for {symbol} with timeframe {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': bar.t,
                    'open': bar.o,
                    'high': bar.h,
                    'low': bar.l,
                    'close': bar.c,
                    'volume': bar.v
                }
                for bar in bars
            ])
            
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
            logger.warning("Not connected to Alpaca API")
            return None
        
        try:
            last_trade = rate_limited_api_call(self.api.get_latest_trade, symbol)
            return float(last_trade.price)
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            
            # Try to get the last bar instead
            try:
                bars = rate_limited_api_call(
                    self.api.get_bars,
                    symbol,
                    '1Min',
                    limit=1
                )
                if len(bars) > 0:
                    return float(bars[0].c)
                return None
            except Exception as e2:
                logger.error(f"Error getting last bar for {symbol}: {e2}")
                return None
    
    def check_market_hours(self) -> bool:
        """Check if the market is currently open"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return False
        
        try:
            clock = rate_limited_api_call(self.api.get_clock)
            return clock.is_open
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            
            # Fallback to manual check
            now = datetime.now(self.timezone)
            market_open_time = datetime.strptime(MARKET_OPEN, "%H:%M").time()
            market_close_time = datetime.strptime(MARKET_CLOSE, "%H:%M").time()
            
            # Check if current time is within market hours
            current_time = now.time()
            is_market_day = now.weekday() < 5  # Monday to Friday
            
            return (
                is_market_day and
                market_open_time <= current_time <= market_close_time
            )
    
    def get_next_market_times(self) -> tuple:
        """Get the next market open and close times"""
        if not self.connected:
            logger.warning("Not connected to Alpaca API")
            return (None, None)
        
        try:
            calendar = rate_limited_api_call(self.api.get_calendar)
            
            # Find the next market day
            now = datetime.now(self.timezone)
            next_open = None
            next_close = None
            
            for day in calendar:
                day_date = datetime.fromisoformat(day.date).replace(tzinfo=self.timezone)
                
                # Parse open and close times
                open_time = datetime.fromisoformat(day.open).replace(tzinfo=self.timezone)
                close_time = datetime.fromisoformat(day.close).replace(tzinfo=self.timezone)
                
                if open_time > now and next_open is None:
                    next_open = open_time
                    next_close = close_time
                    break
            
            return (next_open, next_close)
        except Exception as e:
            logger.error(f"Error getting next market times: {e}")
            
            # Fallback to manual calculation
            now = datetime.now(self.timezone)
            
            # Calculate the next market day (skip weekends)
            days_ahead = 1
            if now.weekday() == 4:  # Friday
                days_ahead = 3  # Next Monday
            elif now.weekday() == 5:  # Saturday
                days_ahead = 2  # Next Monday
            
            next_day = now + timedelta(days=days_ahead)
            
            # Set market open and close times
            market_open_time = datetime.strptime(MARKET_OPEN, "%H:%M").time()
            market_close_time = datetime.strptime(MARKET_CLOSE, "%H:%M").time()
            
            next_open = datetime.combine(next_day.date(), market_open_time).replace(tzinfo=self.timezone)
            next_close = datetime.combine(next_day.date(), market_close_time).replace(tzinfo=self.timezone)
            
            return (next_open, next_close)
    
    def get_platform_name(self) -> str:
        """Get the name of the trading platform"""
        return "Alpaca"
    
    def get_platform_type(self) -> str:
        """Get the type of the trading platform"""
        return "stocks" 