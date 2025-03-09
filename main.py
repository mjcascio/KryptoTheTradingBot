import logging
import os
from trading_bot import TradingBot
from ml_enhancer import MLSignalEnhancer
from strategy_allocator import StrategyAllocator
from portfolio_optimizer import PortfolioOptimizer
from performance_analyzer import PerformanceAnalyzer
from parameter_tuner import AdaptiveParameterTuner
from config import BREAKOUT_PARAMS, TREND_PARAMS, PLATFORMS
from brokers import BrokerFactory

def setup_logging():
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/trading_bot.log"),
            logging.StreamHandler()
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger('alpaca_trade_api').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def initialize_bot():
    """Initialize the trading bot with all features"""
    logger.info("Initializing Enhanced Trading Bot...")
    
    # Create strategy configurations for the allocator
    strategies_config = {
        'breakout': BREAKOUT_PARAMS,
        'trend_following': TREND_PARAMS,
        'mean_reversion': {
            'bb_window': 20,
            'bb_std': 2,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        },
        'momentum': {
            'price_momentum_period': 5,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14
        }
    }
    
    # Initialize strategy allocator
    strategy_allocator = StrategyAllocator(strategies_config)
    
    # Initialize ML enhancer
    ml_enhancer = MLSignalEnhancer()
    
    # Initialize portfolio optimizer
    portfolio_optimizer = PortfolioOptimizer()
    
    # Initialize performance analyzer
    performance_analyzer = PerformanceAnalyzer()
    
    # Initialize parameter tuner
    parameter_tuner = AdaptiveParameterTuner(strategies_config)
    
    # Initialize trading bot with all components
    bot = TradingBot(
        strategies=strategy_allocator.get_strategies()
    )
    
    # Connect ML enhancer to bot
    ml_enhancer.connect_to_bot(bot)
    
    # Connect portfolio optimizer to bot
    portfolio_optimizer.connect_to_bot(bot)
    
    # Connect performance analyzer to bot
    performance_analyzer.connect_to_bot(bot)
    
    # Connect parameter tuner to bot
    parameter_tuner.connect_to_bot(bot)
    
    logger.info("Enhanced Trading Bot initialized successfully")
    
    return bot

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
    # Set up logging
    logger = setup_logging()
    
    # List available platforms
    list_available_platforms()
    
    # Initialize the trading bot
    bot = initialize_bot()
    
    # Start the bot
    logger.info("Starting trading bot...")
    bot.start()
    
    try:
        # Keep the main thread alive
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected. Stopping bot...")
        bot.stop()
        logger.info("Bot stopped. Exiting...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        bot.stop()
        logger.info("Bot stopped due to error. Exiting...") 