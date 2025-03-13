#!/usr/bin/env python3
"""
Forecasting Integration Module

This module integrates the time series forecasting models with the trading bot
to enhance trading decisions based on price forecasts.
"""

import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("forecasting_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the time series forecaster
try:
    from time_series_forecasting import TimeSeriesForecaster
except ImportError:
    logger.error("Could not import TimeSeriesForecaster. Make sure time_series_forecasting.py is in the same directory.")
    sys.exit(1)

class ForecastingIntegration:
    """
    Integrates time series forecasting models with the trading bot
    to enhance trading decisions based on price forecasts.
    """
    
    def __init__(self, settings_path='config/forecasting_settings.json'):
        """
        Initialize the forecasting integration
        
        Args:
            settings_path: Path to the forecasting settings JSON file
        """
        self.settings_path = settings_path
        self.settings = self._load_settings()
        
        # Initialize forecasters
        self.forecasters = {}
        self._initialize_forecasters()
        
        # Cache for forecasts
        self.forecast_cache = {}
        
        logger.info("Forecasting integration initialized")
    
    def _load_settings(self):
        """
        Load forecasting settings from JSON file
        
        Returns:
            Dictionary with settings
        """
        # Default settings
        default_settings = {
            "enabled": True,
            "model_types": ["lstm", "gru"],
            "sequence_length": 60,
            "forecast_horizon": 5,
            "confidence_threshold": 0.7,
            "min_trend_strength": 0.02,
            "use_for_entry": True,
            "use_for_exit": True,
            "use_for_position_sizing": True,
            "position_size_multiplier": 1.5,
            "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"],
            "update_frequency": 24,  # hours
            "last_update": None
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        
        # Load settings if file exists
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
                
                # Update default settings with loaded settings
                default_settings.update(settings)
                logger.info(f"Loaded forecasting settings from {self.settings_path}")
            except Exception as e:
                logger.error(f"Error loading forecasting settings: {e}")
        else:
            # Save default settings
            self._save_settings(default_settings)
            logger.info(f"Created default forecasting settings at {self.settings_path}")
        
        return default_settings
    
    def _save_settings(self, settings=None):
        """
        Save forecasting settings to JSON file
        
        Args:
            settings: Dictionary with settings to save
        """
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4, default=str)
            logger.info(f"Saved forecasting settings to {self.settings_path}")
        except Exception as e:
            logger.error(f"Error saving forecasting settings: {e}")
    
    def _initialize_forecasters(self):
        """Initialize forecasters for each model type"""
        if not self.settings["enabled"]:
            logger.info("Forecasting is disabled in settings")
            return
        
        for model_type in self.settings["model_types"]:
            try:
                forecaster = TimeSeriesForecaster(
                    model_type=model_type,
                    sequence_length=self.settings["sequence_length"],
                    forecast_horizon=self.settings["forecast_horizon"]
                )
                self.forecasters[model_type] = forecaster
                logger.info(f"Initialized {model_type.upper()} forecaster")
            except Exception as e:
                logger.error(f"Error initializing {model_type.upper()} forecaster: {e}")
    
    def _should_update_forecasts(self):
        """
        Check if forecasts should be updated based on the update frequency
        
        Returns:
            Boolean indicating if forecasts should be updated
        """
        if not self.settings["enabled"]:
            return False
        
        last_update = self.settings["last_update"]
        
        if last_update is None:
            return True
        
        # Parse last update time
        if isinstance(last_update, str):
            last_update = datetime.fromisoformat(last_update)
        
        # Check if update frequency has passed
        time_since_update = datetime.now() - last_update
        hours_since_update = time_since_update.total_seconds() / 3600
        
        return hours_since_update >= self.settings["update_frequency"]
    
    def update_forecasts(self, data_provider=None):
        """
        Update forecasts for all symbols
        
        Args:
            data_provider: Function to fetch historical data for a symbol
            
        Returns:
            Dictionary with forecast results
        """
        if not self.settings["enabled"]:
            logger.info("Forecasting is disabled in settings")
            return {}
        
        if not self._should_update_forecasts():
            logger.info("Forecasts are up to date")
            return self.forecast_cache
        
        # Import data fetching module if not provided
        if data_provider is None:
            try:
                from train_ml_model import fetch_historical_data
                data_provider = fetch_historical_data
            except ImportError:
                logger.error("Could not import fetch_historical_data. Please provide a data provider function.")
                return {}
        
        # Update forecasts for each symbol
        forecast_results = {}
        
        for symbol in self.settings["symbols"]:
            try:
                # Fetch historical data
                data = data_provider(symbol, period='2y', interval='1d')
                
                if data is None or len(data) < 100:
                    logger.warning(f"Insufficient data for {symbol}")
                    continue
                
                # Set date as index
                data.set_index('date', inplace=True)
                
                # Generate forecasts for each model type
                symbol_forecasts = {}
                
                for model_type, forecaster in self.forecasters.items():
                    # Generate forecast
                    forecast = forecaster.predict(data, target_column='close')
                    
                    if forecast is not None:
                        # Plot forecast
                        plot_path = forecaster.plot_forecast(data, forecast, target_column='close')
                        
                        # Calculate trend strength
                        trend = self._calculate_trend_strength(forecast)
                        
                        # Store forecast
                        symbol_forecasts[model_type] = {
                            'forecast': forecast.to_dict(),
                            'trend': trend,
                            'plot_path': plot_path
                        }
                        
                        logger.info(f"Generated {model_type.upper()} forecast for {symbol} with trend {trend:.4f}")
                
                # Combine forecasts
                if symbol_forecasts:
                    combined_forecast = self._combine_forecasts(symbol_forecasts)
                    symbol_forecasts['combined'] = combined_forecast
                    forecast_results[symbol] = symbol_forecasts
            
            except Exception as e:
                logger.error(f"Error updating forecasts for {symbol}: {e}")
        
        # Update cache and last update time
        self.forecast_cache = forecast_results
        self.settings["last_update"] = datetime.now()
        self._save_settings()
        
        return forecast_results
    
    def _calculate_trend_strength(self, forecast):
        """
        Calculate the strength and direction of the trend in the forecast
        
        Args:
            forecast: DataFrame with forecast data
            
        Returns:
            Float indicating trend strength (positive for uptrend, negative for downtrend)
        """
        if forecast is None or len(forecast) < 2:
            return 0.0
        
        # Calculate percentage change from first to last forecast point
        first_value = forecast['forecast'].iloc[0]
        last_value = forecast['forecast'].iloc[-1]
        
        if first_value == 0:
            return 0.0
        
        trend = (last_value - first_value) / first_value
        
        return trend
    
    def _combine_forecasts(self, symbol_forecasts):
        """
        Combine forecasts from different models
        
        Args:
            symbol_forecasts: Dictionary with forecasts from different models
            
        Returns:
            Dictionary with combined forecast
        """
        # Extract forecasts
        forecasts = {}
        trends = {}
        
        for model_type, forecast_data in symbol_forecasts.items():
            if 'forecast' in forecast_data:
                forecasts[model_type] = pd.DataFrame.from_dict(forecast_data['forecast'])
                trends[model_type] = forecast_data['trend']
        
        if not forecasts:
            return None
        
        # Get dates from the first forecast
        first_model = list(forecasts.keys())[0]
        dates = forecasts[first_model].index
        
        # Combine forecasts with equal weights
        combined_values = np.zeros(len(dates))
        
        for model_type, forecast_df in forecasts.items():
            combined_values += forecast_df['forecast'].values
        
        combined_values /= len(forecasts)
        
        # Create combined forecast DataFrame
        combined_df = pd.DataFrame({
            'forecast': combined_values
        }, index=dates)
        
        # Calculate combined trend
        combined_trend = sum(trends.values()) / len(trends)
        
        # Create plot for combined forecast
        plot_path = self._plot_combined_forecast(forecasts, combined_df)
        
        return {
            'forecast': combined_df.to_dict(),
            'trend': combined_trend,
            'plot_path': plot_path,
            'model_trends': trends
        }
    
    def _plot_combined_forecast(self, forecasts, combined_df):
        """
        Plot combined forecast with individual model forecasts
        
        Args:
            forecasts: Dictionary with forecasts from different models
            combined_df: DataFrame with combined forecast
            
        Returns:
            Path to saved plot
        """
        try:
            plt.figure(figsize=(12, 6))
            
            # Plot individual forecasts
            for model_type, forecast_df in forecasts.items():
                plt.plot(forecast_df.index, forecast_df['forecast'], label=f'{model_type.upper()} Forecast', alpha=0.5)
            
            # Plot combined forecast
            plt.plot(combined_df.index, combined_df['forecast'], label='Combined Forecast', linewidth=2, color='black')
            
            plt.title('Combined Price Forecast')
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.legend()
            
            # Format x-axis dates
            plt.gcf().autofmt_xdate()
            
            # Save plot
            plot_path = 'results/forecasting/combined_forecast.png'
            plt.savefig(plot_path)
            
            return plot_path
            
        except Exception as e:
            logger.error(f"Error plotting combined forecast: {e}")
            return None
    
    def get_forecast(self, symbol):
        """
        Get the latest forecast for a symbol
        
        Args:
            symbol: Symbol to get forecast for
            
        Returns:
            Dictionary with forecast data
        """
        if not self.settings["enabled"]:
            return None
        
        # Update forecasts if needed
        if self._should_update_forecasts():
            self.update_forecasts()
        
        # Return forecast from cache
        if symbol in self.forecast_cache:
            return self.forecast_cache[symbol]
        
        return None
    
    def get_trend_signal(self, symbol):
        """
        Get a trading signal based on the forecast trend
        
        Args:
            symbol: Symbol to get signal for
            
        Returns:
            Dictionary with signal information
        """
        if not self.settings["enabled"]:
            return {"signal": "neutral", "strength": 0.0, "confidence": 0.0}
        
        forecast_data = self.get_forecast(symbol)
        
        if forecast_data is None or 'combined' not in forecast_data:
            return {"signal": "neutral", "strength": 0.0, "confidence": 0.0}
        
        # Get combined trend
        trend = forecast_data['combined']['trend']
        
        # Calculate signal
        min_trend = self.settings["min_trend_strength"]
        
        if trend > min_trend:
            signal = "buy"
        elif trend < -min_trend:
            signal = "sell"
        else:
            signal = "neutral"
        
        # Calculate strength (normalized trend)
        strength = min(abs(trend) * 5, 1.0)  # Scale trend and cap at 1.0
        
        # Calculate confidence based on agreement between models
        model_trends = forecast_data['combined']['model_trends']
        trend_signs = [1 if t > 0 else -1 if t < 0 else 0 for t in model_trends.values()]
        
        if len(trend_signs) > 0:
            # Count how many models agree with the combined trend sign
            combined_sign = 1 if trend > 0 else -1 if trend < 0 else 0
            agreements = sum(1 for sign in trend_signs if sign == combined_sign)
            confidence = agreements / len(trend_signs)
        else:
            confidence = 0.0
        
        return {
            "signal": signal,
            "strength": strength,
            "confidence": confidence,
            "trend": trend
        }
    
    def adjust_position_size(self, symbol, base_size):
        """
        Adjust position size based on forecast trend strength
        
        Args:
            symbol: Symbol to adjust position size for
            base_size: Base position size
            
        Returns:
            Adjusted position size
        """
        if not self.settings["enabled"] or not self.settings["use_for_position_sizing"]:
            return base_size
        
        signal = self.get_trend_signal(symbol)
        
        if signal["signal"] == "neutral" or signal["confidence"] < self.settings["confidence_threshold"]:
            return base_size
        
        # Adjust position size based on trend strength and confidence
        multiplier = 1.0
        
        if signal["signal"] == "buy":
            # Increase position size for buy signals
            multiplier = 1.0 + (signal["strength"] * signal["confidence"] * 
                               (self.settings["position_size_multiplier"] - 1.0))
        elif signal["signal"] == "sell":
            # Decrease position size for sell signals
            multiplier = 1.0 - (signal["strength"] * signal["confidence"] * 0.5)
        
        adjusted_size = base_size * multiplier
        
        logger.info(f"Adjusted position size for {symbol} from {base_size} to {adjusted_size} based on forecast")
        
        return adjusted_size
    
    def should_enter_trade(self, symbol, side):
        """
        Determine if a trade should be entered based on forecast
        
        Args:
            symbol: Symbol to check
            side: Trade side ('buy' or 'sell')
            
        Returns:
            Boolean indicating if trade should be entered
        """
        if not self.settings["enabled"] or not self.settings["use_for_entry"]:
            return True
        
        signal = self.get_trend_signal(symbol)
        
        # If confidence is below threshold, don't use forecast for entry decision
        if signal["confidence"] < self.settings["confidence_threshold"]:
            return True
        
        # Check if forecast signal matches trade side
        if side == "buy" and signal["signal"] == "buy":
            return True
        elif side == "sell" and signal["signal"] == "sell":
            return True
        elif signal["signal"] == "neutral":
            return True
        
        # Forecast contradicts trade side
        logger.info(f"Forecast for {symbol} contradicts {side} signal, skipping trade")
        return False
    
    def should_exit_trade(self, symbol, side):
        """
        Determine if a trade should be exited based on forecast
        
        Args:
            symbol: Symbol to check
            side: Current position side ('long' or 'short')
            
        Returns:
            Boolean indicating if trade should be exited
        """
        if not self.settings["enabled"] or not self.settings["use_for_exit"]:
            return False
        
        signal = self.get_trend_signal(symbol)
        
        # If confidence is below threshold, don't use forecast for exit decision
        if signal["confidence"] < self.settings["confidence_threshold"]:
            return False
        
        # Check if forecast signal contradicts position side
        if side == "long" and signal["signal"] == "sell":
            logger.info(f"Forecast for {symbol} suggests exiting long position")
            return True
        elif side == "short" and signal["signal"] == "buy":
            logger.info(f"Forecast for {symbol} suggests exiting short position")
            return True
        
        return False
    
    def patch_trading_bot(self, bot):
        """
        Patch the trading bot to integrate forecasting
        
        Args:
            bot: Trading bot instance
            
        Returns:
            Patched trading bot
        """
        if not self.settings["enabled"]:
            logger.info("Forecasting is disabled, not patching trading bot")
            return bot
        
        logger.info("Patching trading bot with forecasting integration")
        
        # Store original methods
        original_scan = bot._scan_for_opportunities
        original_calculate_position_size = bot._calculate_position_size
        original_execute_trade = bot._execute_trade
        
        # Patch _scan_for_opportunities method
        @wraps(original_scan)
        def patched_scan(self, *args, **kwargs):
            # Call original method
            opportunities = original_scan(*args, **kwargs)
            
            if opportunities:
                # Filter opportunities based on forecast
                filtered_opportunities = []
                
                for opportunity in opportunities:
                    symbol = opportunity.get('symbol')
                    side = opportunity.get('side')
                    
                    if symbol and side:
                        # Check if trade should be entered based on forecast
                        if self.forecasting.should_enter_trade(symbol, side):
                            filtered_opportunities.append(opportunity)
                    else:
                        # If symbol or side is missing, keep the opportunity
                        filtered_opportunities.append(opportunity)
                
                return filtered_opportunities
            
            return opportunities
        
        # Patch _calculate_position_size method
        @wraps(original_calculate_position_size)
        def patched_calculate_position_size(self, symbol, *args, **kwargs):
            # Call original method
            base_size = original_calculate_position_size(symbol, *args, **kwargs)
            
            # Adjust position size based on forecast
            adjusted_size = self.forecasting.adjust_position_size(symbol, base_size)
            
            return adjusted_size
        
        # Patch _execute_trade method
        @wraps(original_execute_trade)
        def patched_execute_trade(self, *args, **kwargs):
            # Call original method
            result = original_execute_trade(*args, **kwargs)
            
            # Check if any positions should be exited based on forecast
            if hasattr(self, 'positions'):
                for symbol, position in self.positions.items():
                    side = position.get('side')
                    
                    if side and self.forecasting.should_exit_trade(symbol, side):
                        # Exit position
                        logger.info(f"Exiting {side} position for {symbol} based on forecast")
                        self.exit_position(symbol)
            
            return result
        
        # Attach forecasting instance to bot
        bot.forecasting = self
        
        # Apply patches
        bot._scan_for_opportunities = patched_scan.__get__(bot, type(bot))
        bot._calculate_position_size = patched_calculate_position_size.__get__(bot, type(bot))
        bot._execute_trade = patched_execute_trade.__get__(bot, type(bot))
        
        return bot

def main():
    """Main function for testing"""
    logger.info("Testing forecasting integration...")
    
    try:
        # Create forecasting integration
        forecasting = ForecastingIntegration()
        
        # Update forecasts
        forecasts = forecasting.update_forecasts()
        
        # Print forecast results
        for symbol, forecast_data in forecasts.items():
            if 'combined' in forecast_data:
                trend = forecast_data['combined']['trend']
                signal = forecasting.get_trend_signal(symbol)
                
                logger.info(f"Forecast for {symbol}: Trend={trend:.4f}, Signal={signal['signal']}, "
                           f"Strength={signal['strength']:.4f}, Confidence={signal['confidence']:.4f}")
        
        logger.info("Forecasting integration test completed")
        
    except Exception as e:
        logger.error(f"Error testing forecasting integration: {e}")

if __name__ == "__main__":
    main() 