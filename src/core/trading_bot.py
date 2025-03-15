#!/usr/bin/env python3
"""
Core trading bot implementation with support for stocks and options trading.
Implements a modular design with proper error handling and logging.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import pytz
from dotenv import load_dotenv

from ..monitoring.logging.logger import get_logger
from ..utils.decorators import retry_on_exception
from ..integrations.brokers import BrokerFactory
from ..strategies.manager import StrategyManager
from ..monitoring.system import SystemMonitor, MetricsConfig
from ..data.market_data import MarketDataService
from ..utils.config import Config
from ..integrations.telegram import TelegramNotifier
from .position_manager import PositionManager
from ..utils.pid_manager import PIDManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.out'),
        logging.StreamHandler()
    ]
)
logger = get_logger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Load environment variables
load_dotenv()


class TradingBot:
    """
    Trading bot that implements various trading strategies for both stocks and options.
    Provides a unified interface for trading operations with proper error handling
    and monitoring.
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the trading bot.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_path)
        if not self.config.validate():
            raise ValueError("Invalid configuration")
            
        # Initialize components
        self._init_core_components()
        self._init_trading_state()
        self._init_monitoring()
        
        logger.info("Trading bot initialized")
        
    def _init_core_components(self) -> None:
        """Initialize core trading components."""
        try:
            # Initialize broker factory and connect to default broker
            self.broker_factory = BrokerFactory()
            self._initialize_brokers()
            
            # Initialize market data service
            active_broker = self.broker_factory.get_active_broker()
            if active_broker:
                self.market_data = MarketDataService(active_broker, self.config)
            else:
                raise RuntimeError("No active broker available")
            
            # Initialize position manager
            self.position_manager = PositionManager(self.config)
            
            # Load watchlist
            self.watchlist = self._get_platform_watchlist()
            
        except Exception as e:
            logger.error(f"Failed to initialize core components: {str(e)}", exc_info=True)
            raise
    
    def _init_trading_state(self) -> None:
        """Initialize trading state variables."""
        self.is_running = False
        self.stop_event = threading.Event()
        self.trading_thread = None
        
        # Initialize trading metrics
        self.positions = {'stocks': {}, 'options': {}}
        self.daily_trades = {'stocks': 0, 'options': 0}
        self.daily_pl = {'stocks': 0.0, 'options': 0.0}
        self.orders = {'stocks': {}, 'options': {}}
    
    def _init_monitoring(self) -> None:
        """Initialize monitoring components."""
        try:
            # Initialize system monitor
            metrics_config = MetricsConfig(
                collection_interval=self.config.get('monitoring.metrics_interval', 60),
                retention_days=self.config.get('monitoring.metrics_retention_days', 30)
            )
            self.system_monitor = SystemMonitor(metrics_config)
            
            # Initialize Telegram notifier if enabled
            if self.config.get('monitoring.telegram_enabled', False):
                self.telegram_notifier = TelegramNotifier(self.config)
            else:
                self.telegram_notifier = None
                
            logger.info("Monitoring components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {str(e)}", exc_info=True)
            raise
    
    def _initialize_brokers(self) -> None:
        """Initialize brokers based on configuration."""
        try:
            platforms = self.config.get('platforms', {})
            default_broker = None
            
            # Create broker instances for enabled platforms
            for platform_id, platform_config in platforms.items():
                if platform_config.get('enabled', False) or platform_id == 'alpaca':
                    broker = self.broker_factory.create(platform_id, platform_config)
                    if broker:
                        if platform_id == 'alpaca' or platform_config.get('default', False):
                            default_broker = platform_id
                            logger.info(f"Created {platform_id} broker instance (default)")
                        else:
                            logger.info(f"Created {platform_id} broker instance")
            
            # Set and connect to the default broker
            active_broker_id = default_broker or 'alpaca'
            self.broker_factory.set_active_broker(active_broker_id)
            
            active_broker = self.broker_factory.get_active_broker()
            if active_broker and active_broker.connect():
                logger.info(f"Successfully connected to {active_broker.get_platform_name()}")
            else:
                raise RuntimeError(f"Failed to connect to {active_broker_id}")
                
        except Exception as e:
            logger.error(f"Failed to initialize brokers: {str(e)}", exc_info=True)
            raise
    
    def _get_platform_watchlist(self) -> List[str]:
        """Get the watchlist for the active platform."""
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker:
                logger.warning("No active broker. Using default stock watchlist.")
                return self.config.get('watchlists.stocks', [])
            
            platform_type = active_broker.get_platform_type()
            if platform_type == 'forex':
                return self.config.get('watchlists.forex', [])
            else:
                return self.config.get('watchlists.stocks', [])
                
        except Exception as e:
            logger.error(f"Failed to get platform watchlist: {str(e)}", exc_info=True)
            return []
    
    @retry_on_exception(max_retries=3, delay=5)
    def connect(self) -> bool:
        """
        Connect to all enabled brokers.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Connect all brokers and check results
            broker_results = self.broker_factory.connect_all_brokers()
            if not all(broker_results.values()):
                logger.error("Some brokers failed to connect")
                return False
            
            # Check if the active broker is connected
            active_broker = self.broker_factory.get_active_broker()
            if active_broker and active_broker.connected:
                # Initialize market data service
                self.market_data = MarketDataService(active_broker)
                self.watchlist = self._get_platform_watchlist()
                
                # Notify successful connection
                if self.telegram_notifier:
                    self.telegram_notifier.send_message(
                        f"Connected to {active_broker.get_platform_name()}"
                    )
                return True
            
            logger.error("Failed to connect to the active broker")
            return False
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}", exc_info=True)
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from all brokers.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            return all(self.broker_factory.disconnect_all_brokers().values())
        except Exception as e:
            logger.error(f"Disconnection error: {str(e)}", exc_info=True)
            return False
    
    def start(self) -> bool:
        """
        Start the trading bot.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            # Check if bot is already running
            is_running, pid = self.pid_manager.check_pid()
            if is_running:
                logger.warning(f"Trading bot is already running (PID: {pid})")
                return False
            
            # Clean up any stale PID file
            self.pid_manager.cleanup_stale()
            
            # Create new PID file
            if not self.pid_manager.create_pid(os.getpid()):
                logger.error("Failed to create PID file")
                return False
            
            # Start trading thread
            self.stop_event.clear()
            self.trading_thread = threading.Thread(target=self._trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            
            # Start system monitoring
            self.system_monitor.start()
            
            self.is_running = True
            
            # Send notification
            if self.telegram_notifier:
                self.telegram_notifier.send_message("Trading bot started")
            
            logger.info(f"Trading bot started (PID: {os.getpid()})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start trading bot: {str(e)}")
            self.pid_manager.remove_pid()
            return False
    
    def stop(self) -> bool:
        """
        Stop the trading bot.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping trading bot...")
            self.stop_event.set()
            
            if hasattr(self, 'trading_thread'):
                self.trading_thread.join(timeout=30)
            
            # Stop system monitoring
            self.system_monitor.stop()
            
            # Cleanup
            self.position_manager.close_all_positions()
            self.market_data.disconnect()
            self.pid_manager.remove_pid()
            
            self.is_running = False
            
            # Send notification
            if self.telegram_notifier:
                self.telegram_notifier.send_message("Trading bot stopped")
            
            logger.info("Trading bot stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping trading bot: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the trading bot.
        
        Returns:
            Dict containing the current status information
        """
        try:
            active_broker = self.broker_factory.get_active_broker()
            performance = self.position_manager.get_performance()
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'uptime': self.system_monitor.get_uptime(),
                'active_platform': active_broker.get_platform_name() if active_broker else None,
                'positions': self.position_manager.positions,
                'daily_trades': self.position_manager.daily_trades,
                'daily_pl': self.position_manager.daily_pl,
                'system_metrics': self.system_monitor.get_current_metrics(),
                'performance': performance,
                'last_update': datetime.now(pytz.UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'last_update': datetime.now(pytz.UTC).isoformat()
            }
    
    def _trading_loop(self) -> None:
        """Main trading loop."""
        try:
            while not self.stop_event.is_set():
                try:
                    # Update system metrics
                    self.system_monitor.update_metrics()
                    
                    # Process trading strategies
                    self.strategy_manager.process_strategies(
                        self.market_data,
                        self.position_manager.positions
                    )
                    
                    # Monitor positions
                    self.position_manager.monitor_positions()
                    
                    # Reset daily metrics if needed
                    self.position_manager.reset_daily_metrics()
                    
                    # Sleep for the configured interval
                    self.stop_event.wait(
                        self.config.get('trading.update_interval', 60)
                    )
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {str(e)}", exc_info=True)
                    if self.telegram_notifier:
                        self.telegram_notifier.send_message(
                            f"Trading error: {str(e)}"
                        )
                    # Sleep before retrying
                    self.stop_event.wait(
                        self.config.get('trading.error_retry_interval', 300)
                    )
            
        except Exception as e:
            logger.critical(f"Fatal error in trading loop: {str(e)}", exc_info=True)
            if self.telegram_notifier:
                self.telegram_notifier.send_message(
                    f"Fatal trading error: {str(e)}"
                )
            self.stop()
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        return self.position_manager.get_positions()
    
    def get_recent_trades(self) -> List[Dict[str, Any]]:
        """Get recent trades."""
        return self.position_manager.get_recent_trades()
    
    def get_performance(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.position_manager.get_performance()
    
    def check_api_connection(self) -> bool:
        """Check if API connection is working
        
        Returns:
            bool: True if connection is working
        """
        return self.broker_factory.check_connection()
    
    def check_market_data(self) -> bool:
        """Check if market data is available
        
        Returns:
            bool: True if market data is available
        """
        return self.market_data.check_connection()
    
    def start_stock_trading(self) -> bool:
        """Start stock trading
        
        Returns:
            bool: True if started successfully
        """
        if "stocks" not in self.strategies:
            self.strategies.append("stocks")
            logger.info("Stock trading enabled")
            return True
        return False
    
    def stop_stock_trading(self) -> bool:
        """Stop stock trading
        
        Returns:
            bool: True if stopped successfully
        """
        if "stocks" in self.strategies:
            self.strategies.remove("stocks")
            logger.info("Stock trading disabled")
            return True
        return False
    
    def start_options_trading(self) -> bool:
        """Start options trading
        
        Returns:
            bool: True if started successfully
        """
        if "options" not in self.strategies:
            self.strategies.append("options")
            logger.info("Options trading enabled")
            return True
        return False
    
    def stop_options_trading(self) -> bool:
        """Stop options trading
        
        Returns:
            bool: True if stopped successfully
        """
        if "options" in self.strategies:
            self.strategies.remove("options")
            logger.info("Options trading disabled")
            return True
        return False

    def add_to_watchlist(self, symbol: str) -> bool:
        """Add a symbol to the watchlist
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            bool: True if added successfully
        """
        try:
            if symbol not in self.watchlist:
                self.watchlist.append(symbol)
                logger.info(f"Added {symbol} to watchlist")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding symbol to watchlist: {e}")
            return False

    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove a symbol from the watchlist
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            bool: True if removed successfully
        """
        try:
            if symbol in self.watchlist:
                self.watchlist.remove(symbol)
                logger.info(f"Removed {symbol} from watchlist")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing symbol from watchlist: {e}")
            return False 