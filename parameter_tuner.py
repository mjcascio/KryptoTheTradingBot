import numpy as np
import pandas as pd
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AdaptiveParameterTuner:
    def __init__(self, base_params: Dict[str, Any], optimization_frequency: int = 7, 
                 param_bounds: Optional[Dict[str, Dict[str, float]]] = None, 
                 learning_rate: float = 0.1):
        """
        Initialize the adaptive parameter tuner
        
        Args:
            base_params: Dictionary of base strategy parameters
            optimization_frequency: Days between optimizations
            param_bounds: Dictionary of min/max bounds for each parameter
            learning_rate: How quickly to adjust parameters (0-1)
        """
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        self.base_params = base_params
        self.current_params = base_params.copy()
        self.optimization_frequency = optimization_frequency
        self.last_optimization = None
        self.learning_rate = learning_rate
        self.performance_history = []
        self.params_file = 'data/adaptive_params.json'
        
        # Set default bounds if not provided
        if param_bounds is None:
            self.param_bounds = {}
            for param, value in base_params.items():
                if isinstance(value, (int, float)):
                    self.param_bounds[param] = {
                        'min': value * 0.5,
                        'max': value * 2.0
                    }
        else:
            self.param_bounds = param_bounds
            
        # Load previous parameters if available
        self._load_params()
        
        logger.info(f"Adaptive Parameter Tuner initialized with {len(base_params)} parameters")
    
    def _load_params(self):
        """Load parameters from file if available"""
        if os.path.exists(self.params_file):
            try:
                with open(self.params_file, 'r') as f:
                    data = json.load(f)
                    self.current_params = data.get('current_params', self.base_params)
                    self.last_optimization = datetime.fromisoformat(data.get('last_optimization')) \
                                            if data.get('last_optimization') else None
                    self.performance_history = data.get('performance_history', [])
                logger.info(f"Loaded parameter tuning history with {len(self.performance_history)} entries")
            except Exception as e:
                logger.error(f"Error loading parameter tuning history: {str(e)}")
    
    def _save_params(self):
        """Save parameters to file"""
        try:
            data = {
                'current_params': self.current_params,
                'last_optimization': self.last_optimization.isoformat() if self.last_optimization else None,
                'performance_history': self.performance_history
            }
            
            with open(self.params_file, 'w') as f:
                json.dump(data, f)
            logger.info("Saved parameter tuning data")
        except Exception as e:
            logger.error(f"Error saving parameter tuning data: {str(e)}")
    
    def should_optimize(self) -> bool:
        """
        Check if optimization is due
        
        Returns:
            Boolean indicating if optimization should be performed
        """
        if self.last_optimization is None:
            return True
            
        days_since_optimization = (datetime.now() - self.last_optimization).days
        return days_since_optimization >= self.optimization_frequency
    
    def update_performance(self, performance_data: Dict[str, Any]):
        """
        Update performance history with recent results
        
        Args:
            performance_data: Dictionary with performance metrics
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in performance_data:
                performance_data['timestamp'] = datetime.now().isoformat()
                
            # Add current parameters
            performance_data['parameters'] = self.current_params.copy()
                
            # Add to history
            self.performance_history.append(performance_data)
            
            # Keep only last 30 entries
            if len(self.performance_history) > 30:
                self.performance_history = self.performance_history[-30:]
                
            # Save updated history
            self._save_params()
            
            logger.info(f"Updated performance history: win_rate={performance_data.get('win_rate', 0):.2f}, profit_factor={performance_data.get('profit_factor', 0):.2f}")
        except Exception as e:
            logger.error(f"Error updating performance history: {str(e)}")
    
    def _get_parameter_direction(self, param: str, performance_data: Dict[str, Any], 
                                market_regime: str) -> int:
        """
        Determine direction to adjust a parameter based on performance
        
        Args:
            param: Parameter name
            performance_data: Dictionary with performance metrics
            market_regime: Current market regime
            
        Returns:
            Direction to adjust parameter (-1, 0, or 1)
        """
        try:
            # Get recent performance trend
            if len(self.performance_history) < 2:
                return 0  # No change if insufficient history
                
            recent_history = self.performance_history[-5:]
            
            # Extract relevant metrics
            win_rates = [h.get('win_rate', 0.5) for h in recent_history]
            profit_factors = [h.get('profit_factor', 1.0) for h in recent_history]
            
            # Calculate trend
            win_rate_trend = win_rates[-1] - win_rates[0] if len(win_rates) > 1 else 0
            profit_factor_trend = profit_factors[-1] - profit_factors[0] if len(profit_factors) > 1 else 0
            
            # Parameter-specific logic
            if param == 'price_threshold':
                # If win rate is decreasing, increase threshold to be more selective
                if win_rate_trend < -0.05:
                    return 1  # Increase
                # If win rate is high but profit factor is low, decrease threshold
                elif win_rates[-1] > 0.7 and profit_factors[-1] < 1.5:
                    return -1  # Decrease
                    
            elif param == 'volume_threshold':
                # Adjust based on market regime
                if market_regime == 'volatile':
                    return 1  # Increase in volatile markets
                elif market_regime == 'ranging':
                    return -1  # Decrease in ranging markets
                    
            elif param == 'stop_loss_multiplier':
                # If profit factor is low, adjust stop loss
                if profit_factors[-1] < 1.2:
                    return -1  # Tighten stops
                elif win_rates[-1] < 0.4:
                    return 1  # Loosen stops
                    
            elif param == 'take_profit_multiplier':
                # If win rate is high but profit factor is low, increase targets
                if win_rates[-1] > 0.6 and profit_factors[-1] < 1.5:
                    return 1  # Increase targets
                # If win rate is very low, decrease targets
                elif win_rates[-1] < 0.3:
                    return -1  # Decrease targets
                    
            # Default: no change
            return 0
        except Exception as e:
            logger.error(f"Error determining parameter direction: {str(e)}")
            return 0
    
    def tune_parameters(self, performance_data: Dict[str, Any], market_regime: str) -> Dict[str, Any]:
        """
        Tune parameters based on performance and market regime
        
        Args:
            performance_data: Dictionary with performance metrics
            market_regime: Current market regime
            
        Returns:
            Dictionary with tuned parameters
        """
        try:
            if not self.should_optimize():
                logger.info("Parameter optimization not due yet")
                return self.current_params
                
            # Update performance history
            self.update_performance(performance_data)
            
            # Adjust parameters
            adjusted_params = self.current_params.copy()
            
            for param, value in self.current_params.items():
                # Skip non-numeric parameters
                if not isinstance(value, (int, float)):
                    continue
                    
                # Get adjustment direction
                direction = self._get_parameter_direction(param, performance_data, market_regime)
                
                if direction == 0:
                    continue  # No change
                    
                # Calculate adjustment
                if isinstance(value, int):
                    adjustment = max(1, int(value * self.learning_rate))
                else:
                    adjustment = value * self.learning_rate
                    
                # Apply adjustment
                new_value = value + (adjustment * direction)
                
                # Apply bounds
                if param in self.param_bounds:
                    bounds = self.param_bounds[param]
                    new_value = max(bounds['min'], min(bounds['max'], new_value))
                    
                # Update parameter
                adjusted_params[param] = new_value
                
                logger.info(f"Adjusted parameter {param}: {value} -> {new_value}")
                
            # Update current parameters
            self.current_params = adjusted_params
            self.last_optimization = datetime.now()
            
            # Save parameters
            self._save_params()
            
            logger.info(f"Parameters tuned for {market_regime} market regime")
            
            return self.current_params
        except Exception as e:
            logger.error(f"Error tuning parameters: {str(e)}")
            return self.current_params
    
    def reset_to_base(self) -> Dict[str, Any]:
        """
        Reset parameters to base values
        
        Returns:
            Dictionary with base parameters
        """
        try:
            self.current_params = self.base_params.copy()
            self._save_params()
            logger.info("Parameters reset to base values")
            return self.current_params
        except Exception as e:
            logger.error(f"Error resetting parameters: {str(e)}")
            return self.current_params
    
    def get_parameter_history(self) -> List[Dict[str, Any]]:
        """
        Get parameter adjustment history
        
        Returns:
            List of parameter history entries
        """
        try:
            # Extract parameter history from performance history
            param_history = []
            
            for entry in self.performance_history:
                if 'parameters' in entry:
                    param_history.append({
                        'timestamp': entry.get('timestamp', ''),
                        'parameters': entry['parameters'],
                        'win_rate': entry.get('win_rate', 0),
                        'profit_factor': entry.get('profit_factor', 0)
                    })
                    
            return param_history
        except Exception as e:
            logger.error(f"Error getting parameter history: {str(e)}")
            return []
    
    def analyze_parameter_effectiveness(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze effectiveness of parameter adjustments
        
        Returns:
            Dictionary with parameter effectiveness analysis
        """
        try:
            if len(self.performance_history) < 5:
                logger.warning("Insufficient history for parameter effectiveness analysis")
                return {}
                
            # Extract parameter history
            param_history = self.get_parameter_history()
            
            # Analyze each parameter
            param_effectiveness = {}
            
            for param in self.base_params:
                if not isinstance(self.base_params[param], (int, float)):
                    continue
                    
                # Extract parameter values and corresponding performance
                values = [entry['parameters'].get(param, 0) for entry in param_history]
                win_rates = [entry.get('win_rate', 0) for entry in param_history]
                profit_factors = [entry.get('profit_factor', 0) for entry in param_history]
                
                # Calculate correlations
                win_rate_corr = np.corrcoef(values, win_rates)[0, 1] if len(values) > 1 else 0
                profit_factor_corr = np.corrcoef(values, profit_factors)[0, 1] if len(values) > 1 else 0
                
                param_effectiveness[param] = {
                    'win_rate_correlation': win_rate_corr,
                    'profit_factor_correlation': profit_factor_corr,
                    'overall_effectiveness': (abs(win_rate_corr) + abs(profit_factor_corr)) / 2,
                    'current_value': self.current_params.get(param, 0),
                    'base_value': self.base_params.get(param, 0),
                    'adjustment': (self.current_params.get(param, 0) - self.base_params.get(param, 0)) / self.base_params.get(param, 1) * 100
                }
                
            logger.info(f"Analyzed effectiveness of {len(param_effectiveness)} parameters")
            
            return param_effectiveness
        except Exception as e:
            logger.error(f"Error analyzing parameter effectiveness: {str(e)}")
            return {} 