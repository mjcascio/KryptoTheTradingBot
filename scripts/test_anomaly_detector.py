#!/usr/bin/env python
"""
Test script for the anomaly detector plugin.

This script demonstrates how to use the anomaly detector plugin to detect market anomalies.
"""

import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_sample_data(symbol, num_points=100, anomaly_at=None):
    """
    Generate sample market data for testing.
    
    Args:
        symbol (str): Symbol to generate data for
        num_points (int): Number of data points to generate
        anomaly_at (int, optional): Index at which to introduce an anomaly
        
    Returns:
        pd.DataFrame: Generated market data
    """
    # Generate timestamps
    end_date = datetime.now()
    start_date = end_date - timedelta(days=num_points)
    dates = pd.date_range(start=start_date, end=end_date, periods=num_points)
    
    # Generate price data with a trend and some noise
    trend = np.linspace(100, 120, num_points)
    noise = np.random.normal(0, 1, num_points)
    prices = trend + noise
    
    # Introduce an anomaly if specified
    if anomaly_at is not None and 0 <= anomaly_at < num_points:
        prices[anomaly_at] += 10.0  # Add a price spike
    
    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices - 0.5,
        'high': prices + 1.0,
        'low': prices - 1.0,
        'close': prices,
        'volume': np.random.randint(1000, 10000, num_points)
    })
    
    return data

def make_json_serializable(obj):
    """
    Convert an object to a JSON serializable format.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON serializable object
    """
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    else:
        return obj

def main():
    """Main function."""
    try:
        # Import the anomaly detector plugin
        from plugins.anomaly_detector.anomaly_detector import AnomalyDetectorPlugin
        
        # Create the plugin
        plugin = AnomalyDetectorPlugin()
        logger.info(f"Created plugin: {plugin.name} v{plugin.version}")
        
        # Initialize the plugin
        context = {
            'model_dir': 'models/anomaly_detector',
            'cache_dir': 'cache/anomaly_detector',
            'cache_expiry': 3600,
            'detection_methods': ['statistical', 'autoencoder', 'isolation_forest'],
            'thresholds': {
                'statistical': 3.0,
                'autoencoder': 0.1,
                'isolation_forest': -0.2
            },
            'window_size': 20
        }
        
        if plugin.initialize(context):
            logger.info("Plugin initialized successfully")
        else:
            logger.error("Failed to initialize plugin")
            return 1
        
        # Generate sample market data
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
        market_data = {}
        
        for i, symbol in enumerate(symbols):
            # Introduce an anomaly in some symbols
            anomaly_at = 99 if i % 2 == 0 else None
            market_data[symbol] = generate_sample_data(symbol, num_points=100, anomaly_at=anomaly_at)
            logger.info(f"Generated sample data for {symbol} with anomaly at {anomaly_at}")
        
        # Execute the plugin
        data = {
            'market_data': market_data
        }
        
        result = plugin.execute(data)
        
        # Print the result
        logger.info("Anomaly detection results:")
        for symbol, anomaly_data in result['results'].items():
            if anomaly_data['anomalies_detected']:
                logger.info(f"  {symbol}: ANOMALY DETECTED - {anomaly_data.get('anomaly_type', 'unknown')} anomaly")
                for method, method_results in anomaly_data['methods'].items():
                    if method_results.get('anomalies_detected', False):
                        logger.info(f"    - {method}: score={method_results.get('anomaly_score', 0.0):.4f}")
            else:
                logger.info(f"  {symbol}: No anomalies detected")
        
        # Save the result to a file for inspection
        output_file = 'anomaly_detection_results.json'
        with open(output_file, 'w') as f:
            json.dump(make_json_serializable(result), f, indent=2)
        logger.info(f"Saved results to {output_file}")
        
        # Shutdown the plugin
        if plugin.shutdown():
            logger.info("Plugin shutdown successfully")
        else:
            logger.error("Failed to shutdown plugin")
            return 1
        
        return 0
    
    except ImportError as e:
        logger.error(f"Error importing plugin: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"Error testing plugin: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 