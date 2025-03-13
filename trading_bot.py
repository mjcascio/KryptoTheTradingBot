import os
import time
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv
import threading
from strategies import TradingStrategy
from notifications import NotificationSystem
from dashboard import TradingDashboard, run_dashboard
from market_data import MarketDataService
from sleep_manager import SleepManager
from telegram_notifications import send_trade_notification, send_position_closed_notification
from options_trading import OptionsTrading
from strategy_manager import StrategyManager
from market_scanner import MarketScanner
from config import (
    WATCHLIST, FOREX_WATCHLIST, MAX_TRADES_PER_DAY, MIN_SUCCESS_PROBABILITY,
    MAX_POSITION_SIZE_PCT, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    MAX_DAILY_LOSS_PCT, MARKET_OPEN, MARKET_CLOSE, TIMEZONE, PLATFORMS,
    SLEEP_MODE, OPTIONS_CONFIG
)
import pytz
from functools import wraps
from ratelimit import limits, sleep_and_retry
import yfinance as yf

# Import broker abstraction layer
from brokers import BrokerFactory, BaseBroker

# Import SystemMonitor and MetricsConfig
from utils.monitoring import SystemMonitor, MetricsConfig

# Constants
MAX_DAILY_LOSS_PCT = 0.05  # Maximum daily loss as percentage of capital
MAX_POSITION_SIZE_PCT = 0.02  # Maximum position size as percentage of equity
MIN_POSITION_SIZE = 1000  # Minimum position size in dollars
TIMEZONE = 'America/New_York'

# Load environment variables
load_dotenv()

