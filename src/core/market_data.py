#!/usr/bin/env python3
"""
Market Data Module

This module handles fetching and processing market data.
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from src.integrations.alpaca import AlpacaIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketData:
    """Class for handling market data"""
    
    def __init__(self, api_key: str, api_secret: str, cache_dir: str = 'data/market_data', paper_trading: bool = True):
        """Initialize market data handler
        
        Args:
            api_key (str): Alpaca API key
            api_secret (str): Alpaca API secret
            cache_dir (str): Directory for caching market data
            paper_trading (bool): Whether to use paper trading
        """
        self.cache_dir = cache_dir
        self.alpaca = AlpacaIntegration(api_key=api_key, api_secret=api_secret, paper_trading=paper_trading)
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        logger.info("Market data handler initialized")

    def get_current_data(self, symbol: str, include_options: bool = True) -> Optional[Dict]:
        """Get current market data for a symbol
        
        Args:
            symbol (str): Trading symbol
            include_options (bool): Whether to include options data
            
        Returns:
            Dictionary with market data if successful, None otherwise
        """
        try:
            # Get historical data for calculations
            historical_data = self.get_historical_data(symbol)
            if historical_data is None:
                return None
            
            # Calculate technical indicators
            current_data = self._calculate_indicators(historical_data)
            
            # Get current price and volume
            latest_bar = historical_data.iloc[-1]
            current_data.update({
                'symbol': symbol,
                'current_price': float(latest_bar['close']),
                'volume': int(latest_bar['volume']),
                'timestamp': latest_bar.name  # The timestamp is already in ISO format
            })
            
            # Add options data if requested
            if include_options:
                options_data = self._get_options_data(symbol)
                if options_data:
                    current_data.update(options_data)
            
            return current_data
            
        except Exception as e:
            logger.error(f"Error getting current data for {symbol}: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        period: str = '1y',
        interval: str = '1d',
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """Get historical market data
        
        Args:
            symbol (str): Trading symbol
            period (str): Time period (e.g., '1d', '5d', '1mo', '1y')
            interval (str): Time interval (e.g., '1m', '5m', '1h', '1d')
            use_cache (bool): Whether to use cached data
            
        Returns:
            DataFrame with historical data if successful, None otherwise
        """
        try:
            # Check cache first
            cache_file = os.path.join(self.cache_dir, f"{symbol}_{period}_{interval}.csv")
            if use_cache and os.path.exists(cache_file):
                # Check if cache is still valid (less than 1 day old)
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                if cache_age < timedelta(days=1):
                    return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            
            # Fetch new data from Alpaca
            end_dt = datetime.now()
            if period == '1y':
                start_dt = end_dt - timedelta(days=365)
            elif period == '1mo':
                start_dt = end_dt - timedelta(days=30)
            elif period == '5d':
                start_dt = end_dt - timedelta(days=5)
            else:
                start_dt = end_dt - timedelta(days=1)
            
            # Get bars from Alpaca
            bars = self.alpaca.get_bars(symbol, start_dt, end_dt, interval)
            if not bars:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(bars)
            df.set_index('timestamp', inplace=True)
            
            # Cache the data
            df.to_csv(cache_file)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators
        
        Args:
            df (pd.DataFrame): Historical price data
            
        Returns:
            Dictionary with calculated indicators
        """
        try:
            # Calculate moving averages
            sma_20 = SMAIndicator(close=df['close'], window=20)
            sma_50 = SMAIndicator(close=df['close'], window=50)
            ema_12 = EMAIndicator(close=df['close'], window=12)
            ema_26 = EMAIndicator(close=df['close'], window=26)
            
            # Calculate RSI
            rsi = RSIIndicator(close=df['close'], window=14)
            
            # Calculate Bollinger Bands
            bb = BollingerBands(close=df['close'], window=20, window_dev=2)
            
            # Calculate MACD
            macd_line = ema_12.ema_indicator() - ema_26.ema_indicator()
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_hist = macd_line - signal_line
            
            # Calculate average volume
            avg_volume = df['volume'].rolling(window=20).mean()
            
            # Calculate volatility (20-day standard deviation of returns)
            returns = df['close'].pct_change()
            volatility = returns.rolling(window=20).std() * np.sqrt(252)  # Annualized
            
            # Get latest values
            latest_data = {
                'sma_20': float(sma_20.sma_indicator().iloc[-1]),
                'sma_50': float(sma_50.sma_indicator().iloc[-1]),
                'rsi': float(rsi.rsi().iloc[-1]),
                'bb_upper': float(bb.bollinger_hband().iloc[-1]),
                'bb_middle': float(bb.bollinger_mavg().iloc[-1]),
                'bb_lower': float(bb.bollinger_lband().iloc[-1]),
                'macd_line': float(macd_line.iloc[-1]),
                'macd_signal': float(signal_line.iloc[-1]),
                'macd_hist': float(macd_hist.iloc[-1]),
                'avg_volume': float(avg_volume.iloc[-1]),
                'volatility': float(volatility.iloc[-1])
            }
            
            # Determine trend
            latest_data['trend'] = self._determine_trend(df, latest_data)
            
            return latest_data
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}

    def _determine_trend(self, df: pd.DataFrame, indicators: Dict) -> str:
        """Determine market trend
        
        Args:
            df (pd.DataFrame): Historical price data
            indicators (Dict): Calculated indicators
            
        Returns:
            Trend direction ('bullish', 'bearish', or 'neutral')
        """
        try:
            # Get latest price
            current_price = df['close'].iloc[-1]
            
            # Check multiple factors
            price_above_sma20 = current_price > indicators['sma_20']
            price_above_sma50 = current_price > indicators['sma_50']
            rsi_bullish = indicators['rsi'] > 50
            macd_bullish = indicators['macd_hist'] > 0
            
            # Count bullish factors
            bullish_count = sum([
                price_above_sma20,
                price_above_sma50,
                rsi_bullish,
                macd_bullish
            ])
            
            if bullish_count >= 3:
                return 'bullish'
            elif bullish_count <= 1:
                return 'bearish'
            else:
                return 'neutral'
            
        except Exception as e:
            logger.error(f"Error determining trend: {e}")
            return 'neutral'

    def _get_options_data(self, symbol: str) -> Dict:
        """Get options market data
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dictionary with options data
        """
        try:
            # Get option chain
            option_chain = self.alpaca.get_option_chain(symbol)
            
            # Calculate IV percentile
            iv_values = [opt['implied_volatility'] for opt in option_chain if opt['implied_volatility'] > 0]
            if iv_values:
                iv_percentile = np.percentile(iv_values, 50)  # Use 50th percentile as current IV level
            else:
                iv_percentile = 0
            
            # Get put/call ratio
            calls = sum(1 for opt in option_chain if opt['type'].lower() == 'call')
            puts = sum(1 for opt in option_chain if opt['type'].lower() == 'put')
            put_call_ratio = puts / calls if calls > 0 else 0
            
            # Calculate total open interest and volume
            total_oi = sum(opt['open_interest'] for opt in option_chain)
            total_volume = sum(opt['volume'] for opt in option_chain)
            
            return {
                'option_chain': option_chain,
                'iv_percentile': iv_percentile,
                'put_call_ratio': put_call_ratio,
                'total_open_interest': total_oi,
                'total_option_volume': total_volume
            }
            
        except Exception as e:
            logger.error(f"Error getting options data for {symbol}: {e}")
            return {
                'option_chain': [],
                'iv_percentile': 0,
                'put_call_ratio': 0,
                'total_open_interest': 0,
                'total_option_volume': 0
            } 