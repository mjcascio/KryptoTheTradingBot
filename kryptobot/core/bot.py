"""
Core Bot Module - Main orchestration for the KryptoBot trading system.

This module contains the main TradingBot class that coordinates all trading activities,
including market data fetching, strategy execution, risk management, and ML enhancement.
"""

import os
import time
import logging
import threading
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Any
import pytz
from functools import wraps

# Import from kryptobot modules
from kryptobot.data.market_data import MarketDataService
from kryptobot.trading.strategy import TradingStrategy
from kryptobot.risk.manager import RiskManager
from kryptobot.ml.enhancer import MLSignalEnhancer
from kryptobot.utils.notifications import NotificationSystem
from kryptobot.utils.sleep_manager import SleepManager
from kryptobot.brokers.factory import BrokerFactory
from kryptobot.brokers.base import BaseBroker

# Import configuration
from kryptobot.utils.config import (
    WATCHLIST, FOREX_WATCHLIST, MAX_TRADES_PER_DAY, MIN_SUCCESS_PROBABILITY,
    MAX_POSITION_SIZE_PCT, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    MAX_DAILY_LOSS_PCT, MARKET_OPEN, MARKET_CLOSE, TIMEZONE, PLATFORMS,
    SLEEP_MODE
)

# Configure logging
logger = logging.getLogger(__name__)

