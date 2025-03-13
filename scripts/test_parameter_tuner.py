#!/usr/bin/env python
"""
Test script for the parameter tuner plugin.

This script demonstrates how to use the parameter tuner plugin to optimize strategy parameters.
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

def moving_average_crossover_strategy(params, data):
    """
    Simple moving average crossover strategy for testing.
    
    Args:
        params (Dict[str, Any]): Strategy parameters
        data (pd.DataFrame): Market data
        
    Returns:
        float: Strategy performance metric (e.g., profit)
    """
    # Extract parameters
    short_window = int(params['short_window'])
    long_window = int(params['long_window'])
    
    # Ensure short_window is less than long_window
    if short_window >= long_window:
        return -1.0  # Invalid parameters
    
    # Calculate moving averages
    data = data.copy()  # Create a copy to avoid SettingWithCopyWarning
    data['short_ma'] = data['close'].rolling(window=short_window).mean()
    data['long_ma'] = data['close'].rolling(window=long_window).mean()
    
    # Generate signals
    data['signal'] = 0.0
    data.loc[short_window:, 'signal'] = np.where(
        data['short_ma'][short_window:] > data['long_ma'][short_window:], 1.0, 0.0
    )
    
    # Generate positions
    data['position'] = data['signal'].diff()
    
    # Calculate returns
    data['returns'] = data['close'].pct_change()
    data['strategy_returns'] = data['position'] * data['returns']
    
    # Calculate performance metrics
    total_return = data['strategy_returns'].sum()
    sharpe_ratio = data['strategy_returns'].mean() / data['strategy_returns'].std() * np.sqrt(252)
    
    # Combine metrics into a single score
    score = total_return * 100 + sharpe_ratio
    
    return score

def generate_sample_data(num_points=500):
    """
    Generate sample market data for testing.
    
    Args:
        num_points (int): Number of data points to generate
        
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
    
    # Add some cyclical patterns
    cycles = 10 * np.sin(np.linspace(0, 10 * np.pi, num_points))
    prices += cycles
    
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

def main():
    """Main function."""
    try:
        # Import the parameter tuner plugin
        from plugins.parameter_tuner.parameter_tuner import ParameterTunerPlugin
        
        # Create the plugin
        plugin = ParameterTunerPlugin()
        logger.info(f"Created plugin: {plugin.name} v{plugin.version}")
        
        # Initialize the plugin
        context = {
            'results_dir': 'results/parameter_tuner',
            'cache_dir': 'cache/parameter_tuner',
            'cache_expiry': 86400,
            'optimization_methods': ['simulated_annealing', 'quantum_pso', 'quantum_annealing'],
            'max_iterations': 50,  # Reduced for testing
            'population_size': 10  # Reduced for testing
        }
        
        if plugin.initialize(context):
            logger.info("Plugin initialized successfully")
        else:
            logger.error("Failed to initialize plugin")
            return 1
        
        # Generate sample market data
        data = generate_sample_data(num_points=500)
        logger.info(f"Generated sample data with {len(data)} data points")
        
        # Define parameter space for moving average crossover strategy
        parameter_space = {
            'short_window': {
                'type': 'int',
                'min': 5,
                'max': 50
            },
            'long_window': {
                'type': 'int',
                'min': 20,
                'max': 200
            }
        }
        
        # Define objective function
        def objective_function(params):
            return moving_average_crossover_strategy(params, data.copy())
        
        # Execute the plugin for each optimization method
        optimization_methods = ['simulated_annealing', 'quantum_pso', 'quantum_annealing']
        
        for method in optimization_methods:
            logger.info(f"Testing {method} optimization method")
            
            # Execute the plugin
            result = plugin.execute({
                'strategy_name': 'moving_average_crossover',
                'parameter_space': parameter_space,
                'objective_function': objective_function,
                'optimization_method': method,
                'max_iterations': 50,  # Reduced for testing
                'population_size': 10  # Reduced for testing
            })
            
            # Print the result
            logger.info(f"Optimization results for {method}:")
            logger.info(f"  Best parameters: {result['best_params']}")
            logger.info(f"  Best score: {result['best_score']:.4f}")
            
            # Save the result to a file
            output_file = f"parameter_tuning_{method}_results.json"
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