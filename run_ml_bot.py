#!/usr/bin/env python3
"""
Run ML Bot

This script runs the trading bot with ML integration.
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
        logging.FileHandler("ml_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run trading bot with ML integration')
    parser.add_argument('--train-ml', action='store_true', help='Train ML model before starting')
    parser.add_argument('--train-anomaly', action='store_true', help='Train anomaly detection model before starting')
    parser.add_argument('--symbols', type=str, nargs='+', help='Symbols to train anomaly detection on')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs for anomaly detection')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size for training')
    args = parser.parse_args()
    
    # Train ML model if requested
    if args.train_ml:
        logger.info("Training ML model...")
        try:
            import train_ml_model
            train_ml_model.main()
            logger.info("ML model training completed")
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            return
    
    # Train anomaly detection model if requested
    if args.train_anomaly:
        logger.info("Training anomaly detection model...")
        try:
            import train_anomaly_detector
            
            # Create command line arguments for training
            sys.argv = ['train_anomaly_detector.py']
            if args.symbols:
                sys.argv.extend(['--symbols'] + args.symbols)
            if args.epochs:
                sys.argv.extend(['--epochs', str(args.epochs)])
            if args.batch_size:
                sys.argv.extend(['--batch-size', str(args.batch_size)])
            
            train_anomaly_detector.main()
            logger.info("Anomaly detection model training completed")
        except Exception as e:
            logger.error(f"Error training anomaly detection model: {e}")
            return
    
    # Apply ML patch to trading bot
    logger.info("Applying ML patch to trading bot...")
    try:
        import trading_bot_ml_patch
        trading_bot_ml_patch.main()
    except Exception as e:
        logger.error(f"Error applying ML patch: {e}")
        return
    
    # Import and run the trading bot
    logger.info("Starting trading bot with ML integration...")
    try:
        from trading_bot import TradingBot
        
        # Create and start the trading bot
        bot = TradingBot()
        bot.start()
        
        # Log ML status
        from ml_integration import get_ml_integration
        ml_integration = get_ml_integration()
        ml_status = ml_integration.get_ml_status()
        
        logger.info(f"ML status: {ml_status}")
        
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