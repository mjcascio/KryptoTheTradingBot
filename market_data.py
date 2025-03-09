import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from typing import Optional

from brokers import BaseBroker

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self, broker: BaseBroker):
        self.broker = broker
        self.data_source = 'broker'  # Default to broker
        self.fallback_attempts = 0
        self.max_fallback_attempts = 3
        
    def _get_timeframe_params(self, timeframe: str) -> tuple:
        """Convert broker timeframe to Yahoo Finance parameters"""
        # Parse the timeframe (e.g., '15Min', '1D')
        number = int(''.join(filter(str.isdigit, timeframe)))
        unit = ''.join(filter(str.isalpha, timeframe)).lower()
        
        # Convert to Yahoo Finance interval
        interval_map = {
            'min': f"{number}m",
            'hour': f"{number}h",
            'day': f"{number}d"
        }
        
        # Calculate period based on limit and timeframe
        if unit in ['min', 'hour']:
            period = "7d"  # For intraday data
        else:
            period = "60d"  # For daily data
            
        return interval_map.get(unit, "1d"), period

    def get_market_data(self, symbol: str, timeframe: str = '15Min', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Get market data with fallback between broker and Yahoo Finance
        """
        try:
            if self.data_source == 'broker':
                try:
                    # Try broker first
                    data = self.broker.get_market_data(symbol, timeframe, limit)
                    
                    if data is not None and not data.empty:
                        self.fallback_attempts = 0
                        return data
                    else:
                        logger.warning(f"No data returned from broker for {symbol}. Falling back to Yahoo Finance.")
                        self.fallback_attempts += 1
                        self.data_source = 'yfinance'
                except Exception as e:
                    logger.error(f"Error getting data from broker: {e}")
                    self.fallback_attempts += 1
                    self.data_source = 'yfinance'
            
            # Fallback to Yahoo Finance
            if self.data_source == 'yfinance':
                try:
                    # Convert timeframe to Yahoo Finance format
                    interval, period = self._get_timeframe_params(timeframe)
                    
                    # Get data from Yahoo Finance
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period=period, interval=interval)
                    
                    if data is not None and not data.empty:
                        self.fallback_attempts = 0
                        return data
                    else:
                        logger.warning(f"No data returned from Yahoo Finance for {symbol}.")
                        self.fallback_attempts += 1
                        self.data_source = 'broker'  # Switch back to broker for next attempt
                except Exception as e:
                    logger.error(f"Error getting data from Yahoo Finance: {e}")
                    self.fallback_attempts += 1
                    self.data_source = 'broker'  # Switch back to broker for next attempt
            
            # If we've tried both sources and failed, reset and return None
            if self.fallback_attempts >= self.max_fallback_attempts:
                logger.error(f"Failed to get data for {symbol} after {self.fallback_attempts} attempts.")
                self.fallback_attempts = 0
                self.data_source = 'broker'  # Reset to default
            
            return None
        except Exception as e:
            logger.error(f"Error in get_market_data: {e}")
            return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the current price of a symbol with fallback
        """
        try:
            # Try broker first
            price = self.broker.get_current_price(symbol)
            
            if price is not None:
                return price
            
            # Fallback to Yahoo Finance
            logger.warning(f"Failed to get current price for {symbol} from broker. Falling back to Yahoo Finance.")
            
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d")
                
                if not data.empty:
                    return data['Close'].iloc[-1]
                else:
                    logger.warning(f"No data returned from Yahoo Finance for {symbol}.")
                    return None
            except Exception as e:
                logger.error(f"Error getting current price from Yahoo Finance: {e}")
                return None
        except Exception as e:
            logger.error(f"Error in get_current_price: {e}")
            return None

    def check_market_hours(self) -> bool:
        """
        Check if the market is currently open
        """
        try:
            return self.broker.check_market_hours()
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False

    def get_next_market_times(self) -> tuple:
        """
        Get the next market open and close times
        """
        try:
            return self.broker.get_next_market_times()
        except Exception as e:
            logger.error(f"Error getting next market times: {e}")
            return (None, None) 