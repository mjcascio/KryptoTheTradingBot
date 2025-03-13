#!/usr/bin/env python3
"""
Trading Bot ML Patch

This script patches the trading bot to integrate ML models.
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
import numpy as np

# Import our ML integration
from ml_integration import get_ml_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot_ml_patch.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def patch_trading_bot():
    """
    Patch the trading bot to integrate ML models
    
    This function monkey patches the trading bot's _scan_for_opportunities method
    to integrate ML signal enhancement and anomaly detection.
    """
    try:
        # Import the trading bot
        from trading_bot import TradingBot
        
        # Get the original method
        original_scan_for_opportunities = TradingBot._scan_for_opportunities
        
        # Get ML integration
        ml_integration = get_ml_integration()
        
        # Define the patched method
        def patched_scan_for_opportunities(self):
            """
            Patched method to scan for trading opportunities with ML enhancement
            """
            logger.info("Running patched _scan_for_opportunities with ML enhancement")
            
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
                    
                    # Check for anomalies
                    anomaly_result = ml_integration.check_for_anomalies(data, symbol)
                    
                    # If an anomaly is detected, log it and potentially adjust strategy
                    if anomaly_result.get('is_anomaly', False):
                        logger.info(f"Anomaly detected for {symbol}: score={anomaly_result.get('score', 0.0):.4f}")
                        
                        # Add to dashboard if available
                        if hasattr(self, 'dashboard') and self.dashboard:
                            self.dashboard.add_bot_activity({
                                'message': f"Anomaly detected for {symbol}: score={anomaly_result.get('score', 0.0):.4f}",
                                'level': 'warning',
                                'timestamp': datetime.now().isoformat()
                            })
                    
                    # Check each strategy for signals
                    for strategy_name, strategy in self.strategies.items():
                        signal = strategy.generate_signal(data)
                        
                        if signal['action'] == 'buy':
                            # Enhance signal with ML
                            enhanced_signal = ml_integration.enhance_signal(data, signal)
                            
                            # If signal was rejected by ML, skip
                            if enhanced_signal is None:
                                logger.info(f"Signal for {symbol} rejected by ML enhancer")
                                continue
                            
                            # Use enhanced signal
                            signal = enhanced_signal
                            
                            if signal['probability'] >= self.min_success_probability:
                                # Calculate position size
                                base_position_size = self._calculate_position_size(symbol, equity)
                                
                                # Adjust position size based on ML confidence
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
        
        # Also patch the start method to connect ML integration
        original_start = TradingBot.start
        
        def patched_start(self):
            """
            Patched method to start the trading bot with ML integration
            """
            logger.info("Starting trading bot with ML integration")
            
            # Connect ML integration to the bot
            ml_integration.connect_to_bot(self)
            
            # Call the original start method
            return original_start(self)
        
        # Patch the start method
        TradingBot.start = patched_start
        
        logger.info("Successfully patched trading bot with ML integration")
        return True
    except Exception as e:
        logger.error(f"Error patching trading bot: {e}")
        return False

def main():
    """Main function"""
    logger.info("Applying ML patch to trading bot...")
    
    success = patch_trading_bot()
    
    if success:
        logger.info("ML patch applied successfully")
    else:
        logger.error("Failed to apply ML patch")

if __name__ == "__main__":
    main() 