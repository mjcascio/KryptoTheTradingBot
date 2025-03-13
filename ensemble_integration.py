#!/usr/bin/env python3
"""
Ensemble Integration Module

This module integrates the ensemble learning model with the trading bot.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import joblib

# Import our ensemble learning module
from ensemble_learning import EnsembleLearning

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ensemble_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnsembleIntegration:
    """
    Ensemble integration class that connects the ensemble model with the trading bot.
    """
    
    def __init__(self):
        """Initialize the ensemble integration"""
        self.ensemble = EnsembleLearning()
        self.ensemble_enabled = True
        self.confidence_threshold = 0.6
        self.position_size_multiplier = 1.2  # Slightly higher than standard ML
        
        # Load settings if available
        self._load_settings()
        
        # Load ensemble model
        self.ensemble.load_ensemble_model()
        
        logger.info("Ensemble integration initialized")
    
    def _load_settings(self):
        """Load ensemble settings from file"""
        settings_file = 'config/ensemble_settings.json'
        
        if os.path.exists(settings_file):
            try:
                import json
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                self.ensemble_enabled = settings.get('ensemble_enabled', True)
                self.confidence_threshold = settings.get('confidence_threshold', 0.6)
                self.position_size_multiplier = settings.get('position_size_multiplier', 1.2)
                
                logger.info(f"Loaded ensemble settings: {settings}")
            except Exception as e:
                logger.error(f"Error loading ensemble settings: {e}")
    
    def save_settings(self):
        """Save ensemble settings to file"""
        settings_file = 'config/ensemble_settings.json'
        
        # Create directory if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        settings = {
            'ensemble_enabled': self.ensemble_enabled,
            'confidence_threshold': self.confidence_threshold,
            'position_size_multiplier': self.position_size_multiplier,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            import json
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            logger.info(f"Saved ensemble settings: {settings}")
        except Exception as e:
            logger.error(f"Error saving ensemble settings: {e}")
    
    def enhance_signal(self, data, base_signal):
        """
        Enhance a trading signal using the ensemble model
        
        Args:
            data: DataFrame with OHLCV data
            base_signal: Dictionary with base signal parameters
            
        Returns:
            Dictionary with enhanced signal parameters
        """
        if not self.ensemble_enabled:
            logger.info("Ensemble enhancement disabled")
            return base_signal
        
        try:
            # Extract features
            features = self._extract_features(data)
            
            if features is None:
                logger.warning("Failed to extract features")
                return base_signal
            
            # Get latest features
            latest_features = features.iloc[-1:].values
            
            # Get prediction from ensemble model
            y_pred, y_prob = self.ensemble.predict(latest_features)
            
            if y_prob is None:
                logger.warning("No probability available from ensemble model")
                return base_signal
            
            # Get probability of positive class
            probability = y_prob[0][1]
            
            logger.info(f"Ensemble signal enhancement: Base probability: {base_signal['probability']:.2f}, Ensemble probability: {probability:.2f}")
            
            # Check if confidence meets threshold
            if probability < self.confidence_threshold:
                logger.info(f"Ensemble probability {probability:.2f} below threshold {self.confidence_threshold}")
                return None
            
            # Combine ensemble signal with technical signal
            enhanced_signal = {
                'entry_price': base_signal['entry_price'],
                'stop_loss': base_signal['stop_loss'],
                'take_profit': base_signal['take_profit'],
                'ensemble_probability': probability,
                'combined_score': (base_signal['probability'] + probability) / 2,
                'confidence': probability * base_signal['probability'],
                'position_size_modifier': base_signal['position_size_modifier'] * self.position_size_multiplier * probability
            }
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"Error enhancing signal with ensemble: {str(e)}")
            return base_signal
    
    def _extract_features(self, data):
        """
        Extract features for ensemble model
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with extracted features
        """
        try:
            # Check if we have the ML enhancer module
            try:
                from ml_enhancer import MLSignalEnhancer
                ml_enhancer = MLSignalEnhancer()
                return ml_enhancer._extract_features(data)
            except Exception as e:
                logger.error(f"Error using ML enhancer for feature extraction: {e}")
                
                # Fallback to basic feature extraction
                features = pd.DataFrame(index=data.index)
                
                # Calculate basic features
                # RSI
                delta = data['close'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                rs = gain / loss
                features['rsi'] = 100 - (100 / (1 + rs))
                
                # MACD
                ema_fast = data['close'].ewm(span=12, adjust=False).mean()
                ema_slow = data['close'].ewm(span=26, adjust=False).mean()
                features['macd'] = ema_fast - ema_slow
                features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
                
                # Bollinger Bands
                sma = data['close'].rolling(window=20).mean()
                std = data['close'].rolling(window=20).std()
                upper_band = sma + (std * 2)
                lower_band = sma - (std * 2)
                features['bb_upper'] = (data['close'] - upper_band) / upper_band
                features['bb_lower'] = (data['close'] - lower_band) / lower_band
                
                # Volume
                features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
                
                # Price action
                features['price_change'] = data['close'].pct_change(5)
                
                # ATR
                high_low = data['high'] - data['low']
                high_close = (data['high'] - data['close'].shift()).abs()
                low_close = (data['low'] - data['close'].shift()).abs()
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                features['atr'] = tr.rolling(window=14).mean()
                
                # Trend strength
                x = np.arange(50)
                regress_slopes = [0] * 49
                for i in range(49, len(data['close'])):
                    y = data['close'].iloc[i-49:i+1].values
                    slope, _ = np.polyfit(x, y, 1)
                    regress_slopes.append(slope)
                features['trend_strength'] = pd.Series(regress_slopes, index=data.index)
                
                return features.fillna(0)
                
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def get_ensemble_status(self):
        """
        Get the current status of the ensemble model
        
        Returns:
            Dictionary with ensemble status information
        """
        # Check if ensemble model is available
        ensemble_available = os.path.exists('models/ensemble/ensemble_model.joblib')
        
        return {
            'ensemble_enabled': self.ensemble_enabled,
            'ensemble_available': ensemble_available,
            'confidence_threshold': self.confidence_threshold,
            'position_size_multiplier': self.position_size_multiplier,
            'timestamp': datetime.now().isoformat()
        }
    
    def connect_to_bot(self, bot):
        """
        Connect ensemble integration to the trading bot
        
        Args:
            bot: Trading bot instance
        """
        logger.info("Ensemble integration connected to trading bot")

# Create a singleton instance
ensemble_integration = EnsembleIntegration()

def get_ensemble_integration():
    """Get the singleton ensemble integration instance"""
    return ensemble_integration

def patch_trading_bot():
    """
    Patch the trading bot to integrate ensemble model
    
    This function monkey patches the trading bot's _scan_for_opportunities method
    to integrate ensemble signal enhancement.
    """
    try:
        # Import the trading bot
        from trading_bot import TradingBot
        
        # Get the original method
        original_scan_for_opportunities = TradingBot._scan_for_opportunities
        
        # Get ensemble integration
        ensemble_integration = get_ensemble_integration()
        
        # Define the patched method
        def patched_scan_for_opportunities(self):
            """
            Patched method to scan for trading opportunities with ensemble enhancement
            """
            logger.info("Running patched _scan_for_opportunities with ensemble enhancement")
            
            # Call the original method
            original_scan_for_opportunities(self)
            
            # Get the active broker
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker or not active_broker.connected:
                logger.warning("Cannot check for opportunities: No active broker or not connected")
                return
            
            # Check if we've reached the maximum number of trades for the day
            if self.daily_trades >= self.max_trades_per_day:
                logger.info(f"Maximum daily trades reached ({self.max_trades_per_day})")
                return
            
            # Check if we've reached the maximum daily loss
            account_info = active_broker.get_account_info()
            equity = account_info.get('equity', 0.0)
            
            if self.daily_pl < 0 and abs(self.daily_pl) > equity * self.max_daily_loss_pct:
                logger.warning(f"Maximum daily loss reached ({self.max_daily_loss_pct * 100}% of equity)")
                return
            
            # Get the watchlist for the active platform
            watchlist = self._get_platform_watchlist()
            
            # Check each symbol in the watchlist
            for symbol in watchlist:
                try:
                    # Skip if we already have a position in this symbol
                    if symbol in active_broker.get_positions():
                        continue
                    
                    # Get market data for the symbol
                    data = self.market_data.get_market_data(symbol)
                    if data is None or len(data) < 20:  # Need at least 20 bars for analysis
                        continue
                    
                    # Check each strategy for signals
                    for strategy_name, strategy in self.strategies.items():
                        signal = strategy.generate_signal(data)
                        
                        if signal['action'] == 'buy':
                            # Enhance signal with ensemble
                            enhanced_signal = ensemble_integration.enhance_signal(data, signal)
                            
                            # If signal was rejected by ensemble, skip
                            if enhanced_signal is None:
                                logger.info(f"Signal for {symbol} rejected by ensemble enhancer")
                                continue
                            
                            # Use enhanced signal
                            signal = enhanced_signal
                            
                            if signal.get('combined_score', 0) >= self.min_success_probability:
                                # Calculate position size
                                base_position_size = self._calculate_position_size(symbol, equity)
                                
                                # Adjust position size based on ensemble confidence
                                position_size_modifier = signal.get('position_size_modifier', 1.0)
                                position_size = base_position_size * position_size_modifier
                                
                                if position_size < self.min_position_size:
                                    logger.info(f"Skipping {symbol}: Position size too small ({position_size:.2f} < {self.min_position_size})")
                                    continue
                                
                                # Place buy order
                                self._place_order(symbol, position_size, 'buy', strategy_name, signal)
                                
                                # Increment daily trades counter
                                self.daily_trades += 1
                                
                                # Check if we've reached the maximum number of trades for the day
                                if self.daily_trades >= self.max_trades_per_day:
                                    logger.info(f"Maximum daily trades reached ({self.max_trades_per_day})")
                                    break
                except Exception as e:
                    logger.error(f"Error checking trading opportunity for {symbol}: {e}")
        
        # Patch the method
        TradingBot._scan_for_opportunities = patched_scan_for_opportunities
        
        # Also patch the start method to connect ensemble integration
        original_start = TradingBot.start
        
        def patched_start(self):
            """
            Patched method to start the trading bot with ensemble integration
            """
            logger.info("Starting trading bot with ensemble integration")
            
            # Connect ensemble integration to the bot
            ensemble_integration.connect_to_bot(self)
            
            # Call the original start method
            return original_start(self)
        
        # Patch the start method
        TradingBot.start = patched_start
        
        logger.info("Successfully patched trading bot with ensemble integration")
        return True
    except Exception as e:
        logger.error(f"Error patching trading bot: {e}")
        return False

def main():
    """Main function"""
    logger.info("Applying ensemble integration to trading bot...")
    
    success = patch_trading_bot()
    
    if success:
        logger.info("Ensemble integration applied successfully")
    else:
        logger.error("Failed to apply ensemble integration")

if __name__ == "__main__":
    main() 