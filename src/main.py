#!/usr/bin/env python3
"""
Main entry point for the KryptoBot trading bot.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

from src.core.trading_bot import TradingBot
from src.core.risk_management import RiskManager
from src.strategies.stock import StockStrategy
from src.strategies.options import OptionsStrategy
from src.integrations.telegram_notifications import TelegramNotifier


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the trading bot"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API credentials
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not all([api_key, api_secret]):
            logger.error("Missing required environment variables")
            sys.exit(1)
        
        # Initialize components
        risk_manager = RiskManager(
            max_position_size=10000,  # $10k max position
            max_drawdown=0.02,        # 2% max drawdown
            risk_per_trade=0.01,      # 1% risk per trade
            max_open_positions=5,      # Max 5 positions
            max_daily_loss=0.03,      # 3% max daily loss
            volatility_threshold=0.3   # 30% volatility threshold
        )
        
        stock_strategy = StockStrategy(
            name="Test Stock Strategy",
            description="Basic stock trading strategy for testing"
        )
        
        options_strategy = OptionsStrategy(
            name="Test Options Strategy",
            description="Basic options trading strategy for testing",
            min_delta=0.3,
            max_delta=0.7,
            min_days_to_expiry=7,
            max_days_to_expiry=45,
            min_volume=100,
            min_open_interest=500
        )
        
        # Initialize Telegram notifier
        telegram_notifier = TelegramNotifier()
        
        # Initialize trading bot
        bot = TradingBot(
            api_key=api_key,
            api_secret=api_secret,
            stock_strategy=stock_strategy,
            options_strategy=options_strategy,
            risk_manager=risk_manager,
            telegram_notifier=telegram_notifier,
            paper_trading=True  # Always use paper trading for testing
        )
        
        # Connect trading bot to Telegram notifier
        telegram_notifier.connect_trading_bot(bot)
        
        # Start the bot
        if not bot.start():
            logger.error("Failed to start trading bot")
            sys.exit(1)
        
        # Start Telegram notifications
        telegram_notifier.start()
        
        # Main loop
        while True:
            try:
                # Update bot status
                bot.update()
                
                # Sleep for a bit
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, stopping bot...")
                bot.stop()
                telegram_notifier.stop()
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                bot.stop()
                telegram_notifier.stop()
                break
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 