def retry_on_exception(retries=3, delay=5):
    """
    Decorator to retry a function on exception.
    
    Args:
        retries (int): Number of retries
        delay (int): Delay between retries in seconds
        
    Returns:
        Decorated function
    """
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
                        logger.error(f"Function {func.__name__} failed after {retries} attempts: {e}")
                        raise
                    logger.warning(f"Retry {attempts}/{retries} for {func.__name__} after error: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

class TradingBot:
    """
    Main trading bot class that orchestrates the trading system.
    
    This class coordinates all components of the trading system, including
    market data fetching, strategy execution, risk management, and ML enhancement.
    
    Attributes:
        strategies (TradingStrategy): Trading strategies
        dashboard (TradingDashboard): Trading dashboard
        notifications (NotificationSystem): Notification system
        market_data (MarketDataService): Market data service
        risk_manager (RiskManager): Risk management
        ml_enhancer (MLSignalEnhancer): ML signal enhancer
        sleep_manager (SleepManager): Sleep management
        broker (BaseBroker): Current active broker
        brokers (Dict[str, BaseBroker]): Available brokers
        active_platform (str): Current active platform
        running (bool): Whether the bot is running
        account_info (Dict[str, Any]): Account information
        positions (Dict[str, Any]): Current positions
        trades (List[Dict[str, Any]]): Recent trades
        market_data_cache (Dict[str, pd.DataFrame]): Cache of market data
        plugin_manager (PluginManager): Plugin manager for extensions
    """
    
    def __init__(self, strategies=None, dashboard=None, notifications=None, plugin_config_path=None):
        """
        Initialize the trading bot.
        
        Args:
            strategies (TradingStrategy, optional): Trading strategies
            dashboard (TradingDashboard, optional): Trading dashboard
            notifications (NotificationSystem, optional): Notification system
            plugin_config_path (str, optional): Path to the plugin configuration file
        """
        # Initialize components
        self.strategies = strategies or TradingStrategy()
        self.dashboard = dashboard
        self.notifications = notifications or NotificationSystem()
        
        # Initialize state
        self.running = False
        self.account_info = {}
        self.positions = {}
        self.trades = []
        self.market_data_cache = {}
        
        # Initialize brokers
        self.brokers = {}
        self.active_platform = None
        self._initialize_brokers()
        
        # Initialize services
        self.market_data = None
        self.risk_manager = RiskManager()
        self.ml_enhancer = MLSignalEnhancer()
        self.sleep_manager = SleepManager()
        
        # Initialize plugin system
        self.plugin_manager = None
        self._initialize_plugins(plugin_config_path)
        
        # Connect components
        if self.ml_enhancer:
            self.ml_enhancer.connect_to_bot(self)
        
        logger.info("Trading bot initialized")
    
    def _initialize_brokers(self):
        """
        Initialize brokers for all configured platforms.
        """
        broker_factory = BrokerFactory()
        
        for platform_id, platform_config in PLATFORMS.items():
            try:
                broker = broker_factory.create_broker(
                    platform_id,
                    platform_config.get('api_key'),
                    platform_config.get('api_secret'),
                    platform_config.get('base_url')
                )
                self.brokers[platform_id] = broker
                
                # Set the first broker as active by default
                if self.active_platform is None:
                    self.active_platform = platform_id
                    self.broker = broker
                    self.market_data = MarketDataService(broker)
                
                logger.info(f"Initialized broker for platform: {platform_id}")
            except Exception as e:
                logger.error(f"Failed to initialize broker for platform {platform_id}: {e}")
        
        if not self.brokers:
            raise ValueError("No brokers could be initialized")
    
    def _get_platform_watchlist(self) -> List[str]:
        """
        Get the watchlist for the current platform.
        
        Returns:
            List[str]: List of symbols to watch
        """
        if self.active_platform == 'metatrader':
            return FOREX_WATCHLIST
        return WATCHLIST
    
    def connect(self) -> bool:
        """
        Connect to the trading platform.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.broker and self.broker.connect():
                self._update_account_info()
                logger.info(f"Connected to platform: {self.active_platform}")
                
                if self.notifications:
                    self.notifications.send_notification(
                        f"Connected to {self.active_platform}",
                        f"Trading bot connected to {self.active_platform} platform"
                    )
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error connecting to platform: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the trading platform.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        return self.broker.disconnect() if self.broker else False
    
    def switch_platform(self, platform_id: str) -> bool:
        """
        Switch to a different trading platform.
        
        Args:
            platform_id (str): Platform ID to switch to
            
        Returns:
            bool: True if switch successful, False otherwise
        """
        if platform_id not in self.brokers:
            logger.error(f"Platform {platform_id} not available")
            return False
        
        try:
            # Disconnect from current platform
            if self.broker:
                self.disconnect()
            
            # Switch to new platform
            self.active_platform = platform_id
            self.broker = self.brokers[platform_id]
            self.market_data = MarketDataService(self.broker)
            
            # Connect to new platform
            success = self.connect()
            
            if success:
                logger.info(f"Switched to platform: {platform_id}")
                
                if self.notifications:
                    self.notifications.send_notification(
                        f"Switched to {platform_id}",
                        f"Trading bot switched to {platform_id} platform"
                    )
                
                # Update dashboard if available
                if self.dashboard:
                    self.dashboard.update_platform(platform_id)
            
            return success
        except Exception as e:
            logger.error(f"Error switching to platform {platform_id}: {e}")
            return False
    
    def get_active_platform(self) -> str:
        """
        Get the current active platform.
        
        Returns:
            str: Active platform ID
        """
        return self.active_platform
    
    def get_available_platforms(self) -> List[Dict[str, Any]]:
        """
        Get a list of available platforms.
        
        Returns:
            List[Dict[str, Any]]: List of platform information
        """
        platforms = []
        for platform_id, platform_config in PLATFORMS.items():
            platforms.append({
                'id': platform_id,
                'name': platform_config.get('name', platform_id),
                'type': platform_config.get('type', 'unknown'),
                'description': platform_config.get('description', ''),
                'icon': platform_config.get('icon', 'fa-chart-line'),
                'active': platform_id == self.active_platform
            })
        return platforms
    
    def _update_account_info(self):
        """
        Update account information from the broker.
        """
        try:
            # Get the active broker
            broker = self.brokers.get(self.active_platform)
            if not broker:
                logger.error("No active broker available")
                return
            
            # Get account information
            old_account_info = self.account_info.copy()
            self.account_info = broker.get_account_info()
            
            # Log account information
            if self.account_info:
                equity = self.account_info.get('equity', 0.0)
                buying_power = self.account_info.get('buying_power', 0.0)
                logger.info(f"Updated account info: Equity=${equity}, Buying Power=${buying_power}")
            
            # Record account changes in the blockchain audit trail if available
            if self.plugin_manager and "plugins.blockchain_audit" in self.plugin_manager.plugins:
                # Check if there are significant changes
                if old_account_info and self.account_info:
                    old_equity = old_account_info.get('equity', 0.0)
                    new_equity = self.account_info.get('equity', 0.0)
                    
                    # Record if equity changed by more than 0.1%
                    if abs(new_equity - old_equity) / old_equity > 0.001:
                        audit_plugin = self.plugin_manager.plugins["plugins.blockchain_audit"]
                        change_data = {
                            "component": "account",
                            "change_type": "equity_update",
                            "old_value": old_equity,
                            "new_value": new_equity,
                            "timestamp": datetime.now().isoformat()
                        }
                        audit_plugin.execute({
                            "action": "record_system_change",
                            "change_data": change_data
                        })
        
        except Exception as e:
            logger.error(f"Error updating account info: {e}")
    
    def start(self):
        """
        Start the trading bot.
        """
        if self.running:
            logger.warning("Trading bot is already running")
            return
        
        logger.info("Starting trading bot")
        
        try:
            # Connect to the platform
            if not self.connect():
                logger.error("Failed to connect to platform")
                return
            
            # Start the trading loop
            self.running = True
            self.run()
            
            logger.info("Trading bot started")
            
            if self.notifications:
                self.notifications.send_notification(
                    "Trading Bot Started",
                    f"Trading bot started on {self.active_platform} platform"
                )
        
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            self.running = False
    
    def stop(self):
        """
        Stop the trading bot.
        """
        if not self.running:
            logger.warning("Trading bot is not running")
            return
        
        logger.info("Stopping trading bot")
        
        try:
            # Stop the trading loop
            self.running = False
            
            # Disconnect from the platform
            self.disconnect()
            
            logger.info("Trading bot stopped")
            
            if self.notifications:
                self.notifications.send_notification(
                    "Trading Bot Stopped",
                    "Trading bot has been stopped"
                )
        
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")
    
    def run(self):
        """
        Run the trading bot.
        
        This method starts the main trading loop in a separate thread.
        """
        def trading_loop():
            """
            Main trading loop.
            """
            while self.running:
                try:
                    # Check if the bot should be sleeping
                    self._update_sleep_status()
                    if self.sleep_manager.is_sleeping():
                        logger.info(f"Bot is sleeping: {self.sleep_manager.get_reason()}")
                        time.sleep(60)  # Check every minute
                        continue
                    
                    # Update market data
                    self._update_market_data()
                    
                    # Check existing positions
                    self._check_positions()
                    
                    # Scan for new opportunities
                    self._scan_for_opportunities()
                    
                    # Update account info
                    self._update_account_info()
                    
                    # Sleep for a bit to avoid API rate limits
                    time.sleep(10)
                
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    time.sleep(60)  # Sleep for a minute on error
        
        # Start the trading loop in a separate thread
        thread = threading.Thread(target=trading_loop)
        thread.daemon = True
        thread.start()
    
    def _update_sleep_status(self):
        """
        Update the sleep status of the bot.
        """
        try:
            # Check market hours
            is_market_open = self.market_data.check_market_hours()
            next_open, next_close = self.market_data.get_next_market_times()
            
            # Update sleep manager
            self.sleep_manager.update(is_market_open, next_open, next_close)
            
            # Update dashboard if available
            if self.dashboard:
                self.dashboard.update_sleep_status({
                    'is_sleeping': self.sleep_manager.is_sleeping(),
                    'reason': self.sleep_manager.get_reason(),
                    'next_wake_time': self.sleep_manager.get_next_wake_time()
                })
        
        except Exception as e:
            logger.error(f"Error updating sleep status: {e}")
    
    def _update_market_data(self):
        """
        Update market data for all symbols in the watchlist.
        """
        try:
            watchlist = self._get_platform_watchlist()
            
            for symbol in watchlist:
                # Get market data
                data = self.market_data.get_market_data(symbol)
                
                if data is not None and not data.empty:
                    self.market_data_cache[symbol] = data
                    logger.debug(f"Updated market data for {symbol}")
        
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    def _check_positions(self):
        """
        Check and manage existing positions.
        """
        try:
            if not self.broker:
                logger.warning("No broker available to check positions")
                return
            
            positions = self.broker.get_positions()
            
            for position in positions:
                symbol = position.get('symbol')
                quantity = position.get('quantity', 0.0)
                entry_price = position.get('entry_price', 0.0)
                current_price = position.get('current_price', 0.0)
                
                if not symbol or quantity == 0:
                    continue
                
                # Check if we need to update stop loss or take profit
                stop_loss = position.get('stop_loss')
                take_profit = position.get('take_profit')
                
                # Calculate dynamic stop loss and take profit if not set
                if stop_loss is None or take_profit is None:
                    # Get market data for the symbol
                    data = self.market_data_cache.get(symbol)
                    
                    if data is not None and not data.empty:
                        # Calculate ATR-based stop loss and take profit
                        atr = self.strategies.calculate_atr(data)
                        
                        if atr > 0:
                            # Dynamic stop loss: 2 ATR below entry for long, 2 ATR above entry for short
                            if stop_loss is None:
                                if quantity > 0:  # Long position
                                    stop_loss = entry_price - (2 * atr)
                                else:  # Short position
                                    stop_loss = entry_price + (2 * atr)
                            
                            # Dynamic take profit: 3 ATR above entry for long, 3 ATR below entry for short
                            if take_profit is None:
                                if quantity > 0:  # Long position
                                    take_profit = entry_price + (3 * atr)
                                else:  # Short position
                                    take_profit = entry_price - (3 * atr)
                    
                    # If we calculated new values, update them
                    if stop_loss is not None or take_profit is not None:
                        self.broker.update_position(
                            symbol,
                            stop_loss=stop_loss,
                            take_profit=take_profit
                        )
                        logger.info(f"Updated position for {symbol}: stop_loss={stop_loss}, take_profit={take_profit}")
            
            # Update positions in the bot state
            self._update_account_info()
        
        except Exception as e:
            logger.error(f"Error checking positions: {e}")
    
    def _scan_for_opportunities(self):
        """
        Scan for trading opportunities.
        """
        try:
            # Check if we can trade today
            if not self.market_data.check_market_hours():
                logger.info("Market is closed, skipping opportunity scan")
                return
            
            # Check if we've reached the maximum number of trades for the day
            if len(self.trades) >= MAX_TRADES_PER_DAY:
                logger.info(f"Reached maximum trades for the day ({MAX_TRADES_PER_DAY})")
                return
            
            # Get the watchlist for the current platform
            watchlist = self._get_platform_watchlist()
            
            # Prepare market data for anomaly detection
            market_data = {}
            for symbol in watchlist:
                data = self.market_data_cache.get(symbol)
                if data is not None and not data.empty:
                    market_data[symbol] = data
            
            # Detect market anomalies if the plugin is available
            anomalies = {}
            if self.plugin_manager:
                try:
                    # Execute anomaly detection plugins
                    anomaly_data = {
                        'market_data': market_data
                    }
                    anomaly_results = self.plugin_manager.execute_plugins_by_category('analysis', anomaly_data)
                    
                    # Process anomaly detection results
                    for result in anomaly_results:
                        if 'results' in result:
                            for symbol, anomaly_data in result['results'].items():
                                if anomaly_data.get('anomalies_detected', False):
                                    anomalies[symbol] = anomaly_data
                    
                    if anomalies:
                        logger.info(f"Detected anomalies in {len(anomalies)} symbols")
                        for symbol, anomaly_data in anomalies.items():
                            logger.info(f"  {symbol}: {anomaly_data.get('anomaly_type', 'unknown')} anomaly (score: {anomaly_data.get('anomaly_score', 0.0):.2f})")
                
                except Exception as e:
                    logger.error(f"Error detecting market anomalies: {e}")
            
            for symbol in watchlist:
                # Skip if we already have a position in this symbol
                if symbol in self.positions:
                    continue
                
                # Get market data
                data = self.market_data_cache.get(symbol)
                
                if data is None or data.empty:
                    continue
                
                # Generate trading signals
                signal = self.strategies.generate_signal(symbol, data)
                
                # Enhance signal with ML if available
                if self.ml_enhancer and signal.get('action') != 'hold':
                    enhanced_signal = self.ml_enhancer.enhance_signal(data, signal)
                    
                    # Only use the enhanced signal if it meets our confidence threshold
                    if enhanced_signal.get('confidence', 0.0) >= MIN_SUCCESS_PROBABILITY:
                        signal = enhanced_signal
                    else:
                        # Skip this opportunity if confidence is too low
                        continue
                
                # Adjust signal based on detected anomalies
                if symbol in anomalies:
                    anomaly_data = anomalies[symbol]
                    anomaly_score = anomaly_data.get('anomaly_score', 0.0)
                    anomaly_type = anomaly_data.get('anomaly_type', 'unknown')
                    
                    # Adjust signal strength based on anomaly type
                    if anomaly_type == 'extreme':
                        # For extreme anomalies, we might want to be more cautious
                        if signal.get('action') == 'buy':
                            logger.info(f"Reducing buy signal strength for {symbol} due to extreme anomaly")
                            signal['strength'] = signal.get('strength', 1.0) * 0.5
                        elif signal.get('action') == 'sell':
                            logger.info(f"Increasing sell signal strength for {symbol} due to extreme anomaly")
                            signal['strength'] = signal.get('strength', 1.0) * 1.5
                    elif anomaly_type == 'significant':
                        # For significant anomalies, we might want to adjust slightly
                        if signal.get('action') == 'buy':
                            logger.info(f"Adjusting buy signal strength for {symbol} due to significant anomaly")
                            signal['strength'] = signal.get('strength', 1.0) * 0.8
                        elif signal.get('action') == 'sell':
                            logger.info(f"Adjusting sell signal strength for {symbol} due to significant anomaly")
                            signal['strength'] = signal.get('strength', 1.0) * 1.2
                
                # Execute the signal if it's not a hold
                if signal.get('action') != 'hold':
                    # Calculate position size
                    equity = self.account_info.get('equity', 0.0)
                    position_size = self._calculate_position_size(symbol, equity)
                    
                    if position_size > 0:
                        # Place the order
                        self._place_order(
                            symbol,
                            position_size,
                            signal.get('action'),
                            signal.get('strategy', 'unknown'),
                            signal
                        )
            
            # Use plugins to enhance trading signals if available
            if self.plugin_manager:
                try:
                    # Execute sentiment analysis plugins
                    sentiment_data = {
                        'symbols': watchlist,
                        'timeframe': '1d'
                    }
                    sentiment_results = self.plugin_manager.execute_plugins_by_category('analysis', sentiment_data)
                    
                    # Incorporate sentiment results into trading signals
                    if sentiment_results:
                        for result in sentiment_results:
                            if 'results' in result:
                                for symbol, sentiment in result['results'].items():
                                    if symbol in watchlist:
                                        # Adjust signal strength based on sentiment
                                        if sentiment['sentiment'] == 'bullish':
                                            signal = self.market_data_cache[symbol].iloc[-1]
                                            signal['strength'] = 1.2
                                        elif sentiment['sentiment'] == 'bearish':
                                            signal = self.market_data_cache[symbol].iloc[-1]
                                            signal['strength'] = 0.8
                    
                    logger.info(f"Enhanced trading signals with {len(sentiment_results)} plugin results")
                
                except Exception as e:
                    logger.error(f"Error executing plugins: {e}")
        
        except Exception as e:
            logger.error(f"Error scanning for opportunities: {e}")
    
    def _calculate_position_size(self, symbol: str, equity: float) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            symbol (str): Trading symbol
            equity (float): Account equity
            
        Returns:
            float: Position size
        """
        try:
            # Get market data
            data = self.market_data_cache.get(symbol)
            
            if data is None or data.empty:
                return 0.0
            
            # Calculate ATR for volatility-based position sizing
            atr = self.strategies.calculate_atr(data)
            
            if atr <= 0:
                return 0.0
            
            # Calculate position size based on risk
            risk_amount = equity * MAX_POSITION_SIZE_PCT
            
            # Adjust for volatility
            volatility_factor = 1.0
            
            # Use optimized parameters if available
            if self.plugin_manager:
                try:
                    # Check if we have optimized parameters for this symbol
                    optimized_params = self._get_optimized_parameters(symbol)
                    
                    if optimized_params:
                        logger.info(f"Using optimized parameters for {symbol}: {optimized_params}")
                        
                        # Adjust position size based on optimized parameters
                        if 'position_size_factor' in optimized_params:
                            volatility_factor = optimized_params['position_size_factor']
                
                except Exception as e:
                    logger.error(f"Error getting optimized parameters: {e}")
            
            # Calculate final position size
            position_size = risk_amount / (atr * volatility_factor)
            
            # Apply position size limits
            max_position_size = equity * MAX_POSITION_SIZE_PCT
            position_size = min(position_size, max_position_size)
            
            return position_size
        
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
    
    def _get_optimized_parameters(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get optimized parameters for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Optional[Dict[str, Any]]: Optimized parameters, or None if not available
        """
        if not self.plugin_manager:
            return None
        
        try:
            # Execute parameter tuner plugin
            result = self.plugin_manager.execute_plugin('parameter_tuner', {
                'strategy_name': f"{symbol}_strategy",
                'get_best_params': True
            })
            
            if result and 'best_params' in result:
                return result['best_params']
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting optimized parameters for {symbol}: {e}")
            return None
    
    def optimize_strategy_parameters(self, strategy_name: str, parameter_space: Dict[str, Any], 
                                    optimization_method: str = 'quantum_pso') -> Optional[Dict[str, Any]]:
        """
        Optimize strategy parameters.
        
        Args:
            strategy_name (str): Name of the strategy to optimize
            parameter_space (Dict[str, Any]): Parameter space to search
            optimization_method (str, optional): Optimization method to use
            
        Returns:
            Optional[Dict[str, Any]]: Optimization results, or None if optimization failed
        """
        if not self.plugin_manager:
            logger.warning("Plugin manager not available for parameter optimization")
            return None
        
        try:
            # Get historical data for backtesting
            symbols = self._get_platform_watchlist()
            
            if not symbols:
                logger.warning("No symbols available for parameter optimization")
                return None
            
            # Prepare market data for backtesting
            market_data = {}
            for symbol in symbols:
                data = self.market_data.get_market_data(symbol, timeframe='1d', limit=500)
                if data is not None and not data.empty:
                    market_data[symbol] = data
            
            if not market_data:
                logger.warning("No market data available for parameter optimization")
                return None
            
            # Define objective function for parameter optimization
            def objective_function(params):
                # Backtest the strategy with the given parameters
                return self.strategies.backtest_strategy(strategy_name, params, market_data)
            
            # Execute parameter tuner plugin
            result = self.plugin_manager.execute_plugin('parameter_tuner', {
                'strategy_name': strategy_name,
                'parameter_space': parameter_space,
                'objective_function': objective_function,
                'optimization_method': optimization_method
            })
            
            if result:
                logger.info(f"Optimized parameters for {strategy_name}: {result.get('best_params')}")
                logger.info(f"Best score: {result.get('best_score')}")
                
                return result
            
            return None
        
        except Exception as e:
            logger.error(f"Error optimizing strategy parameters: {e}")
            return None
    
    def _place_order(self, symbol: str, quantity: float, side: str, strategy: str, signal: Dict[str, Any]) -> bool:
        """
        Place an order with the broker.
        
        Args:
            symbol (str): Symbol to trade
            quantity (float): Quantity to trade
            side (str): Order side (buy/sell)
            strategy (str): Strategy that generated the signal
            signal (Dict[str, Any]): Trading signal
            
        Returns:
            bool: True if order was placed successfully, False otherwise
        """
        try:
            # Get the active broker
            broker = self.brokers.get(self.active_platform)
            if not broker:
                logger.error("No active broker available")
                return False
            
            # Calculate stop loss and take profit levels
            current_price = broker.get_current_price(symbol)
            if not current_price:
                logger.error(f"Could not get current price for {symbol}")
                return False
            
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(
                symbol, current_price, side
            )
            
            # Place the order
            order_id = broker.place_order(
                symbol=symbol,
                quantity=quantity,
                side=side,
                order_type="market",
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if not order_id:
                logger.error(f"Failed to place {side} order for {symbol}")
                return False
            
            # Log the order
            logger.info(
                f"Placed {side} order for {quantity} {symbol} at {current_price} "
                f"(stop loss: {stop_loss}, take profit: {take_profit})"
            )
            
            # Record the order in the blockchain audit trail if available
            if self.plugin_manager and "plugins.blockchain_audit" in self.plugin_manager.plugins:
                audit_plugin = self.plugin_manager.plugins["plugins.blockchain_audit"]
                order_data = {
                    "id": order_id,
                    "symbol": symbol,
                    "quantity": quantity,
                    "side": side,
                    "price": current_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "strategy": strategy,
                    "timestamp": datetime.now().isoformat()
                }
                audit_plugin.execute({
                    "action": "record_order",
                    "order_data": order_data
                })
            
            return True
        
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the trading bot.
        
        Returns:
            Dict[str, Any]: Bot status
        """
        return {
            'running': self.running,
            'platform': self.active_platform,
            'account': self.account_info,
            'positions': self.positions,
            'trades': self.trades,
            'sleep_status': {
                'is_sleeping': self.sleep_manager.is_sleeping(),
                'reason': self.sleep_manager.get_reason(),
                'next_wake_time': self.sleep_manager.get_next_wake_time()
            },
            'market_status': {
                'is_open': self.market_data.check_market_hours() if self.market_data else False,
                'next_open': self.market_data.get_next_market_times()[0] if self.market_data else None,
                'next_close': self.market_data.get_next_market_times()[1] if self.market_data else None
            }
        }

    def _initialize_plugins(self, plugin_config_path=None):
        """
        Initialize the plugin system.
        
        Args:
            plugin_config_path (str, optional): Path to the plugin configuration file
        """
        try:
            from kryptobot.utils.plugin_manager import PluginManager
            
            # Use default config path if not provided
            if plugin_config_path is None:
                plugin_config_path = os.path.join('config', 'plugins.yaml')
            
            # Initialize plugin manager
            self.plugin_manager = PluginManager(
                plugin_directories=['plugins'],
                config_path=plugin_config_path
            )
            
            # Discover and load enabled plugins
            self.plugin_manager.discover_plugins()
            loaded_count = self.plugin_manager.load_plugins()
            
            logger.info(f"Loaded {loaded_count} plugins")
            
            # Record system startup in blockchain audit trail if available
            if self.plugin_manager and "plugins.blockchain_audit" in self.plugin_manager.plugins:
                audit_plugin = self.plugin_manager.plugins["plugins.blockchain_audit"]
                change_data = {
                    "component": "trading_bot",
                    "change_type": "system_startup",
                    "details": {
                        "version": "1.0.0",
                        "platform": self.active_platform
                    },
                    "timestamp": datetime.now().isoformat()
                }
                audit_plugin.execute({
                    "action": "record_system_change",
                    "change_data": change_data
                })
        
        except ImportError:
            logger.warning("Plugin manager not available")
            self.plugin_manager = None
        
        except Exception as e:
            logger.error(f"Error initializing plugin system: {e}")
            self.plugin_manager = None

    def shutdown(self):
        """
        Shutdown the trading bot.
        """
        try:
            logger.info("Shutting down trading bot")
            
            # Stop running
            self.running = False
            
            # Record system shutdown in blockchain audit trail if available
            if self.plugin_manager and "plugins.blockchain_audit" in self.plugin_manager.plugins:
                audit_plugin = self.plugin_manager.plugins["plugins.blockchain_audit"]
                change_data = {
                    "component": "trading_bot",
                    "change_type": "system_shutdown",
                    "details": {
                        "reason": "user_initiated"
                    },
                    "timestamp": datetime.now().isoformat()
                }
                audit_plugin.execute({
                    "action": "record_system_change",
                    "change_data": change_data
                })
            
            # Shutdown plugins
            if self.plugin_manager:
                for plugin_name, plugin in self.plugin_manager.plugins.items():
                    try:
                        plugin.shutdown()
                    except Exception as e:
                        logger.error(f"Error shutting down plugin {plugin_name}: {e}")
            
            # Disconnect from brokers
            for platform, broker in self.brokers.items():
                try:
                    broker.disconnect()
                    logger.info(f"Disconnected from {platform}")
                except Exception as e:
                    logger.error(f"Error disconnecting from {platform}: {e}")
            
            logger.info("Trading bot shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during trading bot shutdown: {e}")

    def _handle_trade_execution(self, trade_data: Dict[str, Any]) -> None:
        """
        Handle a trade execution.
        
        Args:
            trade_data (Dict[str, Any]): Trade execution data
        """
        try:
            # Extract trade information
            symbol = trade_data.get('symbol')
            side = trade_data.get('side')
            quantity = trade_data.get('quantity')
            price = trade_data.get('price')
            
            if not all([symbol, side, quantity, price]):
                logger.error(f"Invalid trade data: {trade_data}")
                return
            
            # Log the trade
            logger.info(
                f"Trade executed: {side} {quantity} {symbol} at {price}"
            )
            
            # Update positions
            self._update_positions()
            
            # Update account information
            self._update_account_info()
            
            # Record the trade in the blockchain audit trail if available
            if self.plugin_manager and "plugins.blockchain_audit" in self.plugin_manager.plugins:
                audit_plugin = self.plugin_manager.plugins["plugins.blockchain_audit"]
                audit_plugin.execute({
                    "action": "record_trade",
                    "trade_data": trade_data
                })
        
        except Exception as e:
            logger.error(f"Error handling trade execution: {e}") 