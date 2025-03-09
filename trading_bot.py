import os
import time
from datetime import datetime, timedelta
import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import threading
from strategies import TradingStrategy
from notifications import NotificationSystem
from dashboard import TradingDashboard, run_dashboard
from market_data import MarketDataService
from config import (
    WATCHLIST, FOREX_WATCHLIST, MAX_TRADES_PER_DAY, MIN_SUCCESS_PROBABILITY,
    MAX_POSITION_SIZE_PCT, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    MAX_DAILY_LOSS_PCT, MARKET_OPEN, MARKET_CLOSE, TIMEZONE, PLATFORMS
)
import pytz
from functools import wraps
from ratelimit import limits, sleep_and_retry
import yfinance as yf

# Import broker abstraction layer
from brokers import BrokerFactory, BaseBroker

# Constants
MAX_DAILY_LOSS_PCT = 0.05  # Maximum daily loss as percentage of capital
MAX_POSITION_SIZE_PCT = 0.02  # Maximum position size as percentage of equity
MIN_POSITION_SIZE = 1000  # Minimum position size in dollars
TIMEZONE = 'America/New_York'

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

class TradingBot:
    """Trading bot that implements various trading strategies"""
    
    def __init__(self, strategies=None, dashboard=None, notifications=None):
        """Initialize the trading bot"""
        # Create broker factory
        self.broker_factory = BrokerFactory()
        
        # Initialize brokers based on configuration
        self._initialize_brokers()
        
        # Set up strategies
        self.strategies = strategies or {}
        
        # Set up dashboard
        self.dashboard = dashboard or TradingDashboard()
        
        # Set up notifications
        self.notifications = notifications or NotificationSystem()
        
        # Initialize market data service with the active broker
        active_broker = self.broker_factory.get_active_broker()
        if active_broker:
            self.market_data = MarketDataService(active_broker)
        else:
            logger.error("No active broker available. Market data service not initialized.")
            self.market_data = None
        
        # Trading state
        self.is_running = False
        self.stop_event = threading.Event()
        self.trading_thread = None
        
        # Trading metrics
        self.daily_trades = 0
        self.daily_pl = 0.0
        self.positions = {}
        self.orders = {}
        
        # Load watchlist based on active platform
        self.watchlist = self._get_platform_watchlist()
        
        logger.info("Trading bot initialized")
    
    def _initialize_brokers(self):
        """Initialize brokers based on configuration"""
        default_broker = None
        
        # Create broker instances for enabled platforms
        for platform_id, platform_config in PLATFORMS.items():
            if platform_config.get('enabled', False):
                broker = self.broker_factory.create_broker(platform_id)
                if broker and platform_config.get('default', False):
                    default_broker = platform_id
        
        # Set the default broker as active
        if default_broker:
            self.broker_factory.set_active_broker(default_broker)
            logger.info(f"Set {default_broker} as the active broker")
        else:
            # If no default broker is specified, use the first enabled broker
            available_brokers = self.broker_factory.get_available_brokers()
            if available_brokers:
                self.broker_factory.set_active_broker(available_brokers[0])
                logger.info(f"No default broker specified. Using {available_brokers[0]} as the active broker")
            else:
                logger.error("No enabled brokers found in configuration")
    
    def _get_platform_watchlist(self) -> List[str]:
        """Get the watchlist for the active platform"""
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker:
            logger.warning("No active broker. Using default stock watchlist.")
            return WATCHLIST
        
        platform_type = active_broker.get_platform_type()
        
        if platform_type == 'forex':
            return FOREX_WATCHLIST
        else:
            return WATCHLIST
    
    def connect(self) -> bool:
        """Connect to all enabled brokers"""
        results = self.broker_factory.connect_all_brokers()
        
        # Check if the active broker is connected
        active_broker = self.broker_factory.get_active_broker()
        if active_broker and active_broker.connected:
            # Initialize market data service with the active broker
            self.market_data = MarketDataService(active_broker)
            
            # Update the watchlist based on the active platform
            self.watchlist = self._get_platform_watchlist()
            
            # Update dashboard with account info
            self._update_account_info()
            
            return True
        else:
            logger.error("Failed to connect to the active broker")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from all brokers"""
        return all(self.broker_factory.disconnect_all_brokers().values())
    
    def switch_platform(self, platform_id: str) -> bool:
        """Switch to a different trading platform"""
        if platform_id not in PLATFORMS:
            logger.error(f"Platform {platform_id} not found in configuration")
            return False
        
        if not PLATFORMS[platform_id].get('enabled', False):
            logger.error(f"Platform {platform_id} is not enabled in configuration")
            return False
        
        # Set the new platform as active
        if not self.broker_factory.set_active_broker(platform_id):
            logger.error(f"Failed to set {platform_id} as the active broker")
            return False
        
        # Connect to the broker if not already connected
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker.connected:
            if not active_broker.connect():
                logger.error(f"Failed to connect to {platform_id}")
                return False
        
        # Update market data service with the new broker
        self.market_data = MarketDataService(active_broker)
        
        # Update the watchlist based on the active platform
        self.watchlist = self._get_platform_watchlist()
        
        # Update dashboard with account info
        self._update_account_info()
        
        logger.info(f"Switched to platform: {platform_id}")
        return True
    
    def get_active_platform(self) -> str:
        """Get the ID of the active platform"""
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker:
            return ""
        
        for platform_id, platform_config in PLATFORMS.items():
            if platform_config.get('name', '') == active_broker.get_platform_name():
                return platform_id
        
        return ""
    
    def get_available_platforms(self) -> List[Dict[str, Any]]:
        """Get a list of available platforms"""
        platforms = []
        
        for platform_id, platform_config in PLATFORMS.items():
            if platform_config.get('enabled', False):
                platforms.append({
                    'id': platform_id,
                    'name': platform_config.get('name', platform_id),
                    'type': platform_config.get('type', 'unknown'),
                    'is_active': platform_id == self.get_active_platform()
                })
        
        return platforms
    
    def _update_account_info(self):
        """Update dashboard with account information"""
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker or not active_broker.connected:
            logger.warning("Cannot update account info: No active broker or not connected")
            return
        
        try:
            # Get account info from the broker
            account_info = active_broker.get_account_info()
            
            # Update dashboard with account info
            self.dashboard.update_account({
                'equity': account_info.get('equity', 0.0),
                'buying_power': account_info.get('buying_power', 0.0) or account_info.get('free_margin', 0.0),
                'cash': account_info.get('cash', 0.0) or account_info.get('balance', 0.0),
                'platform': active_broker.get_platform_name(),
                'platform_type': active_broker.get_platform_type()
            })
            
            # Update equity chart
            self.dashboard.update_equity(account_info.get('equity', 0.0))
            
            # Update positions
            positions = active_broker.get_positions()
            for symbol, position in positions.items():
                self.dashboard.update_position(symbol, {
                    'quantity': position.get('qty', 0.0) or position.get('lots', 0.0),
                    'entry_price': position.get('avg_entry_price', 0.0) or position.get('open_price', 0.0),
                    'current_price': position.get('current_price', 0.0),
                    'market_value': position.get('market_value', 0.0),
                    'unrealized_pl': position.get('unrealized_pl', 0.0) or position.get('profit', 0.0),
                    'unrealized_plpc': position.get('unrealized_plpc', 0.0),
                    'platform': active_broker.get_platform_name()
                })
            
            # Update market status
            is_market_open = active_broker.check_market_hours()
            next_open, next_close = active_broker.get_next_market_times()
            
            self.dashboard.update_market_status(
                is_open=is_market_open,
                next_open=next_open.isoformat() if next_open else None,
                next_close=next_close.isoformat() if next_close else None
            )
            
            logger.info(f"Updated account info for {active_broker.get_platform_name()}")
        except Exception as e:
            logger.error(f"Error updating account info: {e}")
    
    def start(self):
        """Start the trading bot"""
        if self.is_running:
            logger.warning("Trading bot is already running")
            return
        
        # Connect to brokers
        if not self.connect():
            logger.error("Failed to connect to brokers. Cannot start trading bot.")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # Start trading in a separate thread
        self.trading_thread = threading.Thread(target=self._trading_loop)
        self.trading_thread.daemon = True
        self.trading_thread.start()
        
        logger.info("Trading bot started")
        
        # Add bot activity log
        self.dashboard.add_bot_activity({
            'message': 'Trading bot started',
            'level': 'info',
            'timestamp': datetime.now().isoformat()
        })
    
    def stop(self):
        """Stop the trading bot"""
        if not self.is_running:
            logger.warning("Trading bot is not running")
            return
        
        self.stop_event.set()
        
        if self.trading_thread:
            self.trading_thread.join(timeout=10)
        
        self.is_running = False
        
        # Disconnect from brokers
        self.disconnect()
        
        logger.info("Trading bot stopped")
        
        # Add bot activity log
        self.dashboard.add_bot_activity({
            'message': 'Trading bot stopped',
            'level': 'info',
            'timestamp': datetime.now().isoformat()
        })
    
    def _trading_loop(self):
        """Main trading loop"""
        while not self.stop_event.is_set():
            try:
                # Get the active broker
                active_broker = self.broker_factory.get_active_broker()
                if not active_broker or not active_broker.connected:
                    logger.error("No active broker or not connected. Stopping trading loop.")
                    self.stop_event.set()
                    break
                
                # Check if market is open
                is_market_open = active_broker.check_market_hours()
                
                if is_market_open:
                    # Update account info
                    self._update_account_info()
                    
                    # Check for trading opportunities
                    self._check_trading_opportunities()
                    
                    # Update positions
                    self._update_positions()
                    
                    # Check for exit signals
                    self._check_exit_signals()
                else:
                    logger.info(f"Market is closed for {active_broker.get_platform_name()}")
                    
                    # Sleep for a longer time when market is closed
                    time.sleep(60)
                    continue
                
                # Sleep for a short time between iterations
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                
                # Add bot activity log
                self.dashboard.add_bot_activity({
                    'message': f"Error in trading loop: {e}",
                    'level': 'error',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Sleep for a short time to avoid tight error loops
                time.sleep(5)
    
    def _check_trading_opportunities(self):
        """Check for trading opportunities"""
        # Get the active broker
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker or not active_broker.connected:
            logger.warning("Cannot check trading opportunities: No active broker or not connected")
            return
        
        # Check if we've reached the maximum number of trades for the day
        if self.daily_trades >= MAX_TRADES_PER_DAY:
            logger.info(f"Maximum daily trades reached ({MAX_TRADES_PER_DAY})")
            return
        
        # Check if we've reached the maximum daily loss
        account_info = active_broker.get_account_info()
        equity = account_info.get('equity', 0.0)
        
        if self.daily_pl < 0 and abs(self.daily_pl) > equity * MAX_DAILY_LOSS_PCT:
            logger.warning(f"Maximum daily loss reached ({MAX_DAILY_LOSS_PCT * 100}% of equity)")
            
            # Add bot activity log
            self.dashboard.add_bot_activity({
                'message': f"Maximum daily loss reached ({MAX_DAILY_LOSS_PCT * 100}% of equity). Trading halted for today.",
                'level': 'warning',
                'timestamp': datetime.now().isoformat()
            })
            
            return
        
        # Get the watchlist for the active platform
        watchlist = self._get_platform_watchlist()
        
        # Check each symbol in the watchlist
        for symbol in watchlist:
            try:
                # Skip if we already have a position in this symbol
                if symbol in active_broker.get_positions():
                    continue
                
                # Get market data for the symbol
                data = self.market_data.get_market_data(symbol)
                if data is None or len(data) < 20:  # Need at least 20 bars for analysis
                    continue
                
                # Check each strategy for signals
                for strategy_name, strategy in self.strategies.items():
                    signal = strategy.generate_signal(data)
                    
                    if signal['action'] == 'buy' and signal['probability'] >= MIN_SUCCESS_PROBABILITY:
                        # Calculate position size
                        position_size = self._calculate_position_size(symbol, equity)
                        
                        if position_size < MIN_POSITION_SIZE:
                            logger.info(f"Skipping {symbol}: Position size too small ({position_size:.2f} < {MIN_POSITION_SIZE})")
                            continue
                        
                        # Place buy order
                        self._place_order(symbol, position_size, 'buy', strategy_name, signal)
                        
                        # Increment daily trades counter
                        self.daily_trades += 1
                        
                        # Check if we've reached the maximum number of trades for the day
                        if self.daily_trades >= MAX_TRADES_PER_DAY:
                            logger.info(f"Maximum daily trades reached ({MAX_TRADES_PER_DAY})")
                            break
            except Exception as e:
                logger.error(f"Error checking trading opportunity for {symbol}: {e}")
    
    def _calculate_position_size(self, symbol: str, equity: float) -> float:
        """Calculate position size based on equity and risk parameters"""
        # Get the active broker
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker or not active_broker.connected:
            logger.warning("Cannot calculate position size: No active broker or not connected")
            return 0.0
        
        # Get current price
        current_price = active_broker.get_current_price(symbol)
        if not current_price:
            logger.warning(f"Cannot calculate position size for {symbol}: Unable to get current price")
            return 0.0
        
        # Calculate position size based on equity and maximum position size percentage
        max_position_value = equity * MAX_POSITION_SIZE_PCT
        
        # For forex, position size is in lots
        if active_broker.get_platform_type() == 'forex':
            # Convert max_position_value to lots
            # Assuming standard lot size of 100,000 units
            standard_lot_size = 100000
            
            # Get the base currency of the pair (first 3 letters)
            base_currency = symbol[:3]
            
            # If the base currency is USD, 1 lot = 100,000 USD
            if base_currency == 'USD':
                max_lots = max_position_value / standard_lot_size
            else:
                # For other currencies, need to convert to USD
                # This is a simplified approach
                max_lots = max_position_value / (standard_lot_size * current_price)
            
            # Round to 2 decimal places (0.01 lot precision)
            return round(max_lots, 2)
        else:
            # For stocks, position size is in shares
            max_shares = max_position_value / current_price
            
            # Round down to nearest whole share
            return int(max_shares)
    
    def _place_order(self, symbol: str, quantity: float, side: str, strategy: str, signal: Dict[str, Any]):
        """Place an order"""
        # Get the active broker
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker or not active_broker.connected:
            logger.warning("Cannot place order: No active broker or not connected")
            return
        
        try:
            # Get current price
            current_price = active_broker.get_current_price(symbol)
            if not current_price:
                logger.warning(f"Cannot place order for {symbol}: Unable to get current price")
                return
            
            # Calculate stop loss and take profit prices
            if side == 'buy':
                stop_loss = current_price * (1 - STOP_LOSS_PCT)
                take_profit = current_price * (1 + TAKE_PROFIT_PCT)
            else:
                stop_loss = current_price * (1 + STOP_LOSS_PCT)
                take_profit = current_price * (1 - TAKE_PROFIT_PCT)
            
            # Place market order
            order_result = active_broker.place_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type='market',
                time_in_force='day'
            )
            
            if not order_result:
                logger.error(f"Failed to place {side} order for {symbol}")
                return
            
            order_id = order_result.get('id', '')
            
            # Store order information
            self.orders[order_id] = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': current_price,
                'strategy': strategy,
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log the order
            logger.info(f"Placed {side} order for {quantity} {symbol} at {current_price} (Strategy: {strategy})")
            
            # Add trade to dashboard
            self.dashboard.add_trade({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': current_price,
                'timestamp': datetime.now().isoformat(),
                'strategy': strategy,
                'platform': active_broker.get_platform_name()
            })
            
            # Add bot activity log
            self.dashboard.add_bot_activity({
                'message': f"Placed {side} order for {quantity} {symbol} at {current_price} (Strategy: {strategy})",
                'level': 'info',
                'timestamp': datetime.now().isoformat()
            })
            
            # Send notification
            self.notifications.send_trade_notification(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=current_price,
                strategy=strategy
            )
            
            # Place stop loss order
            stop_order_result = active_broker.place_order(
                symbol=symbol,
                qty=quantity,
                side='sell' if side == 'buy' else 'buy',
                order_type='stop',
                time_in_force='gtc',
                stop_price=stop_loss
            )
            
            if not stop_order_result:
                logger.warning(f"Failed to place stop loss order for {symbol}")
            else:
                logger.info(f"Placed stop loss order for {symbol} at {stop_loss}")
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            
            # Add bot activity log
            self.dashboard.add_bot_activity({
                'message': f"Error placing order for {symbol}: {e}",
                'level': 'error',
                'timestamp': datetime.now().isoformat()
            })
    
    def _update_positions(self):
        """Update positions"""
        # Get the active broker
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker or not active_broker.connected:
            logger.warning("Cannot update positions: No active broker or not connected")
            return
        
        try:
            # Get current positions
            positions = active_broker.get_positions()
            
            # Update dashboard with positions
            for symbol, position in positions.items():
                self.dashboard.update_position(symbol, {
                    'quantity': position.get('qty', 0.0) or position.get('lots', 0.0),
                    'entry_price': position.get('avg_entry_price', 0.0) or position.get('open_price', 0.0),
                    'current_price': position.get('current_price', 0.0),
                    'market_value': position.get('market_value', 0.0),
                    'unrealized_pl': position.get('unrealized_pl', 0.0) or position.get('profit', 0.0),
                    'unrealized_plpc': position.get('unrealized_plpc', 0.0),
                    'platform': active_broker.get_platform_name()
                })
            
            # Store positions
            self.positions = positions
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    def _check_exit_signals(self):
        """Check for exit signals"""
        # Get the active broker
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker or not active_broker.connected:
            logger.warning("Cannot check exit signals: No active broker or not connected")
            return
        
        try:
            # Get current positions
            positions = active_broker.get_positions()
            
            # Check each position for exit signals
            for symbol, position in positions.items():
                # Get market data for the symbol
                data = self.market_data.get_market_data(symbol)
                if data is None or len(data) < 20:  # Need at least 20 bars for analysis
                    continue
                
                # Check each strategy for exit signals
                for strategy_name, strategy in self.strategies.items():
                    signal = strategy.generate_signal(data)
                    
                    # Check for exit signal
                    if (position.get('type', '') == 0 or position.get('side', '') == 'long') and signal['action'] == 'sell':
                        # Close long position
                        self._close_position(symbol, position, 'sell', strategy_name, signal)
                    elif (position.get('type', '') == 1 or position.get('side', '') == 'short') and signal['action'] == 'buy':
                        # Close short position
                        self._close_position(symbol, position, 'buy', strategy_name, signal)
        except Exception as e:
            logger.error(f"Error checking exit signals: {e}")
    
    def _close_position(self, symbol: str, position: Dict[str, Any], side: str, strategy: str, signal: Dict[str, Any]):
        """Close a position"""
        # Get the active broker
        active_broker = self.broker_factory.get_active_broker()
        if not active_broker or not active_broker.connected:
            logger.warning("Cannot close position: No active broker or not connected")
            return
        
        try:
            # Get position quantity
            quantity = position.get('qty', 0.0) or position.get('lots', 0.0)
            
            # Place market order to close position
            order_result = active_broker.place_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type='market',
                time_in_force='day'
            )
            
            if not order_result:
                logger.error(f"Failed to close position for {symbol}")
                return
            
            # Get current price
            current_price = active_broker.get_current_price(symbol)
            if not current_price:
                logger.warning(f"Cannot get current price for {symbol}")
                current_price = 0.0
            
            # Calculate profit/loss
            entry_price = position.get('avg_entry_price', 0.0) or position.get('open_price', 0.0)
            if side == 'sell':
                pl = (current_price - entry_price) * quantity
            else:
                pl = (entry_price - current_price) * quantity
            
            # Update daily P/L
            self.daily_pl += pl
            
            # Update dashboard with daily P/L
            self.dashboard.update_daily_pl(self.daily_pl)
            
            # Log the trade
            logger.info(f"Closed position for {quantity} {symbol} at {current_price} (P/L: {pl:.2f}, Strategy: {strategy})")
            
            # Add trade to dashboard
            self.dashboard.add_trade({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': current_price,
                'timestamp': datetime.now().isoformat(),
                'strategy': strategy,
                'pl': pl,
                'platform': active_broker.get_platform_name()
            })
            
            # Update strategy performance
            self.dashboard.update_strategy_performance(strategy, {
                'trades': 1,
                'wins': 1 if pl > 0 else 0,
                'losses': 1 if pl <= 0 else 0,
                'pl': pl
            })
            
            # Add bot activity log
            self.dashboard.add_bot_activity({
                'message': f"Closed position for {quantity} {symbol} at {current_price} (P/L: {pl:.2f}, Strategy: {strategy})",
                'level': 'info',
                'timestamp': datetime.now().isoformat()
            })
            
            # Send notification
            self.notifications.send_trade_notification(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=current_price,
                strategy=strategy,
                pl=pl
            )
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            
            # Add bot activity log
            self.dashboard.add_bot_activity({
                'message': f"Error closing position for {symbol}: {e}",
                'level': 'error',
                'timestamp': datetime.now().isoformat()
            })
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the trading bot"""
        active_broker = self.broker_factory.get_active_broker()
        
        return {
            'is_running': self.is_running,
            'daily_trades': self.daily_trades,
            'daily_pl': self.daily_pl,
            'active_platform': active_broker.get_platform_name() if active_broker else 'None',
            'market_open': active_broker.check_market_hours() if active_broker else False,
            'positions_count': len(self.positions),
            'available_platforms': self.get_available_platforms()
        } 