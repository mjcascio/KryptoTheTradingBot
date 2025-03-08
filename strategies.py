import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any, List
import ta
from config import BREAKOUT_PARAMS, TREND_PARAMS
import logging

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self):
        self.breakout_params = BREAKOUT_PARAMS
        self.trend_params = TREND_PARAMS

    def update_parameters(self, new_params: Dict[str, Any]):
        """
        Update strategy parameters
        
        Args:
            new_params: Dictionary with new parameter values
        """
        # Update breakout parameters
        for key, value in new_params.items():
            if key in self.breakout_params:
                self.breakout_params[key] = value
            elif key in self.trend_params:
                self.trend_params[key] = value
                
        logger.info(f"Strategy parameters updated")

    def calculate_breakout_score(self, data: pd.DataFrame) -> float:
        """
        Calculate breakout score based on price action and volume
        Returns a score between 0 and 1
        """
        try:
            # Check for NaN values
            if data.isnull().values.any():
                data = data.ffill().bfill()  # Forward fill then backward fill
                
            # Calculate volume moving average
            volume_ma = data['volume'].rolling(window=self.breakout_params['lookback_period']).mean()
            volume_ratio = data['volume'] / volume_ma

            # Calculate price ranges
            high_low_range = data['high'] - data['low']
            avg_range = high_low_range.rolling(window=self.breakout_params['lookback_period']).mean()
            
            # Identify consolidation
            is_consolidating = high_low_range < (data['close'] * self.breakout_params['consolidation_threshold'])
            
            # Calculate price movement
            price_change = abs(data['close'].pct_change())
            
            # Breakout conditions
            volume_breakout = volume_ratio > self.breakout_params['volume_threshold']
            price_breakout = price_change > self.breakout_params['price_threshold']
            
            # Previous consolidation
            prev_consolidation = is_consolidating.shift(1)
            
            # Fill NaN values with 0
            volume_breakout = volume_breakout.fillna(0).astype(int)
            price_breakout = price_breakout.fillna(0).astype(int)
            prev_consolidation = prev_consolidation.fillna(0).astype(int)
            
            # Combined score
            breakout_score = (
                (volume_breakout * 0.4) +
                (price_breakout * 0.4) +
                (prev_consolidation * 0.2)
            )
            
            return float(breakout_score.iloc[-1])
        except Exception as e:
            logger.error(f"Error calculating breakout score: {str(e)}")
            return 0.0

    def calculate_trend_score(self, data: pd.DataFrame) -> float:
        """
        Calculate trend score using moving averages and RSI
        Returns a score between 0 and 1
        """
        try:
            # Check for NaN values
            if data.isnull().values.any():
                data = data.ffill().bfill()  # Forward fill then backward fill
                
            # Calculate moving averages
            short_ma = data['close'].rolling(window=self.trend_params['short_ma']).mean()
            medium_ma = data['close'].rolling(window=self.trend_params['medium_ma']).mean()
            long_ma = data['close'].rolling(window=self.trend_params['long_ma']).mean()
            
            # Calculate RSI
            rsi = ta.momentum.RSIIndicator(
                data['close'], 
                window=self.trend_params['rsi_period']
            ).rsi()
            
            # Calculate volume trend
            volume_ma = data['volume'].rolling(window=self.trend_params['volume_ma']).mean()
            volume_trend = data['volume'] > volume_ma
            
            # Fill NaN values
            short_ma = short_ma.fillna(data['close'].mean())
            medium_ma = medium_ma.fillna(data['close'].mean())
            long_ma = long_ma.fillna(data['close'].mean())
            rsi = rsi.fillna(50.0)
            volume_trend = volume_trend.fillna(False)
            
            # Trend alignment score
            price = data['close'].iloc[-1]
            trend_aligned = (
                (price > short_ma.iloc[-1]) and
                (short_ma.iloc[-1] > medium_ma.iloc[-1]) and
                (medium_ma.iloc[-1] > long_ma.iloc[-1])
            )
            
            # RSI conditions
            rsi_value = rsi.iloc[-1]
            rsi_trend = 0
            if rsi_value > self.trend_params['rsi_overbought']:
                rsi_trend = 1
            elif rsi_value < self.trend_params['rsi_oversold']:
                rsi_trend = -1
                
            # Combined score
            trend_score = (
                (trend_aligned * 0.5) +
                (abs(rsi_trend) * 0.3) +
                (volume_trend.iloc[-1] * 0.2)
            )
            
            return float(trend_score)
        except Exception as e:
            logger.error(f"Error calculating trend score: {str(e)}")
            return 0.0

    def calculate_mean_reversion_score(self, data: pd.DataFrame) -> float:
        """
        Calculate mean reversion score
        Returns a score between 0 and 1
        """
        try:
            # Calculate Bollinger Bands
            bb_indicator = ta.volatility.BollingerBands(
                data['close'], 
                window=20, 
                window_dev=2
            )
            upper_band = bb_indicator.bollinger_hband()
            lower_band = bb_indicator.bollinger_lband()
            
            # Calculate RSI
            rsi = ta.momentum.RSIIndicator(
                data['close'], 
                window=14
            ).rsi()
            
            # Calculate distance from bands
            price = data['close'].iloc[-1]
            upper_distance = (upper_band.iloc[-1] - price) / price
            lower_distance = (price - lower_band.iloc[-1]) / price
            
            # Oversold/overbought conditions
            oversold = (price < lower_band.iloc[-1]) and (rsi.iloc[-1] < 30)
            overbought = (price > upper_band.iloc[-1]) and (rsi.iloc[-1] > 70)
            
            # Mean reversion score
            if oversold:
                score = 0.8  # Strong buy signal
            elif overbought:
                score = 0.2  # Strong sell signal
            else:
                # Neutral zone - score based on RSI
                rsi_score = 1 - (rsi.iloc[-1] / 100)  # Lower RSI = higher score
                band_position = lower_distance / (upper_distance + lower_distance)
                score = (rsi_score * 0.6) + (band_position * 0.4)
                
            return float(score)
        except Exception as e:
            logger.error(f"Error calculating mean reversion score: {str(e)}")
            return 0.0

    def calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """
        Calculate momentum score
        Returns a score between 0 and 1
        """
        try:
            # Calculate momentum indicators
            price_momentum = data['close'].pct_change(5)
            
            # Calculate MACD
            macd = ta.trend.MACD(
                data['close'],
                window_slow=26,
                window_fast=12,
                window_sign=9
            )
            macd_line = macd.macd()
            signal_line = macd.macd_signal()
            
            # Calculate ADX (trend strength)
            adx = ta.trend.ADXIndicator(
                data['high'],
                data['low'],
                data['close'],
                window=14
            ).adx()
            
            # Momentum conditions
            price_momentum_positive = price_momentum.iloc[-1] > 0
            macd_positive = macd_line.iloc[-1] > signal_line.iloc[-1]
            strong_trend = adx.iloc[-1] > 25
            
            # Combined score
            momentum_score = (
                (price_momentum_positive * 0.4) +
                (macd_positive * 0.4) +
                (strong_trend * 0.2)
            )
            
            return float(momentum_score)
        except Exception as e:
            logger.error(f"Error calculating momentum score: {str(e)}")
            return 0.0

    def analyze_trade_opportunity(self, data: pd.DataFrame) -> Tuple[float, Dict]:
        """
        Analyze trading opportunity and return success probability and trade parameters
        """
        try:
            # Check if we have enough data
            min_required = max(
                self.trend_params['long_ma'],
                self.breakout_params['lookback_period']
            ) + 5  # Add buffer
            
            if len(data) < min_required:
                logger.warning(f"Insufficient data: {len(data)} rows, need at least {min_required}")
                return 0.0, {
                    'entry_price': 0,
                    'stop_loss': 0,
                    'take_profit': 0,
                    'position_size_modifier': 0,
                    'breakout_score': 0,
                    'trend_score': 0
                }
                
            # Check for NaN values
            if data.isnull().values.any():
                data = data.ffill().bfill()  # Forward fill then backward fill
            
            breakout_score = self.calculate_breakout_score(data)
            trend_score = self.calculate_trend_score(data)
            
            # Calculate combined probability
            success_probability = (breakout_score * 0.5) + (trend_score * 0.5)
            
            # Calculate optimal position size based on volatility
            volatility = data['close'].pct_change().std()
            if pd.isna(volatility) or volatility == 0:
                position_size_modifier = 1.0
            else:
                position_size_modifier = 1.0 / (volatility * 100)  # Adjust position size based on volatility
            
            # Determine stop loss and take profit levels
            current_price = data['close'].iloc[-1]
            
            # Calculate ATR
            atr_indicator = ta.volatility.AverageTrueRange(
                data['high'], 
                data['low'], 
                data['close']
            )
            atr = atr_indicator.average_true_range().iloc[-1]
            
            # Handle NaN ATR
            if pd.isna(atr) or atr == 0:
                atr = current_price * 0.02  # Default to 2% of price
            
            trade_params = {
                'entry_price': current_price,
                'stop_loss': current_price - (2 * atr),  # 2 ATR for stop loss
                'take_profit': current_price + (6 * atr),  # 6 ATR for take profit
                'position_size_modifier': position_size_modifier,
                'breakout_score': breakout_score,
                'trend_score': trend_score
            }
            
            return success_probability, trade_params
        except Exception as e:
            logger.error(f"Error analyzing trade opportunity: {str(e)}")
            return 0.0, {
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'position_size_modifier': 0,
                'breakout_score': 0,
                'trend_score': 0
            }

    def analyze_with_params(self, data: pd.DataFrame, strategy_params: Dict[str, Any]) -> Tuple[float, Dict]:
        """
        Analyze trading opportunity with specific parameters
        
        Args:
            data: DataFrame with OHLCV data
            strategy_params: Dictionary with strategy parameters
            
        Returns:
            Tuple of (success_probability, trade_parameters)
        """
        try:
            # Save original parameters
            original_breakout = self.breakout_params.copy()
            original_trend = self.trend_params.copy()
            
            # Update parameters temporarily
            for key, value in strategy_params.items():
                if key in self.breakout_params:
                    self.breakout_params[key] = value
                elif key in self.trend_params:
                    self.trend_params[key] = value
            
            # Analyze with temporary parameters
            result = self.analyze_trade_opportunity(data)
            
            # Restore original parameters
            self.breakout_params = original_breakout
            self.trend_params = original_trend
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing with custom parameters: {str(e)}")
            # Restore original parameters in case of error
            self.breakout_params = original_breakout
            self.trend_params = original_trend
            return 0.0, {'entry_price': 0, 'stop_loss': 0, 'take_profit': 0, 'position_size_modifier': 0} 