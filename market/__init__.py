"""
Market module for KryptoBot Trading System.

This module handles all market data operations, analysis, and market-related
functionality. It provides tools for analyzing market conditions, calculating
correlations, and managing market data across different assets.

Key Components:
    - Market Analysis: Technical analysis, sector analysis, and correlations
    - Market Data: Real-time and historical data management
    - Market Hours: Trading session management and market status

Example:
    from market.analysis import calculate_correlation_matrix
    from market.data import get_market_status, is_market_open

    # Check market status
    market_status = get_market_status()
    if market_status['is_open']:
        # Calculate correlations for a basket of stocks
        correlations = calculate_correlation_matrix([
            "AAPL", "MSFT", "GOOGL", "AMZN"
        ])
        
        # Process correlation data
        for symbol, data in correlations['matrix'].items():
            print(f"Correlations for {symbol}: {data}")
"""

from .analysis import *
from .data import * 