# Configure logging with rotation
log_file = "trading_bot.log"
max_log_size = 10 * 1024 * 1024  # 10MB
backup_count = 5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            log_file,
            maxBytes=max_log_size,
            backupCount=backup_count
        ),
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
    """Trading bot that implements various trading strategies for both stocks and options"""
    
    def __init__(self, strategies=None, dashboard=None, notifications=None):
        """Initialize the trading bot"""
        # Initialize notification system
        self.notification_system = NotificationSystem()
        
        # Initialize other components
        self.broker_factory = BrokerFactory()
        self.strategy_manager = StrategyManager()
        self.market_scanner = MarketScanner()
        self.risk_manager = RiskManager()
        
        # Initialize system monitor with config
        metrics_config = MetricsConfig(
            collection_interval=60,  # 1 minute interval
            retention_days=7,
            alert_thresholds={
                "cpu_usage": 80.0,
                "memory_usage": 80.0,
                "disk_usage": 80.0
            }
        )
        self.system_monitor = SystemMonitor(metrics_config)
        
        # Initialize trading state
        self.is_running = False
        self.stop_event = threading.Event()
        self.trading_thread = None
        self.positions = {'stocks': {}, 'options': {}}
        self.daily_trades = 0
        self.daily_pl = 0.0
        
        # Initialize risk parameters
        self.risk_params = {
            'max_position_size': 5000.0,
            'max_loss_per_trade': 500.0,
            'daily_loss_limit': 2000.0
        }
        
        # Initialize strategy manager
        self.strategy_manager = StrategyManager()
        
        # Initialize options trading
        self.options_trading = OptionsTrading()
        
        # Initialize market scanner
        self.market_scanner = MarketScanner()
        
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
        
        # Initialize sleep manager
        self.sleep_manager = SleepManager()
        
        # Trading metrics
        self.daily_trades = {'stocks': 0, 'options': 0}
        self.daily_pl = {'stocks': 0.0, 'options': 0.0}
        self.orders = {'stocks': {}, 'options': {}}
        
        # Load watchlist based on active platform
        self.watchlist = self._get_platform_watchlist()
        
        logger.info("Trading bot initialized with unified stock and options support")
    
    def _initialize_brokers(self):
        """Initialize brokers based on configuration"""
        default_broker = None
        
        # Create broker instances for enabled platforms
        for platform_id, platform_config in PLATFORMS.items():
            if platform_config.get('enabled', False) or platform_id == 'alpaca':
                broker = self.broker_factory.create_broker(platform_id)
                if broker:
                    # Always set Alpaca as the default broker
                    if platform_id == 'alpaca':
                        default_broker = platform_id
                        logger.info(f"Created Alpaca broker instance")
                    elif platform_config.get('default', False):
                        default_broker = platform_id
                        logger.info(f"Created {platform_id} broker instance (default)")
                    else:
                        logger.info(f"Created {platform_id} broker instance")
        
        # Set the default broker as active
        if default_broker:
            self.broker_factory.set_active_broker(default_broker)
            logger.info(f"Set {default_broker} as the active broker")
        else:
            # If no default broker is specified, use Alpaca
            self.broker_factory.set_active_broker('alpaca')
            logger.info(f"No default broker specified. Using alpaca as the active broker")
            
        # Connect to the active broker
        active_broker = self.broker_factory.get_active_broker()
        if active_broker:
            success = active_broker.connect()
            if success:
                logger.info(f"Successfully connected to {active_broker.get_platform_name()}")
            else:
                logger.error(f"Failed to connect to {active_broker.get_platform_name()}")
        else:
            logger.error("No active broker available")
    
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
                # Get take profit and stop loss values
                take_profit = position.get('take_profit', 0.0) or position.get('tp', 0.0)
                stop_loss = position.get('stop_loss', 0.0) or position.get('sl', 0.0)
                
                # If take profit and stop loss are not set, calculate them based on entry price and percentages
                entry_price = position.get('avg_entry_price', 0.0) or position.get('open_price', 0.0)
                if entry_price > 0:
                    if take_profit <= 0 and hasattr(self, 'take_profit_pct') and self.take_profit_pct > 0:
                        # For long positions, take profit is above entry price
                        if position.get('side', 'long').lower() == 'long':
                            take_profit = entry_price * (1 + self.take_profit_pct)
                        # For short positions, take profit is below entry price
                        else:
                            take_profit = entry_price * (1 - self.take_profit_pct)
                    
                    if stop_loss <= 0 and hasattr(self, 'stop_loss_pct') and self.stop_loss_pct > 0:
                        # For long positions, stop loss is below entry price
                        if position.get('side', 'long').lower() == 'long':
                            stop_loss = entry_price * (1 - self.stop_loss_pct)
                        # For short positions, stop loss is above entry price
                        else:
                            stop_loss = entry_price * (1 + self.stop_loss_pct)
                
                self.dashboard.update_position(symbol, {
                    'quantity': position.get('qty', 0.0) or position.get('lots', 0.0),
                    'entry_price': entry_price,
                    'current_price': position.get('current_price', 0.0),
                    'market_value': position.get('market_value', 0.0),
                    'unrealized_pl': position.get('unrealized_pl', 0.0) or position.get('profit', 0.0),
                    'unrealized_plpc': position.get('unrealized_plpc', 0.0),
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
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
        self.trading_thread = threading.Thread(target=self.run)
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
    
    def run(self):
        """Main trading loop"""
        if self.is_running:
            logger.warning("Trading bot is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # Start dashboard in a separate thread
        dashboard_thread = threading.Thread(target=run_dashboard, args=(self.dashboard,))
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        logger.info("Starting trading bot")
        
        while not self.stop_event.is_set():
            try:
                # Check if market is open
                if not self._is_market_open():
                    time.sleep(60)  # Sleep for 1 minute
                    continue
                
                # Reset daily metrics at market open
                self._reset_daily_metrics_if_needed()
                
                # Get active broker
                active_broker = self.broker_factory.get_active_broker()
                if not active_broker or not active_broker.connected:
                    logger.error("No active broker or broker not connected")
                    time.sleep(60)
                    continue
                
                # Update account information
                self._update_account_info()
                
                # Check if we should be in sleep mode
                if self.sleep_manager.should_sleep():
                    time.sleep(60)
                    continue
                
                # Run market scanner
                scan_results = self.market_scanner.scan_market()
                
                # Process stock trading opportunities
                self._process_stock_opportunities(scan_results.get('stocks', []))
                
                # Process options trading opportunities
                self._process_options_opportunities(scan_results.get('options', []))
                
                # Monitor existing positions
                self._monitor_positions()
                
                # Update dashboard
                self._update_dashboard()
                
                # Sleep for the configured interval
                time.sleep(self.strategy_manager.get_scan_interval())
                
            except Exception as e:
                logger.error(f"Error in main trading loop: {e}")
                time.sleep(60)
    
    def _process_stock_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Process stock trading opportunities"""
        for opportunity in opportunities:
            try:
                # Get strategy parameters
                strategy = self.strategy_manager.get_stock_strategy(opportunity['symbol'])
                
                # Execute trade if strategy conditions are met
                if strategy and strategy.should_enter_trade(opportunity):
                    self.execute_trade(
                        symbol=opportunity['symbol'],
                        side=strategy.get_trade_side(),
                        quantity=strategy.calculate_position_size(self.risk_params),
                        strategy_name=strategy.name
                    )
            except Exception as e:
                logger.error(f"Error processing stock opportunity: {e}")
    
    def _process_options_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Process options trading opportunities"""
        for opportunity in opportunities:
            try:
                # Get strategy parameters
                strategy = self.strategy_manager.get_options_strategy(opportunity['symbol'])
                
                # Execute trade if strategy conditions are met
                if strategy and strategy.should_enter_trade(opportunity):
                    self.execute_options_trade(
                        symbol=opportunity['symbol'],
                        strategy=strategy.name,
                        expiration=strategy.select_expiration(opportunity),
                        strike=strategy.select_strike(opportunity),
                        option_type=strategy.select_option_type(opportunity),
                        quantity=strategy.calculate_contracts(self.risk_params)
                    )
            except Exception as e:
                logger.error(f"Error processing options opportunity: {e}")
    
    def _monitor_positions(self):
        """Monitor all open positions"""
        try:
            # Monitor stock positions
            self._monitor_stock_positions()
            
            # Monitor options positions
            self.monitor_options_positions()
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def _reset_daily_metrics_if_needed(self):
        """Reset daily metrics at market open"""
        now = datetime.now(pytz.timezone(TIMEZONE))
        market_open_time = datetime.strptime(MARKET_OPEN, '%H:%M').time()
        
        if now.time() == market_open_time:
            self.daily_trades = {'stocks': 0, 'options': 0}
            self.daily_pl = {'stocks': 0.0, 'options': 0.0}
            logger.info("Daily metrics reset at market open")
    
    def _update_dashboard(self):
        """Update dashboard with current trading status"""
        status = {
            'stocks': self.get_trading_status(),
            'options': self.get_options_trading_status(),
            'last_update': datetime.now(pytz.timezone(TIMEZONE))
        }
        self.dashboard.update(status)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the trading bot"""
        active_broker = self.broker_factory.get_active_broker()
        
        return {
            'is_running': self.is_running,
            'daily_trades': self.daily_trades['stocks'],
            'daily_pl': self.daily_pl['stocks'],
            'active_platform': active_broker.get_platform_name() if active_broker else 'None',
            'market_open': active_broker.check_market_hours() if active_broker else False,
            'positions_count': len(self.positions['stocks']),
            'available_platforms': self.get_available_platforms()
        }

    def execute_options_trade(self, symbol: str, strategy: str, expiration: str, strike: float, option_type: str, quantity: int) -> bool:
        """Execute an options trade based on the given parameters"""
        try:
            # Verify risk parameters
            if not self.strategy_manager.verify_risk_parameters('options'):
                logger.warning("Risk parameters check failed for options trade")
                return False
            
            # Get current account information
            account_info = self.broker_factory.get_active_broker().get_account()
            equity = account_info.get('equity', 0.0)
            
            # Check daily loss limit
            if self.daily_pl['options'] < 0 and abs(self.daily_pl['options']) > equity * self.risk_params['max_daily_loss_pct']:
                logger.warning(f"Maximum daily loss reached for options trading")
                return False
            
            # Check maximum trades per day
            if self.daily_trades['options'] >= self.risk_params['max_options_trades_per_day']:
                logger.warning(f"Maximum daily options trades reached")
                return False
            
            # Execute the options trade
            trade_result = self.options_trading.place_order(
                symbol=symbol,
                strategy=strategy,
                expiration=expiration,
                strike=strike,
                option_type=option_type,
                quantity=quantity
            )
            
            if trade_result['success']:
                # Update trading metrics
                self.daily_trades['options'] += 1
                order_id = trade_result['order_id']
                
                # Store order information
                self.orders['options'][order_id] = {
                    'symbol': symbol,
                    'strategy': strategy,
                    'expiration': expiration,
                    'strike': strike,
                    'option_type': option_type,
                    'quantity': quantity,
                    'timestamp': datetime.now(pytz.timezone(TIMEZONE))
                }
                
                # Send notification
                self.notifications.send_options_trade_notification(trade_result)
                
                logger.info(f"Options trade executed successfully: {trade_result}")
                return True
            else:
                logger.error(f"Failed to execute options trade: {trade_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self._handle_error(
                str(e),
                context=f"Options Trade Execution ({symbol})",
                is_critical=True
            )
            return False
    
    def monitor_options_positions(self):
        """Monitor and manage open options positions"""
        try:
            # Get all open options positions
            positions = self.options_trading.get_positions()
            
            for position in positions:
                position_id = position['position_id']
                current_value = position['current_value']
                entry_value = position['entry_value']
                
                # Calculate profit/loss percentage
                pl_pct = (current_value - entry_value) / entry_value
                
                # Check stop loss
                if pl_pct <= -self.risk_params['options_stop_loss_pct']:
                    logger.info(f"Stop loss triggered for options position {position_id}")
                    self.close_options_position(position_id)
                
                # Check take profit
                elif pl_pct >= self.risk_params['options_take_profit_pct']:
                    logger.info(f"Take profit triggered for options position {position_id}")
                    self.close_options_position(position_id)
                
                # Check time-based exit (e.g., DTE threshold)
                elif self._should_exit_by_time(position):
                    logger.info(f"Time-based exit triggered for options position {position_id}")
                    self.close_options_position(position_id)
        
        except Exception as e:
            logger.error(f"Error monitoring options positions: {e}")
    
    def close_options_position(self, position_id: str) -> bool:
        """Close an options position"""
        try:
            result = self.options_trading.close_position(position_id)
            
            if result['success']:
                # Update trading metrics
                self.daily_pl['options'] += result.get('realized_pl', 0.0)
                
                # Remove from tracked positions
                if position_id in self.positions['options']:
                    del self.positions['options'][position_id]
                
                # Send notification
                self.notifications.send_options_position_closed_notification(result)
                
                logger.info(f"Options position closed successfully: {result}")
                return True
            else:
                logger.error(f"Failed to close options position: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing options position: {e}")
            return False
    
    def _should_exit_by_time(self, position: Dict[str, Any]) -> bool:
        """Check if an options position should be exited based on time criteria"""
        try:
            # Get days to expiration
            expiration = datetime.strptime(position['expiration'], '%Y-%m-%d')
            now = datetime.now(pytz.timezone(TIMEZONE))
            dte = (expiration - now).days
            
            # Exit if DTE is below threshold
            if dte <= self.risk_params['min_dte']:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking time-based exit criteria: {e}")
            return False
    
    def get_options_trading_status(self) -> Dict[str, Any]:
        """Get current status of options trading"""
        return {
            'daily_trades': self.daily_trades['options'],
            'daily_pl': self.daily_pl['options'],
            'positions_count': len(self.positions['options']),
            'risk_parameters': self.risk_params
        }

    def _monitor_stock_positions(self):
        """Monitor and manage open stock positions"""
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker or not active_broker.connected:
                self._handle_error(
                    "Cannot monitor positions: No active broker or not connected",
                    context="Position Monitoring"
                )
                return
            
            # Get all open stock positions
            positions = active_broker.get_positions()
            
            for symbol, position in positions.items():
                try:
                    # Get current price and position details
                    current_price = position.get('current_price', 0.0)
                    entry_price = position.get('avg_entry_price', 0.0)
                    side = position.get('side', 'long').lower()
                    
                    if current_price <= 0 or entry_price <= 0:
                        continue
                    
                    # Calculate profit/loss percentage
                    pl_pct = (current_price - entry_price) / entry_price
                    if side == 'short':
                        pl_pct = -pl_pct
                    
                    # Get strategy for this position
                    strategy = self.strategy_manager.get_stock_strategy(symbol)
                    if not strategy:
                        continue
                    
                    # Check exit conditions
                    should_exit = False
                    exit_reason = None
                    
                    # Check stop loss
                    if pl_pct <= -self.risk_params['stock_stop_loss_pct']:
                        should_exit = True
                        exit_reason = "Stop loss triggered"
                    
                    # Check take profit
                    elif pl_pct >= self.risk_params['stock_take_profit_pct']:
                        should_exit = True
                        exit_reason = "Take profit triggered"
                    
                    # Check strategy-specific exit conditions
                    elif strategy.should_exit_trade(position):
                        should_exit = True
                        exit_reason = "Strategy exit signal"
                    
                    if should_exit:
                        logger.info(f"{exit_reason} for {symbol}")
                        self._close_stock_position(symbol, position, exit_reason)
                    else:
                        # Only log position status, don't send notification or trigger position updates
                        logger.debug(f"Monitoring position: {symbol} {side.upper()}, P/L: {pl_pct:.2%}")
                
                except Exception as e:
                    logger.error(f"Error monitoring position for {symbol}: {e}")
            
        except Exception as e:
            self._handle_error(
                str(e),
                context="Stock Position Monitoring",
                is_critical=True
            )
    
    def _close_stock_position(self, symbol: str, position: Dict[str, Any], reason: str) -> bool:
        """Close a stock position"""
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker or not active_broker.connected:
                logger.error("Cannot close position: No active broker or not connected")
                return False
            
            # Get position details
            quantity = position.get('qty', 0) or position.get('quantity', 0)
            side = position.get('side', 'long').lower()
            
            # Determine closing order side
            close_side = 'sell' if side == 'long' else 'buy'
            
            # Place closing order
            result = active_broker.place_order(
                symbol=symbol,
                qty=quantity,
                side=close_side,
                order_type='market',
                time_in_force='day'
            )
            
            if result['success']:
                # Update trading metrics
                self.daily_pl['stocks'] += result.get('realized_pl', 0.0)
                
                # Remove from tracked positions
                if symbol in self.positions['stocks']:
                    del self.positions['stocks'][symbol]
                
                # Send notification
                send_position_closed_notification(
                    symbol=symbol,
                    side=close_side,
                    quantity=quantity,
                    price=result.get('price', 0.0),
                    pl=result.get('realized_pl', 0.0),
                    reason=reason
                )
                
                logger.info(f"Stock position closed successfully: {symbol} ({reason})")
                return True
            else:
                logger.error(f"Failed to close stock position: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing stock position {symbol}: {e}")
            return False
    
    def execute_trade(self, symbol: str, side: str, quantity: float, strategy_name: str) -> bool:
        """Execute a stock trade"""
        try:
            # Verify risk parameters
            if not self.strategy_manager.verify_risk_parameters('stocks'):
                logger.warning("Risk parameters check failed for stock trade")
                return False
            
            # Get current account information
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker or not active_broker.connected:
                logger.error("Cannot execute trade: No active broker or not connected")
                return False
            
            account_info = active_broker.get_account()
            equity = account_info.get('equity', 0.0)
            
            # Check daily loss limit
            if self.daily_pl['stocks'] < 0 and abs(self.daily_pl['stocks']) > equity * self.risk_params['max_daily_loss_pct']:
                logger.warning(f"Maximum daily loss reached for stock trading")
                return False
            
            # Check maximum trades per day
            if self.daily_trades['stocks'] >= self.risk_params['max_stock_trades_per_day']:
                logger.warning(f"Maximum daily stock trades reached")
                return False
            
            # Place the order
            result = active_broker.place_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type='market',
                time_in_force='day'
            )
            
            if result['success']:
                # Update trading metrics
                self.daily_trades['stocks'] += 1
                order_id = result['order_id']
                
                # Store order information
                self.orders['stocks'][order_id] = {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'strategy': strategy_name,
                    'timestamp': datetime.now(pytz.timezone(TIMEZONE))
                }
                
                # Send notification
                send_trade_notification(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=result.get('price', 0.0),
                    strategy=strategy_name
                )
                
                logger.info(f"Stock trade executed successfully: {symbol} {side} {quantity} shares")
                return True
            else:
                logger.error(f"Failed to execute stock trade: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self._handle_error(
                str(e),
                context=f"Stock Trade Execution ({symbol})",
                is_critical=True
            )
            return False
    
    def _is_market_open(self) -> bool:
        """Check if the market is currently open"""
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker or not active_broker.connected:
                return False
            
            # Get current time in market timezone
            now = datetime.now(pytz.timezone(TIMEZONE))
            
            # First check with the broker
            if not active_broker.check_market_hours():
                return False
            
            # Get market hours
            market_open_time = datetime.strptime(MARKET_OPEN, '%H:%M').time()
            market_close_time = datetime.strptime(MARKET_CLOSE, '%H:%M').time()
            
            # Check if current time is within market hours
            current_time = now.time()
            
            # Handle overnight markets (e.g., crypto or forex)
            if market_open_time < market_close_time:
                return market_open_time <= current_time <= market_close_time
            else:
                # Market spans midnight
                return current_time >= market_open_time or current_time <= market_close_time
            
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False

    def _handle_error(self, error: str, error_type: str = "ERROR", is_critical: bool = False):
        """Handle and report errors."""
        logger.error(f"{error_type}: {error}")
        
        # Record error in system monitor
        if self.system_monitor:
            self.system_monitor.record_error(error_type)
        
        # Send notification
        subject = f"KryptoBot {error_type}"
        message = f"""
Error Details:
-------------
Type: {error_type}
Message: {error}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

System Status:
-------------
{self._get_system_status()}
"""
        self.notification_system.send_notification(subject, message)
        
        # Run diagnostics if critical error
        if is_critical and self.system_monitor:
            diagnostics = self.system_monitor.run_diagnostics()
            if diagnostics.get('critical_issues', 0) > 0:
                self.notification_system.send_notification(
                    "Critical System Issues Detected",
                    f"Diagnostics found {diagnostics['critical_issues']} critical issues.\n"
                    f"Please check the diagnostic report for details."
                )

    def start_stock_trading(self):
        """Start stock trading only."""
        if not self.is_running:
            logger.info("Starting stock trading")
            self.is_running = True
            self.stop_event.clear()
            
            # Start trading in a separate thread
            self.trading_thread = threading.Thread(target=self._run_stock_trading)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            
            logger.info("Stock trading started")
            
            # Add bot activity log
            self.dashboard.add_bot_activity({
                'message': 'Stock trading started',
                'level': 'info',
                'timestamp': datetime.now().isoformat()
            })
    
    def stop_stock_trading(self):
        """Stop stock trading only."""
        if not self.is_running:
            logger.warning("Stock trading is not running")
            return
        
        logger.info("Stopping stock trading")
        self.stop_event.set()
        
        if self.trading_thread:
            self.trading_thread.join(timeout=10)
        
        self.is_running = False
        
        # Add bot activity log
        self.dashboard.add_bot_activity({
            'message': 'Stock trading stopped',
            'level': 'info',
            'timestamp': datetime.now().isoformat()
        })
    
    def start_options_trading(self):
        """Start options trading only."""
        if not hasattr(self, 'options_trading') or not self.options_trading:
            logger.error("Options trading module not initialized")
            return
        
        logger.info("Starting options trading")
        
        # Initialize options trading state
        self.options_trading.is_running = True
        self.options_trading.stop_event = threading.Event()
        
        # Start options trading in a separate thread
        self.options_trading_thread = threading.Thread(target=self._run_options_trading)
        self.options_trading_thread.daemon = True
        self.options_trading_thread.start()
        
        logger.info("Options trading started")
        
        # Add bot activity log
        self.dashboard.add_bot_activity({
            'message': 'Options trading started',
            'level': 'info',
            'timestamp': datetime.now().isoformat()
        })
    
    def stop_options_trading(self):
        """Stop options trading only."""
        if not hasattr(self, 'options_trading') or not self.options_trading:
            logger.error("Options trading module not initialized")
            return
        
        if not hasattr(self.options_trading, 'is_running') or not self.options_trading.is_running:
            logger.warning("Options trading is not running")
            return
        
        logger.info("Stopping options trading")
        
        # Stop the options trading thread
        if hasattr(self.options_trading, 'stop_event'):
            self.options_trading.stop_event.set()
        
        if hasattr(self, 'options_trading_thread'):
            self.options_trading_thread.join(timeout=10)
            self.options_trading_thread = None
        
        self.options_trading.is_running = False
        
        # Add bot activity log
        self.dashboard.add_bot_activity({
            'message': 'Options trading stopped',
            'level': 'info',
            'timestamp': datetime.now().isoformat()
        })
    
    def _run_stock_trading(self):
        """Main stock trading loop."""
        logger.info("Starting stock trading loop")
        
        while not self.stop_event.is_set():
            try:
                # Check if market is open
                if not self._is_market_open():
                    time.sleep(60)  # Sleep for 1 minute
                    continue
                
                # Reset daily metrics at market open
                self._reset_daily_metrics_if_needed()
                
                # Get active broker
                active_broker = self.broker_factory.get_active_broker()
                if not active_broker or not active_broker.connected:
                    logger.error("No active broker or broker not connected")
                    time.sleep(60)
                    continue
                
                # Update account information
                self._update_account_info()
                
                # Check if we should be in sleep mode
                if self.sleep_manager.should_sleep():
                    time.sleep(60)
                    continue
                
                # Run market scanner for stocks only
                scan_results = self.market_scanner.scan_market(asset_type='stocks')
                
                # Process stock trading opportunities
                self._process_stock_opportunities(scan_results.get('stocks', []))
                
                # Monitor stock positions
                self._monitor_stock_positions()
                
                # Update dashboard
                self._update_dashboard()
                
                # Sleep for the configured interval
                time.sleep(self.strategy_manager.get_scan_interval())
                
            except Exception as e:
                self._handle_error(
                    str(e),
                    context="Stock Trading Loop",
                    is_critical=True
                )
                time.sleep(60)
    
    def _run_options_trading(self):
        """Main options trading loop."""
        logger.info("Starting options trading loop")
        
        while not self.options_trading.stop_event.is_set():
            try:
                # Check if market is open
                if not self._is_market_open():
                    time.sleep(60)  # Sleep for 1 minute
                    continue
                
                # Reset daily metrics at market open
                self._reset_daily_metrics_if_needed()
                
                # Get active broker
                active_broker = self.broker_factory.get_active_broker()
                if not active_broker or not active_broker.connected:
                    logger.error("No active broker or broker not connected")
                    time.sleep(60)
                    continue
                
                # Update account information
                self._update_account_info()
                
                # Check if we should be in sleep mode
                if self.sleep_manager.should_sleep():
                    time.sleep(60)
                    continue
                
                # Run market scanner for options only
                scan_results = self.market_scanner.scan_market(asset_type='options')
                
                # Process options trading opportunities
                self._process_options_opportunities(scan_results.get('options', []))
                
                # Monitor options positions
                self.monitor_options_positions()
                
                # Update dashboard
                self._update_dashboard()
                
                # Sleep for the configured interval
                time.sleep(self.strategy_manager.get_scan_interval())
                
            except Exception as e:
                self._handle_error(
                    str(e),
                    context="Options Trading Loop",
                    is_critical=True
                )
                time.sleep(60)
    
    def _get_system_status(self) -> str:
        """Get formatted system status string."""
        try:
            if not self.system_monitor:
                return "System monitor not initialized"
            
            health = self.system_monitor.get_system_health()
            
            # Format system metrics
            system_metrics = health['system']
            status = f"""CPU Usage: {system_metrics['cpu_usage']}
Memory Usage: {system_metrics['memory_usage']}
Disk Usage: {system_metrics['disk_usage']}"""

            # Add trading bot status if available
            if 'trading_bot' in health:
                bot_status = health['trading_bot']
                status += f"""

Trading Bot:
- Running: {bot_status.get('is_running', False)}
- Market Open: {bot_status.get('market_open', False)}
- Active Broker: {bot_status.get('active_broker', {}).get('name', 'None')}
- Stock Positions: {bot_status.get('positions', {}).get('stocks', 0)}
- Options Positions: {bot_status.get('positions', {}).get('options', 0)}"""

            # Add error metrics
            if 'error_metrics' in health:
                error_metrics = health['error_metrics']
                status += f"""

Error Metrics:
- Total Errors: {error_metrics.get('error_count', 0)}
- Total Warnings: {error_metrics.get('warning_count', 0)}
- Last Diagnostic: {error_metrics.get('last_diagnostic_run', 'Never')}"""
            
            return status
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return f"Error getting system status: {str(e)}" 