#!/usr/bin/env python3
"""
Anomaly Detector Training Script

This script trains the anomaly detection model using historical market data.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
from dotenv import load_dotenv
from tqdm import tqdm
import argparse

# Import our anomaly detector
from anomaly_detector import AnomalyDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("anomaly_detector_training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fetch_historical_data(symbol, period='5y', interval='1d'):
    """
    Fetch historical price data for a symbol
    
    Args:
        symbol: Trading symbol
        period: Time period to fetch (default: 5 years)
        interval: Data interval (default: 1 day)
        
    Returns:
        DataFrame with OHLCV data
    """
    try:
        logger.info(f"Fetching historical data for {symbol}...")
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        
        # Rename columns to lowercase
        data.columns = [col.lower() for col in data.columns]
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Rename Date column to date
        data = data.rename(columns={'date': 'date'})
        
        # Check if we have enough data
        if len(data) < 500:  # Need more data for anomaly detection
            logger.warning(f"Insufficient data for {symbol}: {len(data)} rows")
            return None
            
        logger.info(f"Fetched {len(data)} rows of historical data for {symbol}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return None

def train_anomaly_detector(symbols=None, epochs=50, batch_size=32):
    """
    Train the anomaly detection model
    
    Args:
        symbols: List of symbols to fetch data for
        epochs: Number of training epochs
        batch_size: Batch size for training
        
    Returns:
        Trained anomaly detector
    """
    if symbols is None:
        # Use a subset of major symbols for training
        symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
    
    # Initialize anomaly detector
    detector = AnomalyDetector()
    
    # Fetch and combine data from multiple symbols
    all_data = []
    
    for symbol in tqdm(symbols, desc="Fetching data"):
        data = fetch_historical_data(symbol)
        if data is not None:
            # Add symbol column
            data['symbol'] = symbol
            all_data.append(data)
    
    if not all_data:
        logger.error("No data fetched for training")
        return None
        
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined data shape: {combined_data.shape}")
    
    # Group by symbol and train on each symbol's data
    for symbol, group in tqdm(combined_data.groupby('symbol'), desc="Training models"):
        logger.info(f"Training anomaly detector on {symbol} data...")
        
        # Sort by date
        group = group.sort_values('date')
        
        # Train the model
        history = detector.train(
            data=group,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2
        )
        
        if history is not None:
            # Test the model
            anomalies = detector.detect_anomalies(group)
            
            if anomalies is not None:
                # Plot anomalies
                detector.plot_anomalies(group, anomalies, symbol=symbol)
                
                # Log anomaly statistics
                anomaly_count = anomalies['is_anomaly'].sum()
                anomaly_pct = (anomaly_count / len(anomalies)) * 100
                logger.info(f"Detected {anomaly_count} anomalies in {symbol} data ({anomaly_pct:.2f}%)")
    
    return detector

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Train anomaly detection model')
    parser.add_argument('--symbols', type=str, nargs='+', help='Symbols to train on')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size for training')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting anomaly detection model training...")
    
    # Train the model
    detector = train_anomaly_detector(
        symbols=args.symbols,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    if detector is not None:
        logger.info("Anomaly detection model training completed successfully")
    else:
        logger.error("Anomaly detection model training failed")

if __name__ == "__main__":
    main() 