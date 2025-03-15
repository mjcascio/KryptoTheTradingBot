#!/usr/bin/env python3
"""
Main entry point for the KryptoBot trading bot.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

from src.core.trading_bot import TradingBot


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_bot(bot):
    """Run the trading bot and handle updates"""
    try:
        while True:
            try:
                # Update bot status
                bot.update()
                
                # Sleep briefly
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in bot update loop: {e}")
                if bot.telegram_notifier:
                    await bot.telegram_notifier.send_message(
                        f"❌ Error in bot update loop: {str(e)}"
                    )
                break
    
    finally:
        # Ensure cleanup on exit
        bot.stop()


async def main_async():
    """Async main function to run the trading bot"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API credentials
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not all([api_key, api_secret]):
            logger.error("Missing required environment variables")
            sys.exit(1)
        
        # Create configuration
        config = {
            'platforms': {
                'alpaca': {
                    'enabled': True,
                    'default': True,
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'paper_trading': True
                }
            },
            'risk': {
                'max_position_size': 10000,
                'max_drawdown': 0.02,
                'risk_per_trade': 0.01,
                'max_open_positions': 5,
                'max_daily_loss': 0.03,
                'volatility_threshold': 0.3
            },
            'strategies': {
                'stock': {
                    'enabled': True,
                    'name': "Test Stock Strategy",
                    'description': "Basic stock trading strategy for testing"
                },
                'options': {
                    'enabled': True,
                    'name': "Test Options Strategy",
                    'description': "Basic options trading strategy for testing",
                    'min_delta': 0.3,
                    'max_delta': 0.7,
                    'min_days_to_expiry': 7,
                    'max_days_to_expiry': 45,
                    'min_volume': 100,
                    'min_open_interest': 500
                }
            },
            'monitoring': {
                'telegram_enabled': True,
                'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                'metrics_enabled': True,
                'metrics_interval': 60,
                'metrics_retention_days': 30
            },
            'system': {
                'pid_file': 'trading_bot.pid',
                'log_file': 'trading_bot.log',
                'data_dir': 'data'
            }
        }
        
        # Initialize trading bot
        bot = TradingBot(config)
        
        # Start the bot
        if not bot.start():
            logger.error("Failed to start trading bot")
            sys.exit(1)
        
        # Run the bot
        await run_bot(bot)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async main function
        loop.run_until_complete(main_async())
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping bot...")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)
    finally:
        # Clean up the event loop
        loop.close()


if __name__ == "__main__":
    main() 