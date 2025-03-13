#!/usr/bin/env python3
"""
ML Model Training Script

This script fetches historical data, generates features, and trains the ML model
for enhancing trading signals in the KryptoBot trading system.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from dotenv import load_dotenv
from tqdm import tqdm
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from config import WATCHLIST, STOP_LOSS_PCT, TAKE_PROFIT_PCT
from ml_enhancer import MLSignalEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ml_training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs('models', exist_ok=True)
os.makedirs('results', exist_ok=True)

def fetch_historical_data(symbol, period='2y', interval='1d'):
    """
    Fetch historical price data for a symbol
    
    Args:
        symbol: Trading symbol
        period: Time period to fetch (default: 2 years)
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
        if len(data) < 100:
            logger.warning(f"Insufficient data for {symbol}: {len(data)} rows")
            return None
            
        logger.info(f"Fetched {len(data)} rows of historical data for {symbol}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return None

def generate_training_data(symbols=None, period='2y', interval='1d'):
    """
    Generate training data for the ML model
    
    Args:
        symbols: List of symbols to fetch data for (default: WATCHLIST)
        period: Time period to fetch (default: 2 years)
        interval: Data interval (default: 1 day)
        
    Returns:
        Tuple of (X, y) for training
    """
    if symbols is None:
        symbols = WATCHLIST
        
    # Initialize ML enhancer
    ml_enhancer = MLSignalEnhancer()
    
    all_features = []
    all_outcomes = []
    
    for symbol in tqdm(symbols, desc="Generating training data"):
        # Fetch historical data
        data = fetch_historical_data(symbol, period, interval)
        
        if data is None or len(data) < 100:
            continue
            
        # Extract features
        try:
            features = ml_enhancer._extract_features(data)
            
            # Skip if we have NaN values
            if features.isnull().values.any():
                logger.warning(f"NaN values in features for {symbol}")
                features = features.fillna(0)
                
            # Simulate trades and determine outcomes
            for i in range(50, len(data) - 20):  # Start from 50th day to have enough data for features
                # Skip if we have NaN values in the current row
                if features.iloc[i].isnull().values.any():
                    continue
                    
                # Get current price and features
                current_price = data['close'].iloc[i]
                current_features = features.iloc[i].values
                
                # Simulate a long trade
                entry_price = current_price
                stop_loss = entry_price * (1 - STOP_LOSS_PCT)
                take_profit = entry_price * (1 + TAKE_PROFIT_PCT)
                
                # Check future prices to see if stop loss or take profit was hit
                future_prices = data['close'].iloc[i+1:i+20]  # Look 20 days ahead
                
                # Determine outcome
                outcome = 0  # Default to loss
                
                for future_price in future_prices:
                    if future_price <= stop_loss:
                        # Stop loss hit
                        outcome = 0
                        break
                    elif future_price >= take_profit:
                        # Take profit hit
                        outcome = 1
                        break
                
                # Add to training data
                all_features.append(current_features)
                all_outcomes.append(outcome)
                
        except Exception as e:
            logger.error(f"Error generating features for {symbol}: {e}")
            continue
    
    # Convert to numpy arrays
    X = np.array(all_features)
    y = np.array(all_outcomes)
    
    logger.info(f"Generated {len(X)} training samples with {sum(y)} positive outcomes")
    
    return X, y

def train_model(X, y):
    """
    Train the ML model
    
    Args:
        X: Feature matrix
        y: Target vector
        
    Returns:
        Trained ML enhancer
    """
    # Initialize ML enhancer
    ml_enhancer = MLSignalEnhancer()
    
    # Scale features
    X_scaled = ml_enhancer.scaler.fit_transform(X)
    
    # Train model
    logger.info("Training ML model...")
    ml_enhancer.model.fit(X_scaled, y)
    
    # Save model
    joblib.dump(ml_enhancer.model, ml_enhancer.model_path)
    
    # Save scaler
    joblib.dump(ml_enhancer.scaler, 'models/scaler.joblib')
    
    logger.info(f"ML model trained and saved to {ml_enhancer.model_path}")
    
    # Calculate feature importance
    feature_importance = dict(zip(ml_enhancer.feature_columns, 
                                 ml_enhancer.model.feature_importances_))
    
    # Log feature importance
    for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"Feature importance: {feature}: {importance:.4f}")
    
    # Plot feature importance
    plt.figure(figsize=(10, 6))
    sns.barplot(x=list(feature_importance.values()), y=list(feature_importance.keys()))
    plt.title('Feature Importance')
    plt.tight_layout()
    plt.savefig('results/feature_importance.png')
    
    # Calculate and log model accuracy
    accuracy = ml_enhancer.model.score(X_scaled, y)
    logger.info(f"Model accuracy: {accuracy:.4f}")
    
    # Generate predictions
    y_pred = ml_enhancer.model.predict(X_scaled)
    
    # Generate classification report
    report = classification_report(y, y_pred)
    logger.info(f"Classification report:\n{report}")
    
    # Generate confusion matrix
    cm = confusion_matrix(y, y_pred)
    
    # Plot confusion matrix
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('results/confusion_matrix.png')
    
    # Save training results
    results = {
        'accuracy': float(accuracy),
        'feature_importance': feature_importance,
        'training_samples': len(X),
        'positive_outcomes': int(sum(y)),
        'training_date': datetime.now().isoformat()
    }
    
    # Save results to JSON
    import json
    with open('results/training_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    
    return ml_enhancer

def main():
    """Main function"""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting ML model training...")
    
    # Generate training data
    X, y = generate_training_data()
    
    if len(X) == 0:
        logger.error("No training data generated")
        return
    
    # Train model
    ml_enhancer = train_model(X, y)
    
    logger.info("ML model training completed")

if __name__ == "__main__":
    main() 