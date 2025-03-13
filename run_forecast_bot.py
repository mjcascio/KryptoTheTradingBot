#!/usr/bin/env python3
"""
Run Trading Bot with Time Series Forecasting Integration

This script runs the trading bot with time series forecasting integration
to enhance trading decisions based on price forecasts.
"""

import os
import sys
import logging
import argparse
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("forecast_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the trading bot with forecasting integration"""
    logger.info("Starting trading bot with forecasting integration...")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run trading bot with forecasting integration')
    parser.add_argument('--train-lstm', action='store_true', help='Train LSTM model before starting')
    parser.add_argument('--train-gru', action='store_true', help='Train GRU model before starting')
    parser.add_argument('--symbols', nargs='+', help='Symbols to train forecasting models for')
    parser.add_argument('--config', type=str, default='config/config.json', help='Path to config file')
    parser.add_argument('--forecast-config', type=str, default='config/forecasting_settings.json', help='Path to forecasting settings file')
    args = parser.parse_args()
    
    try:
        # Import required modules
        try:
            from trading_bot import TradingBot
            from forecasting_integration import ForecastingIntegration
            from time_series_forecasting import TimeSeriesForecaster
            from train_ml_model import fetch_historical_data
        except ImportError as e:
            logger.error(f"Error importing required modules: {e}")
            sys.exit(1)
        
        # Train forecasting models if requested
        if args.train_lstm or args.train_gru:
            train_forecasting_models(args)
        
        # Load trading bot configuration
        config = load_config(args.config)
        
        # Create trading bot instance
        bot = TradingBot(config)
        
        # Create forecasting integration
        forecasting = ForecastingIntegration(settings_path=args.forecast_config)
        
        # Update forecasts
        logger.info("Updating forecasts...")
        forecasts = forecasting.update_forecasts(data_provider=fetch_historical_data)
        
        # Log forecast results
        for symbol, forecast_data in forecasts.items():
            if 'combined' in forecast_data:
                trend = forecast_data['combined']['trend']
                signal = forecasting.get_trend_signal(symbol)
                
                logger.info(f"Forecast for {symbol}: Trend={trend:.4f}, Signal={signal['signal']}, "
                           f"Strength={signal['strength']:.4f}, Confidence={signal['confidence']:.4f}")
        
        # Patch trading bot with forecasting integration
        bot = forecasting.patch_trading_bot(bot)
        
        # Start trading bot
        logger.info("Starting trading bot...")
        bot.run()
        
    except Exception as e:
        logger.error(f"Error running trading bot with forecasting: {e}")
        sys.exit(1)

def train_forecasting_models(args):
    """
    Train forecasting models
    
    Args:
        args: Command line arguments
    """
    try:
        from time_series_forecasting import TimeSeriesForecaster
        from train_ml_model import fetch_historical_data
        
        # Get symbols to train for
        symbols = args.symbols
        
        if not symbols:
            # Load symbols from forecasting settings
            forecast_config = load_config(args.forecast_config)
            symbols = forecast_config.get('symbols', ['SPY', 'QQQ', 'AAPL', 'MSFT'])
        
        logger.info(f"Training forecasting models for symbols: {symbols}")
        
        for symbol in symbols:
            # Fetch historical data
            data = fetch_historical_data(symbol, period='5y', interval='1d')
            
            if data is None or len(data) < 100:
                logger.warning(f"Insufficient data for {symbol}")
                continue
            
            # Set date as index
            data.set_index('date', inplace=True)
            
            # Train LSTM model
            if args.train_lstm:
                logger.info(f"Training LSTM model for {symbol}...")
                lstm_forecaster = TimeSeriesForecaster(model_type='lstm', sequence_length=60, forecast_horizon=5)
                lstm_forecaster.train(data, target_column='close', epochs=50, batch_size=32)
                lstm_forecaster.evaluate(data, target_column='close')
            
            # Train GRU model
            if args.train_gru:
                logger.info(f"Training GRU model for {symbol}...")
                gru_forecaster = TimeSeriesForecaster(model_type='gru', sequence_length=60, forecast_horizon=5)
                gru_forecaster.train(data, target_column='close', epochs=50, batch_size=32)
                gru_forecaster.evaluate(data, target_column='close')
            
            logger.info(f"Completed training for {symbol}")
        
        logger.info("Forecasting model training completed")
        
    except Exception as e:
        logger.error(f"Error training forecasting models: {e}")
        raise

def load_config(config_path):
    """
    Load configuration from JSON file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary with configuration
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        # Return empty config
        return {}

if __name__ == "__main__":
    main() 