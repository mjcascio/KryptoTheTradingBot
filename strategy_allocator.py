import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class StrategyAllocator:
    def __init__(self, strategies_config: Dict[str, Dict[str, Any]]):
        """
        Initialize with multiple strategy configurations
        
        Args:
            strategies_config: Dict of strategy names and their configurations
        """
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        self.strategies = {}
        self.performance_metrics = {}
        self.current_weights = {}
        self.lookback_period = 30  # days
        self.history_file = 'data/strategy_allocation_history.json'
        self.allocation_history = []
        
        # Initialize strategies
        for name, config in strategies_config.items():
            self.strategies[name] = config
            self.performance_metrics[name] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'win_rate': 0.5,  # Initial default
                'profit_factor': 1.0,  # Initial default
                'sharpe_ratio': 0.0
            }
            self.current_weights[name] = 1.0 / len(strategies_config)  # Equal weight initially
        
        # Load allocation history
        self._load_history()
        
        logger.info(f"Strategy Allocator initialized with {len(strategies_config)} strategies")
    
    def _load_history(self):
        """Load allocation history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.allocation_history = json.load(f)
                logger.info(f"Loaded strategy allocation history with {len(self.allocation_history)} entries")
            except Exception as e:
                logger.error(f"Error loading strategy allocation history: {str(e)}")
                self.allocation_history = []
        else:
            self.allocation_history = []
    
    def _save_history(self):
        """Save allocation history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.allocation_history, f)
        except Exception as e:
            logger.error(f"Error saving strategy allocation history: {str(e)}")
    
    def detect_market_condition(self, market_data: pd.DataFrame) -> str:
        """
        Detect current market condition
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            String representing market condition
        """
        try:
            # Calculate volatility
            atr = self._calculate_atr(market_data)
            avg_atr = atr.rolling(20).mean().iloc[-1]
            current_atr = atr.iloc[-1]
            
            # Determine trend
            sma50 = market_data['close'].rolling(50).mean().iloc[-1]
            sma200 = market_data['close'].rolling(200).mean().iloc[-1]
            price = market_data['close'].iloc[-1]
            
            # Calculate momentum
            momentum = market_data['close'].pct_change(20).iloc[-1]
            
            # Classify market condition
            if current_atr > avg_atr * 1.5:
                condition = 'volatile'
            elif price > sma50 and sma50 > sma200 and momentum > 0.02:
                condition = 'bullish_trend'
            elif price < sma50 and sma50 < sma200 and momentum < -0.02:
                condition = 'bearish_trend'
            else:
                condition = 'ranging'
                
            logger.info(f"Detected market condition: {condition}")
            return condition
            
        except Exception as e:
            logger.error(f"Error detecting market condition: {str(e)}")
            return 'unknown'
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def get_optimal_strategy(self, symbol: str, market_data: pd.DataFrame, strategy_analyzer) -> Dict:
        """
        Get optimal strategy for current market conditions
        
        Args:
            symbol: Stock symbol
            market_data: DataFrame with OHLCV data
            strategy_analyzer: Strategy analyzer instance
            
        Returns:
            Dictionary with combined signal parameters
        """
        try:
            # Detect market condition
            condition = self.detect_market_condition(market_data)
            
            # Get signals from all strategies
            signals = {}
            for name, config in self.strategies.items():
                # Apply strategy-specific parameters
                success_prob, params = strategy_analyzer.analyze_with_params(market_data, config)
                
                signals[name] = {
                    'probability': success_prob,
                    'params': params,
                    'weight': self.current_weights[name]
                }
                
                logger.info(f"Strategy {name} signal: probability={success_prob:.2f}, weight={self.current_weights[name]:.2f}")
            
            # Apply strategy weights based on performance and market condition
            self._update_weights(condition)
            
            # Combine signals
            combined_signal = self._combine_signals(signals, condition)
            
            # Record allocation
            self._record_allocation(symbol, condition, signals, combined_signal)
            
            return combined_signal
            
        except Exception as e:
            logger.error(f"Error getting optimal strategy: {str(e)}")
            return None
    
    def _update_weights(self, market_condition: str):
        """
        Update strategy weights based on performance and market condition
        
        Args:
            market_condition: String representing market condition
        """
        try:
            # Strategy-condition affinities
            condition_affinities = {
                'breakout': {'volatile': 0.8, 'bullish_trend': 0.6, 'bearish_trend': 0.6, 'ranging': 0.3, 'unknown': 0.5},
                'trend_following': {'volatile': 0.4, 'bullish_trend': 0.9, 'bearish_trend': 0.9, 'ranging': 0.2, 'unknown': 0.5},
                'mean_reversion': {'volatile': 0.5, 'bullish_trend': 0.3, 'bearish_trend': 0.3, 'ranging': 0.9, 'unknown': 0.5},
                'momentum': {'volatile': 0.7, 'bullish_trend': 0.8, 'bearish_trend': 0.7, 'ranging': 0.4, 'unknown': 0.5}
            }
            
            # Calculate performance-based weights
            performance_weights = {}
            total_weight = 0
            
            for name, metrics in self.performance_metrics.items():
                # Skip strategies with no trades
                if metrics['trades'] == 0:
                    performance_weights[name] = 1.0
                    total_weight += 1.0
                    continue
                    
                # Calculate performance score
                win_rate = metrics['win_rate']
                profit_factor = metrics['profit_factor']
                performance_score = (win_rate * 0.4) + (min(profit_factor, 3) / 3 * 0.6)
                
                # Combine with market condition affinity
                affinity = condition_affinities.get(name, {}).get(market_condition, 0.5)
                combined_weight = performance_score * 0.7 + affinity * 0.3
                
                performance_weights[name] = combined_weight
                total_weight += combined_weight
            
            # Normalize weights
            for name in performance_weights:
                self.current_weights[name] = performance_weights[name] / total_weight
                
            logger.info(f"Updated strategy weights for {market_condition} condition: {self.current_weights}")
            
        except Exception as e:
            logger.error(f"Error updating strategy weights: {str(e)}")
    
    def _combine_signals(self, signals: Dict[str, Dict], market_condition: str) -> Dict:
        """
        Combine signals from multiple strategies
        
        Args:
            signals: Dictionary of signals from each strategy
            market_condition: String representing market condition
            
        Returns:
            Dictionary with combined signal parameters
        """
        try:
            # Initialize combined signal
            combined = {
                'probability': 0,
                'entry_price': 0,
                'stop_loss': 0,
                'take_profit': 0,
                'position_size_modifier': 0,
                'strategies_used': [],
                'market_condition': market_condition
            }
            
            total_weight = 0
            
            # Weighted average of signals
            for name, signal in signals.items():
                weight = self.current_weights[name]
                
                # Only include strategies with sufficient probability
                if signal['probability'] > 0.6:
                    combined['probability'] += signal['probability'] * weight
                    combined['entry_price'] += signal['params']['entry_price'] * weight
                    combined['stop_loss'] += signal['params']['stop_loss'] * weight
                    combined['take_profit'] += signal['params']['take_profit'] * weight
                    combined['position_size_modifier'] += signal['params']['position_size_modifier'] * weight
                    combined['strategies_used'].append(name)
                    total_weight += weight
            
            # Normalize if we have valid strategies
            if total_weight > 0:
                combined['probability'] /= total_weight
                combined['entry_price'] /= total_weight
                combined['stop_loss'] /= total_weight
                combined['take_profit'] /= total_weight
                combined['position_size_modifier'] /= total_weight
                
                logger.info(f"Combined signal: probability={combined['probability']:.2f}, strategies={combined['strategies_used']}")
                return combined
            else:
                logger.info("No strategies with sufficient probability")
                return None
                
        except Exception as e:
            logger.error(f"Error combining signals: {str(e)}")
            return None
    
    def _record_allocation(self, symbol: str, condition: str, signals: Dict, combined_signal: Dict):
        """
        Record strategy allocation for analysis
        
        Args:
            symbol: Stock symbol
            condition: Market condition
            signals: Dictionary of signals from each strategy
            combined_signal: Combined signal
        """
        try:
            if combined_signal is None:
                return
                
            # Create allocation record
            allocation = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'market_condition': condition,
                'weights': self.current_weights.copy(),
                'strategies_used': combined_signal['strategies_used'],
                'combined_probability': combined_signal['probability']
            }
            
            # Add to history
            self.allocation_history.append(allocation)
            
            # Keep history manageable
            if len(self.allocation_history) > 1000:
                self.allocation_history = self.allocation_history[-1000:]
                
            # Save to file
            self._save_history()
            
        except Exception as e:
            logger.error(f"Error recording allocation: {str(e)}")
    
    def update_performance(self, strategy_name: str, trade_result: Dict):
        """
        Update performance metrics for a strategy
        
        Args:
            strategy_name: Name of the strategy
            trade_result: Dictionary with trade result
        """
        try:
            if strategy_name not in self.performance_metrics:
                logger.warning(f"Unknown strategy: {strategy_name}")
                return
                
            metrics = self.performance_metrics[strategy_name]
            
            # Update trade counts
            metrics['trades'] += 1
            if trade_result['profit'] > 0:
                metrics['wins'] += 1
            else:
                metrics['losses'] += 1
                
            # Update profit
            metrics['profit'] += trade_result['profit']
            
            # Update derived metrics
            metrics['win_rate'] = metrics['wins'] / metrics['trades'] if metrics['trades'] > 0 else 0.5
            
            if metrics['losses'] > 0:
                total_wins = sum([t['profit'] for t in self.allocation_history if t.get('profit', 0) > 0])
                total_losses = abs(sum([t['profit'] for t in self.allocation_history if t.get('profit', 0) < 0]))
                metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else 2.0
            else:
                metrics['profit_factor'] = 2.0  # Default if no losses
                
            logger.info(f"Updated performance for {strategy_name}: win_rate={metrics['win_rate']:.2f}, profit_factor={metrics['profit_factor']:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating performance: {str(e)}")
            
    def get_performance_metrics(self) -> Dict:
        """
        Get current performance metrics for all strategies
        
        Returns:
            Dictionary with performance metrics
        """
        return self.performance_metrics

    def get_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the dictionary of available strategies and their configurations
        
        Returns:
            Dictionary of strategy names and their configurations
        """
        return self.strategies 