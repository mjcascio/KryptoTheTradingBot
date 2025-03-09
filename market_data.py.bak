import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self, alpaca_api):
        self.alpaca = alpaca_api
        self.data_source = 'alpaca'  # Default to Alpaca
        self.fallback_attempts = 0
        self.max_fallback_attempts = 3
        
    def _get_timeframe_params(self, timeframe: str) -> tuple:
        """Convert Alpaca timeframe to Yahoo Finance parameters"""
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
        Get market data with fallback between Alpaca and Yahoo Finance
        """
        try:
            if self.data_source == 'alpaca':
                try:
                    # Try Alpaca first
                    bars = self.alpaca.get_bars(
                        symbol,
                        timeframe,
                        limit=limit,
                        adjustment='raw'
                    ).df
                    
                    if not bars.empty:
                        logger.info(f"Successfully fetched data from Alpaca for {symbol}")
                        self.fallback_attempts = 0  # Reset fallback counter
                        return bars
                    
                except Exception as e:
                    logger.warning(f"Alpaca data fetch failed for {symbol}: {str(e)}")
                    self.fallback_attempts += 1
                    
                # If we've had multiple Alpaca failures, switch to Yahoo Finance
                if self.fallback_attempts >= self.max_fallback_attempts:
                    logger.info("Switching to Yahoo Finance as primary data source")
                    self.data_source = 'yahoo'
            
            # Fallback to Yahoo Finance
            if self.data_source == 'yahoo':
                interval, period = self._get_timeframe_params(timeframe)
                ticker = yf.Ticker(symbol)
                bars = ticker.history(period=period, interval=interval)
                
                # Rename columns to match Alpaca format
                bars.rename(columns={
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                }, inplace=True)
                
                # Take only the required number of rows
                bars = bars.tail(limit)
                
                if not bars.empty:
                    logger.info(f"Successfully fetched data from Yahoo Finance for {symbol}")
                    return bars
                    
            logger.error(f"Failed to fetch market data for {symbol} from both sources")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return None
            
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price with fallback between Alpaca and Yahoo Finance
        """
        try:
            if self.data_source == 'alpaca':
                try:
                    trade = self.alpaca.get_latest_trade(symbol)
                    return float(trade.price)
                except Exception as e:
                    logger.warning(f"Alpaca price fetch failed for {symbol}: {str(e)}")
                    
            # Fallback or primary if using Yahoo
            ticker = yf.Ticker(symbol)
            current = ticker.history(period='1d', interval='1m').iloc[-1]
            return float(current['Close'])
            
        except Exception as e:
            logger.error(f"Error fetching current price: {str(e)}")
            return None
            
    def check_market_hours(self) -> bool:
        """
        Check if market is open with fallback
        """
        try:
            if self.data_source == 'alpaca':
                try:
                    clock = self.alpaca.get_clock()
                    return clock.is_open
                except Exception as e:
                    logger.warning(f"Alpaca market hours check failed: {str(e)}")
                    
            # Fallback to manual check for market hours
            now = datetime.now().astimezone(pd.Timestamp.tz_localize(None).tz_localize('America/New_York'))
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            return (
                now.weekday() < 5 and  # Monday to Friday
                market_open <= now <= market_close
            )
            
        except Exception as e:
            logger.error(f"Error checking market hours: {str(e)}")
            return False
            
    def get_next_market_times(self) -> tuple:
        """
        Get the next market open and close times
        
        Returns:
            tuple: (next_open_time, next_close_time) as formatted strings
        """
        try:
            if self.data_source == 'alpaca':
                try:
                    clock = self.alpaca.get_clock()
                    next_open = clock.next_open.strftime('%Y-%m-%d %H:%M:%S')
                    next_close = clock.next_close.strftime('%Y-%m-%d %H:%M:%S')
                    return next_open, next_close
                except Exception as e:
                    logger.warning(f"Alpaca market times check failed: {str(e)}")
            
            # Fallback to manual calculation
            now = datetime.now().astimezone(pd.Timestamp.tz_localize(None).tz_localize('America/New_York'))
            
            # Calculate next open time
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            # If it's after market close or weekend, find next trading day
            if now.weekday() >= 5:  # Weekend
                days_to_monday = 7 - now.weekday() + 0  # Days until next Monday
                next_open_date = now + timedelta(days=days_to_monday)
                next_open_date = next_open_date.replace(hour=9, minute=30, second=0, microsecond=0)
                next_close_date = next_open_date.replace(hour=16, minute=0, second=0, microsecond=0)
            elif now >= market_close:  # After market close
                if now.weekday() == 4:  # Friday
                    next_open_date = now + timedelta(days=3)  # Next Monday
                else:
                    next_open_date = now + timedelta(days=1)  # Next day
                next_open_date = next_open_date.replace(hour=9, minute=30, second=0, microsecond=0)
                next_close_date = next_open_date.replace(hour=16, minute=0, second=0, microsecond=0)
            elif now <= market_open:  # Before market open
                next_open_date = market_open
                next_close_date = market_close
            else:  # During market hours
                next_open_date = now + timedelta(days=1)
                if next_open_date.weekday() >= 5:  # If next day is weekend
                    days_to_monday = 7 - next_open_date.weekday() + 0  # Days until next Monday
                    next_open_date = now + timedelta(days=days_to_monday)
                next_open_date = next_open_date.replace(hour=9, minute=30, second=0, microsecond=0)
                next_close_date = market_close
                
            next_open = next_open_date.strftime('%Y-%m-%d %H:%M:%S')
            next_close = next_close_date.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Calculated next market times: Open={next_open}, Close={next_close}")
            return next_open, next_close
            
        except Exception as e:
            logger.error(f"Error getting next market times: {str(e)}")
            # Return default values instead of "Unknown"
            now = datetime.now()
            if now.weekday() >= 5:  # Weekend
                days_to_monday = 7 - now.weekday() + 0
                next_day = now + timedelta(days=days_to_monday)
            else:
                next_day = now + timedelta(days=1)
            
            next_open = next_day.replace(hour=9, minute=30, second=0).strftime('%Y-%m-%d %H:%M:%S')
            next_close = next_day.replace(hour=16, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
            return next_open, next_close 