#!/usr/bin/env python3
"""
Run Ensemble Bot

This script runs the trading bot with ensemble learning integration.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ensemble_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run trading bot with ensemble learning integration')
    parser.add_argument('--train-ensemble', action='store_true', help='Train ensemble model before starting')
    parser.add_argument('--voting', type=str, default='soft', choices=['soft', 'hard'], help='Voting type for ensemble')
    parser.add_argument('--weights', type=str, help='Comma-separated weights for ensemble models (e.g., "1,2,1")')
    args = parser.parse_args()
    
    # Train ensemble model if requested
    if args.train_ensemble:
        logger.info("Training ensemble model...")
        try:
            import ensemble_learning
            ensemble_learning.main()
            logger.info("Ensemble model training completed")
        except Exception as e:
            logger.error(f"Error training ensemble model: {e}")
            return
    
    # Apply ensemble integration to trading bot
    logger.info("Applying ensemble integration to trading bot...")
    try:
        import ensemble_integration
        ensemble_integration.main()
    except Exception as e:
        logger.error(f"Error applying ensemble integration: {e}")
        return
    
    # Import and run the trading bot
    logger.info("Starting trading bot with ensemble integration...")
    try:
        from trading_bot import TradingBot
        
        # Create and start the trading bot
        bot = TradingBot()
        bot.start()
        
        # Log ensemble status
        from ensemble_integration import get_ensemble_integration
        ensemble_integration = get_ensemble_integration()
        ensemble_status = ensemble_integration.get_ensemble_status()
        
        logger.info(f"Ensemble status: {ensemble_status}")
        
        # Keep the script running
        logger.info("Trading bot is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the script running until interrupted
            while True:
                import time
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Stopping trading bot...")
            bot.stop()
            logger.info("Trading bot stopped")
    except Exception as e:
        logger.error(f"Error running trading bot: {e}")

if __name__ == "__main__":
    main() 