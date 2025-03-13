"""Main entry point for KryptoBot Trading System."""

import asyncio
import logging
import os
import sys
import certifi
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

from utils.logging import setup_logging
from utils.database_pool import DatabasePool
from utils.api_security import APISecurityConfig, APISecurityManager
from utils.error_handling import ErrorHandler
from utils.monitoring import MetricsConfig, SystemMonitor
from trading.bot import TradingBot
from ml_enhancer import MLSignalEnhancer
from strategy_allocator import StrategyAllocator
from portfolio_optimizer import PortfolioOptimizer
from performance_analyzer import PerformanceAnalyzer
from parameter_tuner import AdaptiveParameterTuner
from config import BREAKOUT_PARAMS, TREND_PARAMS, PLATFORMS
from brokers import BrokerFactory

# Load environment variables
load_dotenv()

# Set SSL certificate path
ssl_cert_file = os.getenv('SSL_CERT_FILE', certifi.where())
requests_ca_bundle = os.getenv('REQUESTS_CA_BUNDLE', certifi.where())
os.environ['SSL_CERT_FILE'] = ssl_cert_file
os.environ['REQUESTS_CA_BUNDLE'] = requests_ca_bundle

# Apply timezone localization patch
try:
    import fix_timezone
    logging.info("Successfully imported fix_timezone module")
except ImportError:
    print("Warning: Could not import fix_timezone module")
    # Apply the patch directly
    import pandas as pd
    if hasattr(pd.Timestamp, 'tz_localize'):
        original_tz_localize = pd.Timestamp.tz_localize
        
        def patched_tz_localize(self, tz=None, ambiguous='raise', nonexistent='raise'):
            """Patched version of tz_localize that handles None timezone correctly."""
            if tz is None:
                return self
            return original_tz_localize(self, tz, ambiguous, nonexistent)
        
        pd.Timestamp.tz_localize = patched_tz_localize
        print("Applied pandas Timestamp.tz_localize patch directly")


# Import watchlist patch
try:
    import watchlist_patch
    logging.info("Successfully imported watchlist patch")
except ImportError:
    logging.warning("Could not import watchlist patch")
# Initialize logging
logger = setup_logging("main")

class Application:
    """Main application class."""
    
    def __init__(self):
        """Initialize application components."""
        self.db_pool: Optional[DatabasePool] = None
        self.security_manager: Optional[APISecurityManager] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.trading_bot: Optional[TradingBot] = None
        
        # Create necessary directories
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("metrics").mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize all application components."""
        try:
            # Initialize database pool
            self.db_pool = DatabasePool(
                database="data/trading.db",
                min_size=5,
                max_size=20
            )
            await self.db_pool.initialize()
            logger.info("Database pool initialized")
            
            # Initialize security manager
            security_config = APISecurityConfig(
                key_rotation_days=30,
                rate_limit_per_minute=60,
                max_request_size=1024 * 1024
            )
            self.security_manager = APISecurityManager(security_config)
            logger.info("Security manager initialized")
            
            # Initialize error handler
            self.error_handler = ErrorHandler(logger)
            # Register error callbacks
            self.error_handler.register_callback(
                ConnectionError,
                self._handle_connection_error
            )
            logger.info("Error handler initialized")
            
            # Initialize system monitor
            metrics_config = MetricsConfig(
                collection_interval=60,
                retention_days=7,
                alert_thresholds={
                    "cpu_usage": 80.0,
                    "memory_usage": 80.0,
                    "disk_usage": 80.0
                }
            )
            self.system_monitor = SystemMonitor(metrics_config)
            logger.info("System monitor initialized")
            
            # Initialize trading bot with enhanced components
            self.trading_bot = TradingBot(
                db_pool=self.db_pool,
                security_manager=self.security_manager,
                error_handler=self.error_handler,
                system_monitor=self.system_monitor
            )
            logger.info("Trading bot initialized")
            
        except Exception as e:
            logger.error(f"Error initializing application: {e}")
            raise
    
    async def _handle_connection_error(self, error: ConnectionError):
        """Handle connection errors."""
        logger.error(f"Connection error occurred: {error}")
        if self.system_monitor:
            await self.system_monitor.record_error("connection_error")
    
    async def start(self):
        """Start the application."""
        try:
            # Initialize components
            await self.initialize()
            
            # Start trading bot
            await self.trading_bot.start()
            logger.info("Trading bot started")
            
            # Keep application running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            await self.stop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the application."""
        try:
            # Stop trading bot
            if self.trading_bot:
                await self.trading_bot.stop()
            
            # Stop system monitor
            if self.system_monitor:
                await self.system_monitor.stop()
            
            # Close database pool
            if self.db_pool:
                await self.db_pool.close()
            
            logger.info("Application stopped")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
            raise

def list_available_platforms():
    """List all available trading platforms"""
    logger.info("Available Trading Platforms:")
    
    for platform_id, platform_config in PLATFORMS.items():
        status = "Enabled" if platform_config.get('enabled', False) else "Disabled"
        default = " (Default)" if platform_config.get('default', False) else ""
        logger.info(f"- {platform_config.get('name', platform_id)} ({platform_id}): {status}{default}")
        logger.info(f"  Type: {platform_config.get('type', 'unknown')}")
        logger.info(f"  Watchlist: {len(platform_config.get('watchlist', []))} symbols")

if __name__ == "__main__":
    # List available platforms
    list_available_platforms()
    
    # Create and run application
    app = Application()
    try:
        asyncio.run(app.start())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise 