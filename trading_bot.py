import os
import time
from datetime import datetime, timedelta
import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import threading
from strategies import TradingStrategy
from notifications import NotificationSystem
from dashboard import TradingDashboard, run_dashboard
from market_data import MarketDataService
from config import (
    WATCHLIST, MAX_TRADES_PER_DAY, MIN_SUCCESS_PROBABILITY,
    MAX_POSITION_SIZE_PCT, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    MAX_DAILY_LOSS_PCT, MARKET_OPEN, MARKET_CLOSE, TIMEZONE
)
import pytz
from functools import wraps
from ratelimit import limits, sleep_and_retry
import yfinance as yf

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
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:  # Last attempt
                        logger.error(f"Failed after {retries} attempts: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@sleep_and_retry
@limits(calls=CALLS_PER_SECOND, period=PERIOD)
def rate_limited_api_call(func, *args, **kwargs):
    """Wrapper for rate-limited API calls"""
    return func(*args, **kwargs)

class TradingBot:
    def __init__(self, ml_enhancer=None, strategy_allocator=None, 
                portfolio_optimizer=None, performance_analyzer=None, 
                parameter_tuner=None):
        """
        Initialize the Trading Bot with enhanced features
        
        Args:
            ml_enhancer: Machine Learning Signal Enhancer
            strategy_allocator: Strategy Allocator
            portfolio_optimizer: Portfolio Optimizer
            performance_analyzer: Performance Analyzer
            parameter_tuner: Adaptive Parameter Tuner
        """
        self.api = None
        self.strategy = None
        self.notifications = None
        self.dashboard = None
        self.market_data = None
        self.daily_trades = 0
        self.daily_pl = 0.0
        self.positions = {}
        self.win_count = 0
        self.loss_count = 0
        self.running = True
        
        # Initialize components
        self._initialize_components(ml_enhancer, strategy_allocator, portfolio_optimizer, performance_analyzer, parameter_tuner)
        
    def _initialize_components(self, ml_enhancer, strategy_allocator, portfolio_optimizer, performance_analyzer, parameter_tuner):
        """Initialize API and strategy components"""
        try:
            # Initialize Alpaca API
            self.api = tradeapi.REST(
                os.getenv('ALPACA_API_KEY'),
                os.getenv('ALPACA_SECRET_KEY'),
                base_url=os.getenv('ALPACA_BASE_URL'),
                api_version='v2'
            )
            
            # Test API connection
            try:
                account = self.api.get_account()
                logger.info(f"Connected to Alpaca API. Account status: {account.status}")
                
                # Initialize account info in dashboard
                self.account_info = {
                    'equity': float(account.equity),
                    'buying_power': float(account.buying_power),
                    'cash': float(account.cash)
                }
            except Exception as e:
                logger.error(f"Failed to connect to Alpaca API: {str(e)}")
                raise
            
            # Initialize strategy
            self.strategy = TradingStrategy()
            
            # Initialize notifications
            self.notifications = NotificationSystem()
            
            # Initialize dashboard
            self.dashboard = TradingDashboard()
            
            # Update initial dashboard data
            self.dashboard.update_account(self.account_info)
            
            # Initialize market data service
            self.market_data = MarketDataService(self.api)
            
            # Set initial market status
            try:
                is_market_open = self.market_data.check_market_hours()
                
                # Calculate next market times manually if API fails
                now = datetime.now()
                if now.weekday() >= 5:  # Weekend
                    days_to_monday = 7 - now.weekday() + 0
                    next_day = now + timedelta(days=days_to_monday)
                else:
                    next_day = now + timedelta(days=1)
                
                next_open = next_day.replace(hour=9, minute=30, second=0).strftime('%Y-%m-%d %H:%M:%S')
                next_close = next_day.replace(hour=16, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
                
                self.dashboard.update_market_status(
                    is_open=is_market_open,
                    next_open=next_open,
                    next_close=next_close
                )
                logger.info(f"Set initial market status: is_open={is_market_open}, next_open={next_open}, next_close={next_close}")
            except Exception as e:
                logger.error(f"Error setting initial market status: {str(e)}")
            
            # Initialize metrics
            self._initialize_metrics()
            
            # Initialize enhanced features
            self.ml_enhancer = ml_enhancer
            self.strategy_allocator = strategy_allocator
            self.portfolio_optimizer = portfolio_optimizer
            self.performance_analyzer = performance_analyzer
            self.parameter_tuner = parameter_tuner
            
            # Start dashboard in a separate thread
            self.dashboard_thread = threading.Thread(target=run_dashboard)
            self.dashboard_thread.daemon = True
            self.dashboard_thread.start()
            
            logger.info("Trading bot components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            raise

    def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            logger.info("Cleaning up resources...")
            
            # Cancel all open orders
            open_orders = rate_limited_api_call(self.api.list_orders, status='open')
            for order in open_orders:
                try:
                    rate_limited_api_call(self.api.cancel_order, order.id)
                    logger.info(f"Cancelled order {order.id}")
                except Exception as e:
                    logger.error(f"Error cancelling order {order.id}: {str(e)}")
            
            # Log final positions
            self._sync_positions()
            if self.positions:
                logger.info("Final positions at shutdown:")
                for symbol, pos in self.positions.items():
                    logger.info(f"{symbol}: {pos}")
            
            # Clear internal state
            self.positions = {}
            self.running = False
            
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def stop(self):
        """Signal the bot to stop gracefully"""
        logger.info("Stopping trading bot...")
        self.running = False

    def run(self):
        """Main trading loop"""
        logger.info("Starting trading bot...")
        self.notifications.alert("Trading bot started", "INFO")
        
        # Initial update of market status
        try:
            is_market_open = self.market_data.check_market_hours()
            next_open, next_close = self.market_data.get_next_market_times()
            self.dashboard.update_market_status(
                is_open=is_market_open,
                next_open=next_open,
                next_close=next_close
            )
        except Exception as e:
            logger.error(f"Error updating initial market status: {str(e)}")
        
        # Initial update of account information
        try:
            account = self.api.get_account()
            self.account_info = {
                'equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'cash': float(account.cash)
            }
            self.dashboard.update_account(self.account_info)
            
            # Update equity history
            self.dashboard.update_equity(float(account.equity))
            
            logger.info(f"Updated account info: Equity=${self.account_info['equity']:.2f}, Buying Power=${self.account_info['buying_power']:.2f}")
        except Exception as e:
            logger.error(f"Error updating initial account info: {str(e)}")
        
        try:
            while self.running:
                try:
                    now = datetime.now(pytz.timezone(TIMEZONE))
                    
                    # Reset daily metrics at market open
                    if now.strftime('%H:%M') == MARKET_OPEN:
                        self.reset_daily_metrics()
                        self.notifications.daily_summary(
                            total_trades=self.daily_trades,
                            win_rate=(self.win_count / self.daily_trades * 100) if self.daily_trades > 0 else 0,
                            total_pl=self.daily_pl
                        )
                    
                    # Check if market is open using market data service
                    try:
                        is_market_open = self.market_data.check_market_hours()
                        
                        # Update dashboard with market status
                        next_open, next_close = self.market_data.get_next_market_times()
                        self.dashboard.update_market_status(
                            is_open=is_market_open,
                            next_open=next_open,
                            next_close=next_close
                        )
                    except Exception as e:
                        logger.error(f"Error checking market status: {str(e)}")
                        is_market_open = False
                    
                    # Update account information in dashboard
                    try:
                        account = self.api.get_account()
                        self.account_info = {
                            'equity': float(account.equity),
                            'buying_power': float(account.buying_power),
                            'cash': float(account.cash)
                        }
                        self.dashboard.update_account(self.account_info)
                        
                        # Update equity history
                        self.dashboard.update_equity(float(account.equity))
                        
                        logger.info(f"Updated account info: Equity=${self.account_info['equity']:.2f}, Buying Power=${self.account_info['buying_power']:.2f}")
                    except Exception as e:
                        logger.error(f"Error updating account info: {str(e)}")
                    
                    if not is_market_open:
                        logger.info("Market is closed")
                        time.sleep(60)
                        continue
                    
                    logger.info("Market is open - scanning for opportunities...")
                    
                    # Sync positions and monitor existing ones
                    self._sync_positions()
                    self.monitor_positions()
                    
                    # Tune parameters if needed
                    self.tune_parameters()
                    
                    # Get potential trades
                    potential_trades = []
                    for symbol in WATCHLIST:
                        if not self.running:
                            break
                            
                        # Skip if we already have a position
                        if symbol in self.positions:
                            continue
                        
                        trade_params = self.check_trade_conditions(symbol)
                        if trade_params:
                            potential_trades.append({
                                'symbol': symbol,
                                **trade_params
                            })
                    
                    # Optimize portfolio if available
                    if self.portfolio_optimizer and potential_trades:
                        account = self.api.get_account()
                        account_value = float(account.equity)
                        
                        # Get current positions
                        current_positions = {}
                        positions = self.api.list_positions()
                        for position in positions:
                            current_positions[position.symbol] = {
                                'quantity': int(position.qty),
                                'current_price': float(position.current_price),
                                'unrealized_pl': float(position.unrealized_pl)
                            }
                            
                        # Optimize portfolio
                        optimized_trades = self.portfolio_optimizer.optimize_portfolio(
                            current_positions, potential_trades, account_value
                        )
                        
                        # Execute optimized trades
                        for trade in optimized_trades:
                            self.execute_trade(trade['symbol'], trade)
                    else:
                        # Execute all potential trades
                        for trade in potential_trades:
                            self.execute_trade(trade['symbol'], trade)
                    
                    # Sleep for 1 minute before next iteration
                    for _ in range(60):  # Check should_run every second
                        if not self.running:
                            break
                        time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}")
                    time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.cleanup()
            logger.info("Trading bot stopped")

    def _initialize_metrics(self):
        """Initialize or restore metrics, especially after restart"""
        try:
            # Get current ET time
            et_time = datetime.now(pytz.timezone(TIMEZONE))
            
            # Check if we need to reset metrics
            if self.daily_trades == 0:
                self.reset_daily_metrics()
            
            # Sync positions with actual account positions
            self._sync_positions()
            
            logger.info("Metrics initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing metrics: {str(e)}")
            
    def _sync_positions(self):
        """Synchronize internal position tracking with Alpaca positions"""
        try:
            # Get all current positions
            positions = self.api.list_positions()
            
            # Reset positions dictionary
            self.positions = {}
            
            # Rebuild positions from current account state
            for position in positions:
                symbol = position.symbol
                self.positions[symbol] = {
                    'shares': int(position.qty),
                    'entry_price': float(position.avg_entry_price),
                    'current_price': float(position.current_price),
                    'market_value': float(position.market_value),
                    'unrealized_pl': float(position.unrealized_pl)
                }
                
                # Update dashboard with position data
                self.dashboard.update_position(symbol, {
                    'quantity': int(position.qty),
                    'entry_price': float(position.avg_entry_price),
                    'current_price': float(position.current_price),
                    'unrealized_pl': float(position.unrealized_pl),
                    'stop_loss': float(position.avg_entry_price) * 0.98,  # Estimated stop loss
                    'take_profit': float(position.avg_entry_price) * 1.05  # Estimated take profit
                })
            
            logger.info(f"Synchronized {len(self.positions)} positions")
        except Exception as e:
            logger.error(f"Error syncing positions: {str(e)}")
    
    def reset_daily_metrics(self):
        """Reset daily trading metrics"""
        self.daily_trades = 0
        self.daily_pl = 0.0
        self.win_count = 0
        self.loss_count = 0
        
    def get_market_data(self, symbol: str, timeframe: str = '15Min', limit: int = 100) -> pd.DataFrame:
        """
        Fetch market data using the market data service
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe for data
            limit: Number of bars to fetch
            
        Returns:
            DataFrame with market data
        """
        data = self.market_data.get_market_data(symbol, timeframe, limit)
        if data is None or data.empty:
            logger.error(f"Error fetching market data for {symbol}")
            return pd.DataFrame()
        return data
            
    def calculate_position_size(self, symbol: str, trade_params: Dict) -> int:
        """
        Calculate position size based on account equity and risk parameters
        
        Args:
            symbol: Stock symbol
            trade_params: Dictionary with trade parameters
            
        Returns:
            Number of shares to trade
        """
        try:
            account = self.api.get_account()
            equity = float(account.equity)
            
            # Base position size on account equity and max position size
            base_position = equity * MAX_POSITION_SIZE_PCT
            
            # Adjust for volatility
            adjusted_position = base_position * trade_params['position_size_modifier']
            
            # Get current price
            current_price = float(trade_params['entry_price'])
            
            # Calculate number of shares
            shares = int(adjusted_position / current_price)
            
            logger.info(f"Calculated position size for {symbol}: {shares} shares (${adjusted_position:.2f})")
            
            return shares
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0
        
    def check_trade_conditions(self, symbol: str) -> Optional[Dict]:
        """
        Check if trading conditions are met
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with trade parameters or None
        """
        try:
            # Check if we've reached daily trade limit
            if self.daily_trades >= MAX_TRADES_PER_DAY:
                logger.info("Daily trade limit reached")
                return None
                
            # Check if we've hit daily loss limit
            account = self.api.get_account()
            if self.daily_pl <= -(float(account.equity) * MAX_DAILY_LOSS_PCT):
                logger.info("Daily loss limit reached")
                return None
                
            # Get market data
            data = self.get_market_data(symbol)
            if data.empty:
                return None
                
            # Use strategy allocator if available
            if self.strategy_allocator:
                signal = self.strategy_allocator.get_optimal_strategy(symbol, data, self.strategy)
                if signal is None:
                    return None
                    
                # Use ML enhancer if available
                if self.ml_enhancer and signal['probability'] >= 0.6:
                    enhanced_signal = self.ml_enhancer.enhance_signal(data, signal)
                    if enhanced_signal['combined_score'] < MIN_SUCCESS_PROBABILITY:
                        return None
                    return enhanced_signal
                    
                # Check if probability meets minimum threshold
                if signal['probability'] < MIN_SUCCESS_PROBABILITY:
                    return None
                    
                return signal
            else:
                # Use basic strategy
                success_prob, trade_params = self.strategy.analyze_trade_opportunity(data)
                
                # Use ML enhancer if available
                if self.ml_enhancer and success_prob >= 0.6:
                    enhanced_signal = self.ml_enhancer.enhance_signal(data, {
                        'probability': success_prob,
                        **trade_params
                    })
                    if enhanced_signal['combined_score'] < MIN_SUCCESS_PROBABILITY:
                        return None
                    return enhanced_signal
                
                # Check if probability meets minimum threshold
                if success_prob < MIN_SUCCESS_PROBABILITY:
                    return None
                
                return trade_params
        except Exception as e:
            logger.error(f"Error checking trade conditions: {str(e)}")
            return None
        
    def execute_trade(self, symbol: str, trade_params: Dict):
        """
        Execute trade with given parameters
        
        Args:
            symbol: Stock symbol
            trade_params: Dictionary with trade parameters
        """
        try:
            # Calculate position size
            shares = self.calculate_position_size(symbol, trade_params)
            
            if shares <= 0:
                logger.info(f"Invalid position size calculated for {symbol}")
                return
                
            # Get current price from market data service
            current_price = self.market_data.get_current_price(symbol)
            if current_price is None:
                logger.error(f"Could not get current price for {symbol}")
                return
                
            # Update entry price with current price
            trade_params['entry_price'] = current_price
                
            # Place entry order
            entry_order = self.api.submit_order(
                symbol=symbol,
                qty=shares,
                side='buy',
                type='limit',
                time_in_force='day',
                limit_price=trade_params['entry_price']
            )
            
            # Place stop loss
            stop_loss_order = self.api.submit_order(
                symbol=symbol,
                qty=shares,
                side='sell',
                type='stop',
                time_in_force='gtc',
                stop_price=trade_params['stop_loss']
            )
            
            # Place take profit
            take_profit_order = self.api.submit_order(
                symbol=symbol,
                qty=shares,
                side='sell',
                type='limit',
                time_in_force='gtc',
                limit_price=trade_params['take_profit']
            )
            
            # Update tracking
            self.positions[symbol] = {
                'entry_order_id': entry_order.id,
                'stop_loss_id': stop_loss_order.id,
                'take_profit_id': take_profit_order.id,
                'shares': shares,
                'entry_price': trade_params['entry_price'],
                'entry_time': datetime.now().isoformat(),
                'stop_loss': trade_params['stop_loss'],
                'take_profit': trade_params['take_profit']
            }
            
            # Add trade to dashboard history
            self.dashboard.add_trade({
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'side': 'buy',
                'quantity': shares,
                'price': trade_params['entry_price'],
                'type': 'limit'
            })
            
            # Update dashboard with position data
            self.dashboard.update_position(symbol, {
                'quantity': shares,
                'entry_price': trade_params['entry_price'],
                'current_price': trade_params['entry_price'],
                'unrealized_pl': 0.0,
                'stop_loss': trade_params['stop_loss'],
                'take_profit': trade_params['take_profit']
            })
            
            # Record trade in performance analyzer if available
            if self.performance_analyzer:
                self.performance_analyzer.add_trade({
                    'symbol': symbol,
                    'entry_time': datetime.now().isoformat(),
                    'entry_price': trade_params['entry_price'],
                    'shares': shares,
                    'stop_loss': trade_params['stop_loss'],
                    'take_profit': trade_params['take_profit'],
                    'strategy': trade_params.get('strategies_used', ['default']),
                    'market_condition': trade_params.get('market_condition', 'unknown')
                })
            
            self.daily_trades += 1
            logger.info(f"Trade executed for {symbol}: {shares} shares at {trade_params['entry_price']}")
            
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {str(e)}")
            self.notifications.alert(f"Trade execution error: {str(e)}", "ERROR")
            
    def monitor_positions(self):
        """Monitor and update existing positions"""
        try:
            positions = self.api.list_positions()
            
            # Get account info
            account = self.api.get_account()
            account_value = float(account.equity)
            
            # Update daily P&L
            self.daily_pl = sum(float(position.unrealized_pl) for position in positions)
            
            # Update dashboard with daily stats
            self.dashboard.update_daily_stats({
                'trades': self.daily_trades,
                'win_rate': (self.win_count / (self.win_count + self.loss_count) * 100) if (self.win_count + self.loss_count) > 0 else 0.0,
                'total_pl': self.daily_pl
            })
            
            # Update daily P/L history
            self.dashboard.update_daily_pl(self.daily_pl)
            
            # Check for closed positions
            current_symbols = [position.symbol for position in positions]
            closed_positions = [symbol for symbol in self.positions if symbol not in current_symbols]
            
            for symbol in closed_positions:
                position = self.positions[symbol]
                
                # Get last price
                last_price = self.market_data.get_current_price(symbol)
                if last_price is None:
                    continue
                    
                # Calculate profit/loss
                entry_price = position['entry_price']
                shares = position['shares']
                profit = (last_price - entry_price) * shares
                
                # Update win/loss count
                if profit > 0:
                    self.win_count += 1
                else:
                    self.loss_count += 1
                    
                # Add trade to dashboard history
                self.dashboard.add_trade({
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': symbol,
                    'side': 'sell',
                    'quantity': shares,
                    'price': last_price,
                    'type': 'market'
                })
                
                # Update strategy performance if strategy is known
                if 'strategy' in position:
                    self.dashboard.update_strategy_performance(
                        position['strategy'],
                        {'profit': profit, 'symbol': symbol}
                    )
                    
                # Update trade in performance analyzer
                if self.performance_analyzer:
                    self.performance_analyzer.add_trade({
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'exit_time': datetime.now().isoformat(),
                        'entry_price': entry_price,
                        'exit_price': last_price,
                        'shares': shares,
                        'profit': profit,
                        'status': 'closed'
                    })
                    
                logger.info(f"Position closed for {symbol}: P&L = ${profit:.2f}")
                
                # Remove from positions
                del self.positions[symbol]
            
            # Update existing positions in dashboard
            for position in positions:
                symbol = position.symbol
                self.dashboard.update_position(symbol, {
                    'quantity': int(position.qty),
                    'entry_price': float(position.avg_entry_price),
                    'current_price': float(position.current_price),
                    'unrealized_pl': float(position.unrealized_pl),
                    'stop_loss': float(position.avg_entry_price) * 0.98,  # Estimated stop loss
                    'take_profit': float(position.avg_entry_price) * 1.05  # Estimated take profit
                })
            
            # Check if rebalancing is needed
            if self.portfolio_optimizer:
                current_positions = {}
                for position in positions:
                    current_positions[position.symbol] = {
                        'quantity': int(position.qty),
                        'current_price': float(position.current_price),
                        'unrealized_pl': float(position.unrealized_pl)
                    }
                    
                rebalance_actions = self.portfolio_optimizer.suggest_rebalancing(
                    current_positions, account_value
                )
                
                # Execute rebalancing if needed
                for action in rebalance_actions:
                    if action['action'] == 'reduce':
                        self.api.submit_order(
                            symbol=action['symbol'],
                            qty=action['shares'],
                            side='sell',
                            type='market',
                            time_in_force='day'
                        )
                        logger.info(f"Rebalancing: Reducing {action['symbol']} by {action['shares']} shares. Reason: {action['reason']}")
                
        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}")
            self.notifications.alert(f"Position monitoring error: {str(e)}", "ERROR")
            
    def tune_parameters(self):
        """Tune strategy parameters based on performance"""
        try:
            if not self.parameter_tuner:
                return
                
            # Check if tuning is due
            if not self.parameter_tuner.should_optimize():
                return
                
            # Get performance metrics
            if self.performance_analyzer:
                metrics = self.performance_analyzer.calculate_metrics()
            else:
                # Basic metrics if no analyzer
                metrics = {
                    'win_rate': self.win_count / (self.win_count + self.loss_count) if (self.win_count + self.loss_count) > 0 else 0.5,
                    'profit_factor': 1.5,  # Default
                    'sharpe_ratio': 1.0    # Default
                }
                
            # Detect market regime
            if self.strategy_allocator:
                # Use first symbol in watchlist for regime detection
                data = self.get_market_data(WATCHLIST[0], timeframe='1D', limit=100)
                market_regime = self.strategy_allocator.detect_market_condition(data)
            else:
                market_regime = 'unknown'
                
            # Tune parameters
            updated_params = self.parameter_tuner.tune_parameters(metrics, market_regime)
            
            # Update strategy parameters
            self.strategy.update_parameters(updated_params)
            
            logger.info(f"Parameters tuned based on performance. Market regime: {market_regime}")
            
        except Exception as e:
            logger.error(f"Error tuning parameters: {str(e)}") 