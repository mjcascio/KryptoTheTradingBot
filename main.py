import logging
import os
from trading_bot import TradingBot
from ml_enhancer import MLSignalEnhancer
from strategy_allocator import StrategyAllocator
from portfolio_optimizer import PortfolioOptimizer
from performance_analyzer import PerformanceAnalyzer
from parameter_tuner import AdaptiveParameterTuner
from config import BREAKOUT_PARAMS, TREND_PARAMS

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
            'adx_period': 14,
            'adx_threshold': 25
        }
    }
    
    # Parameter bounds for the tuner
    param_bounds = {
        'price_threshold': {'min': 0.005, 'max': 0.05},
        'volume_threshold': {'min': 1.2, 'max': 3.0},
        'lookback_period': {'min': 10, 'max': 30},
        'consolidation_threshold': {'min': 0.005, 'max': 0.02},
        'short_ma': {'min': 5, 'max': 15},
        'medium_ma': {'min': 15, 'max': 30},
        'long_ma': {'min': 30, 'max': 80},
        'rsi_period': {'min': 7, 'max': 21}
    }
    
    # Create the bot
    bot = TradingBot(
        ml_enhancer=MLSignalEnhancer(),
        strategy_allocator=StrategyAllocator(strategies_config),
        portfolio_optimizer=PortfolioOptimizer(
            max_positions=10,
            sector_max_allocation=0.30,
            stock_max_allocation=0.15
        ),
        performance_analyzer=PerformanceAnalyzer(),
        parameter_tuner=AdaptiveParameterTuner(
            base_params={**BREAKOUT_PARAMS, **TREND_PARAMS},
            param_bounds=param_bounds
        )
    )
    
    return bot

if __name__ == "__main__":
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Krypto Trading Bot - Alpaca Markets Edition")
    
    try:
        # Initialize and run the trading bot
        bot = initialize_bot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Trading Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise 