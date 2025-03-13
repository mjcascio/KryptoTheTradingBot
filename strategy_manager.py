#!/usr/bin/env python3
"""
Strategy Manager for KryptoBot

This module manages trading strategies for both stocks and options,
ensuring consistent risk parameters across all trades.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/strategy_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
STRATEGIES_FILE = "data/strategies.json"
STRATEGY_README = "TRADING_STRATEGIES_README.md"
EST_TIMEZONE = pytz.timezone('US/Eastern')

class StrategyManager:
    """
    Manages trading strategies for both stocks and options with consistent risk parameters.
    """
    
    def __init__(self):
        """Initialize the strategy manager."""
        self.strategies = self._load_strategies()
        self.current_strategy = self._get_current_strategy()
        self.risk_parameters = self._load_risk_parameters()
        
        # Create directories if they don't exist
        os.makedirs('data', exist_ok=True)
        
        logger.info("Strategy Manager initialized")
    
    def _load_strategies(self) -> Dict[str, Any]:
        """
        Load trading strategies from the strategies file.
        
        Returns:
            Dict containing trading strategies
        """
        try:
            if os.path.exists(STRATEGIES_FILE):
                with open(STRATEGIES_FILE, 'r') as f:
                    strategies = json.load(f)
                logger.info(f"Loaded {len(strategies)} strategies from {STRATEGIES_FILE}")
                return strategies
            else:
                # Create default strategies if file doesn't exist
                default_strategies = self._create_default_strategies()
                self._save_strategies(default_strategies)
                return default_strategies
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")
            return self._create_default_strategies()
    
    def _create_default_strategies(self) -> Dict[str, Any]:
        """
        Create default trading strategies.
        
        Returns:
            Dict containing default trading strategies
        """
        default_strategies = {
            "conservative": {
                "name": "Conservative",
                "description": "Low-risk strategy focusing on blue-chip stocks and conservative options strategies",
                "risk_level": "low",
                "max_position_size": 0.05,  # 5% of portfolio per position
                "stop_loss_percentage": 0.02,  # 2% stop loss
                "take_profit_percentage": 0.05,  # 5% take profit
                "max_daily_loss": 0.01,  # 1% max daily loss
                "max_open_positions": 5,
                "stock_parameters": {
                    "min_volume": 1000000,
                    "min_market_cap": 10000000000,  # $10B
                    "preferred_sectors": ["Technology", "Healthcare", "Consumer Staples"]
                },
                "option_parameters": {
                    "max_days_to_expiration": 45,
                    "min_days_to_expiration": 14,
                    "preferred_strategies": ["covered_call", "cash_secured_put"],
                    "min_open_interest": 500,
                    "max_implied_volatility": 0.4,
                    "delta_range": [0.3, 0.7]
                }
            },
            "moderate": {
                "name": "Moderate",
                "description": "Balanced risk-reward strategy for both stocks and options",
                "risk_level": "medium",
                "max_position_size": 0.1,  # 10% of portfolio per position
                "stop_loss_percentage": 0.025,  # 2.5% stop loss
                "take_profit_percentage": 0.075,  # 7.5% take profit
                "max_daily_loss": 0.02,  # 2% max daily loss
                "max_open_positions": 8,
                "stock_parameters": {
                    "min_volume": 500000,
                    "min_market_cap": 2000000000,  # $2B
                    "preferred_sectors": ["Technology", "Consumer Discretionary", "Financials", "Industrials"]
                },
                "option_parameters": {
                    "max_days_to_expiration": 60,
                    "min_days_to_expiration": 7,
                    "preferred_strategies": ["vertical_spread", "iron_condor", "calendar_spread"],
                    "min_open_interest": 250,
                    "max_implied_volatility": 0.6,
                    "delta_range": [0.25, 0.75]
                }
            },
            "aggressive": {
                "name": "Aggressive",
                "description": "High-risk, high-reward strategy focusing on growth stocks and aggressive options strategies",
                "risk_level": "high",
                "max_position_size": 0.15,  # 15% of portfolio per position
                "stop_loss_percentage": 0.035,  # 3.5% stop loss
                "take_profit_percentage": 0.1,  # 10% take profit
                "max_daily_loss": 0.03,  # 3% max daily loss
                "max_open_positions": 10,
                "stock_parameters": {
                    "min_volume": 100000,
                    "min_market_cap": 500000000,  # $500M
                    "preferred_sectors": ["Technology", "Communications", "Consumer Discretionary"]
                },
                "option_parameters": {
                    "max_days_to_expiration": 90,
                    "min_days_to_expiration": 0,  # Including 0DTE
                    "preferred_strategies": ["long_call", "long_put", "straddle", "strangle"],
                    "min_open_interest": 100,
                    "max_implied_volatility": 1.0,
                    "delta_range": [0.2, 0.8]
                }
            },
            "trend_following": {
                "name": "Trend Following",
                "description": "Strategy that follows market trends using technical indicators",
                "risk_level": "medium",
                "max_position_size": 0.08,  # 8% of portfolio per position
                "stop_loss_percentage": 0.03,  # 3% stop loss
                "take_profit_percentage": 0.09,  # 9% take profit
                "max_daily_loss": 0.02,  # 2% max daily loss
                "max_open_positions": 7,
                "stock_parameters": {
                    "min_volume": 300000,
                    "min_market_cap": 1000000000,  # $1B
                    "technical_indicators": ["moving_averages", "macd", "rsi"],
                    "trend_confirmation": True
                },
                "option_parameters": {
                    "max_days_to_expiration": 60,
                    "min_days_to_expiration": 14,
                    "preferred_strategies": ["long_call", "long_put", "debit_spread"],
                    "min_open_interest": 200,
                    "max_implied_volatility": 0.7,
                    "delta_range": [0.4, 0.7]
                }
            },
            "breakout": {
                "name": "Breakout",
                "description": "Strategy that identifies and trades breakouts from key levels",
                "risk_level": "high",
                "max_position_size": 0.1,  # 10% of portfolio per position
                "stop_loss_percentage": 0.03,  # 3% stop loss
                "take_profit_percentage": 0.12,  # 12% take profit
                "max_daily_loss": 0.025,  # 2.5% max daily loss
                "max_open_positions": 6,
                "stock_parameters": {
                    "min_volume": 500000,
                    "min_market_cap": 1000000000,  # $1B
                    "volume_surge_threshold": 2.0,  # 2x average volume
                    "breakout_confirmation": True
                },
                "option_parameters": {
                    "max_days_to_expiration": 45,
                    "min_days_to_expiration": 7,
                    "preferred_strategies": ["long_call", "long_put"],
                    "min_open_interest": 300,
                    "max_implied_volatility": 0.8,
                    "delta_range": [0.4, 0.6]
                }
            }
        }
        
        logger.info("Created default strategies")
        return default_strategies
    
    def _save_strategies(self, strategies: Dict[str, Any]) -> None:
        """
        Save trading strategies to the strategies file.
        
        Args:
            strategies: Dict containing trading strategies
        """
        try:
            with open(STRATEGIES_FILE, 'w') as f:
                json.dump(strategies, f, indent=4)
            logger.info(f"Saved {len(strategies)} strategies to {STRATEGIES_FILE}")
            
            # Also update the README file
            self._update_strategy_readme(strategies)
        except Exception as e:
            logger.error(f"Error saving strategies: {e}")
    
    def _update_strategy_readme(self, strategies: Dict[str, Any]) -> None:
        """
        Update the strategy README file.
        
        Args:
            strategies: Dict containing trading strategies
        """
        try:
            readme_content = "# KryptoBot Trading Strategies\n\n"
            readme_content += "This document outlines the trading strategies available in KryptoBot.\n\n"
            
            for strategy_id, strategy in strategies.items():
                readme_content += f"## {strategy['name']} Strategy\n\n"
                readme_content += f"**ID:** `{strategy_id}`\n\n"
                readme_content += f"**Description:** {strategy['description']}\n\n"
                readme_content += f"**Risk Level:** {strategy['risk_level'].capitalize()}\n\n"
                
                readme_content += "### Risk Parameters\n\n"
                readme_content += f"- **Max Position Size:** {strategy['max_position_size'] * 100}% of portfolio\n"
                readme_content += f"- **Stop Loss:** {strategy['stop_loss_percentage'] * 100}%\n"
                readme_content += f"- **Take Profit:** {strategy['take_profit_percentage'] * 100}%\n"
                readme_content += f"- **Max Daily Loss:** {strategy['max_daily_loss'] * 100}%\n"
                readme_content += f"- **Max Open Positions:** {strategy['max_open_positions']}\n\n"
                
                readme_content += "### Stock Trading Parameters\n\n"
                stock_params = strategy['stock_parameters']
                readme_content += f"- **Minimum Volume:** {stock_params.get('min_volume', 'N/A')}\n"
                readme_content += f"- **Minimum Market Cap:** ${stock_params.get('min_market_cap', 'N/A'):,}\n"
                
                if 'preferred_sectors' in stock_params:
                    readme_content += f"- **Preferred Sectors:** {', '.join(stock_params['preferred_sectors'])}\n"
                
                if 'technical_indicators' in stock_params:
                    readme_content += f"- **Technical Indicators:** {', '.join(stock_params['technical_indicators'])}\n"
                
                if 'volume_surge_threshold' in stock_params:
                    readme_content += f"- **Volume Surge Threshold:** {stock_params['volume_surge_threshold']}x average\n"
                
                readme_content += "\n### Options Trading Parameters\n\n"
                option_params = strategy['option_parameters']
                readme_content += f"- **Days to Expiration:** {option_params.get('min_days_to_expiration', 'N/A')} to {option_params.get('max_days_to_expiration', 'N/A')} days\n"
                readme_content += f"- **Preferred Strategies:** {', '.join(option_params['preferred_strategies'])}\n"
                readme_content += f"- **Minimum Open Interest:** {option_params.get('min_open_interest', 'N/A')}\n"
                readme_content += f"- **Maximum Implied Volatility:** {option_params.get('max_implied_volatility', 'N/A') * 100}%\n"
                
                if 'delta_range' in option_params:
                    readme_content += f"- **Delta Range:** {option_params['delta_range'][0]} to {option_params['delta_range'][1]}\n"
                
                readme_content += "\n---\n\n"
            
            readme_content += "## How to Use These Strategies\n\n"
            readme_content += "To change the active strategy, use one of the following methods:\n\n"
            readme_content += "1. Send a Telegram command: `/strategy [strategy_id]`\n"
            readme_content += "2. Respond to the morning report with the strategy ID\n"
            readme_content += "3. Update the `current_strategy.json` file manually\n\n"
            
            readme_content += "## Custom Strategies\n\n"
            readme_content += "To add a custom strategy, edit the `data/strategies.json` file following the same format as the existing strategies.\n"
            
            with open(STRATEGY_README, 'w') as f:
                f.write(readme_content)
            
            logger.info(f"Updated strategy README at {STRATEGY_README}")
        except Exception as e:
            logger.error(f"Error updating strategy README: {e}")
    
    def _get_current_strategy(self) -> str:
        """
        Get the current active strategy ID.
        
        Returns:
            String ID of the current strategy
        """
        try:
            current_strategy_file = "data/current_strategy.json"
            if os.path.exists(current_strategy_file):
                with open(current_strategy_file, 'r') as f:
                    data = json.load(f)
                    return data.get('strategy_id', 'moderate')
            else:
                # Default to moderate if no current strategy is set
                return 'moderate'
        except Exception as e:
            logger.error(f"Error getting current strategy: {e}")
            return 'moderate'  # Default to moderate on error
    
    def _save_current_strategy(self, strategy_id: str) -> None:
        """
        Save the current active strategy ID.
        
        Args:
            strategy_id: String ID of the strategy to set as current
        """
        try:
            current_strategy_file = "data/current_strategy.json"
            with open(current_strategy_file, 'w') as f:
                json.dump({'strategy_id': strategy_id, 'updated_at': datetime.now().isoformat()}, f, indent=4)
            logger.info(f"Set current strategy to '{strategy_id}'")
        except Exception as e:
            logger.error(f"Error saving current strategy: {e}")
    
    def _load_risk_parameters(self) -> Dict[str, Any]:
        """
        Load risk parameters from the current strategy.
        
        Returns:
            Dict containing risk parameters
        """
        try:
            strategy = self.strategies.get(self.current_strategy)
            if not strategy:
                logger.warning(f"Strategy '{self.current_strategy}' not found, using moderate")
                strategy = self.strategies.get('moderate', {})
            
            # Extract risk parameters
            risk_params = {
                'max_position_size': strategy.get('max_position_size', 0.1),
                'stop_loss_percentage': strategy.get('stop_loss_percentage', 0.025),
                'take_profit_percentage': strategy.get('take_profit_percentage', 0.075),
                'max_daily_loss': strategy.get('max_daily_loss', 0.02),
                'max_open_positions': strategy.get('max_open_positions', 8),
                'stock_parameters': strategy.get('stock_parameters', {}),
                'option_parameters': strategy.get('option_parameters', {})
            }
            
            logger.info(f"Loaded risk parameters for strategy '{self.current_strategy}'")
            return risk_params
        except Exception as e:
            logger.error(f"Error loading risk parameters: {e}")
            # Return default risk parameters
            return {
                'max_position_size': 0.1,
                'stop_loss_percentage': 0.025,
                'take_profit_percentage': 0.075,
                'max_daily_loss': 0.02,
                'max_open_positions': 8,
                'stock_parameters': {},
                'option_parameters': {}
            }
    
    def get_strategy_details(self, strategy_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get details for a specific strategy or the current strategy.
        
        Args:
            strategy_id: Optional ID of the strategy to get details for
                        (defaults to current strategy)
        
        Returns:
            Dict containing strategy details
        """
        strategy_id = strategy_id or self.current_strategy
        return self.strategies.get(strategy_id, {})
    
    def get_current_strategy_details(self) -> Dict[str, Any]:
        """
        Get details for the current strategy.
        
        Returns:
            Dict containing current strategy details
        """
        return self.get_strategy_details(self.current_strategy)
    
    def get_risk_parameters(self) -> Dict[str, Any]:
        """
        Get the current risk parameters.
        
        Returns:
            Dict containing risk parameters
        """
        return self.risk_parameters
    
    def set_strategy(self, strategy_id: str) -> bool:
        """
        Set the current strategy.
        
        Args:
            strategy_id: ID of the strategy to set as current
        
        Returns:
            Boolean indicating success
        """
        if strategy_id in self.strategies:
            self.current_strategy = strategy_id
            self.risk_parameters = self._load_risk_parameters()
            self._save_current_strategy(strategy_id)
            logger.info(f"Strategy changed to '{strategy_id}'")
            return True
        else:
            logger.warning(f"Strategy '{strategy_id}' not found")
            return False
    
    def add_strategy(self, strategy_id: str, strategy_details: Dict[str, Any]) -> bool:
        """
        Add a new strategy or update an existing one.
        
        Args:
            strategy_id: ID of the strategy to add/update
            strategy_details: Dict containing strategy details
        
        Returns:
            Boolean indicating success
        """
        try:
            # Validate strategy details
            required_fields = ['name', 'description', 'risk_level', 'max_position_size', 
                              'stop_loss_percentage', 'take_profit_percentage']
            
            for field in required_fields:
                if field not in strategy_details:
                    logger.error(f"Missing required field '{field}' in strategy details")
                    return False
            
            # Add or update strategy
            self.strategies[strategy_id] = strategy_details
            self._save_strategies(self.strategies)
            logger.info(f"Added/updated strategy '{strategy_id}'")
            return True
        except Exception as e:
            logger.error(f"Error adding strategy: {e}")
            return False
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """
        Remove a strategy.
        
        Args:
            strategy_id: ID of the strategy to remove
        
        Returns:
            Boolean indicating success
        """
        if strategy_id in self.strategies:
            # Don't allow removing the current strategy
            if strategy_id == self.current_strategy:
                logger.warning(f"Cannot remove current strategy '{strategy_id}'")
                return False
            
            # Don't allow removing all strategies
            if len(self.strategies) <= 1:
                logger.warning("Cannot remove the only strategy")
                return False
            
            del self.strategies[strategy_id]
            self._save_strategies(self.strategies)
            logger.info(f"Removed strategy '{strategy_id}'")
            return True
        else:
            logger.warning(f"Strategy '{strategy_id}' not found")
            return False
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available strategies.
        
        Returns:
            List of dicts containing strategy details
        """
        return [{'id': k, **v} for k, v in self.strategies.items()]
    
    def get_strategy_recommendation(self, market_data: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Get a strategy recommendation based on market conditions.
        
        Args:
            market_data: Optional dict containing market data for analysis
        
        Returns:
            Tuple of (strategy_id, explanation)
        """
        try:
            # If no market data is provided, use a simple recommendation
            if not market_data:
                return self.current_strategy, "Continuing with current strategy due to insufficient market data."
            
            # Analyze market conditions (simplified example)
            market_volatility = market_data.get('volatility', 'medium')
            market_trend = market_data.get('trend', 'neutral')
            
            # Simple recommendation logic
            if market_volatility == 'high' and market_trend == 'bullish':
                recommended_strategy = 'aggressive'
                explanation = "High volatility with bullish trend suggests an aggressive strategy to capitalize on potential gains."
            elif market_volatility == 'high' and market_trend == 'bearish':
                recommended_strategy = 'conservative'
                explanation = "High volatility with bearish trend suggests a conservative strategy to minimize risk."
            elif market_trend == 'bullish':
                recommended_strategy = 'moderate'
                explanation = "Bullish trend suggests a moderate strategy to balance risk and reward."
            elif market_trend == 'bearish':
                recommended_strategy = 'conservative'
                explanation = "Bearish trend suggests a conservative strategy to protect capital."
            elif market_volatility == 'low':
                recommended_strategy = 'trend_following'
                explanation = "Low volatility suggests a trend following strategy to capitalize on established trends."
            else:
                recommended_strategy = self.current_strategy
                explanation = "Current market conditions do not suggest a strategy change."
            
            # Check if the recommended strategy exists
            if recommended_strategy not in self.strategies:
                recommended_strategy = self.current_strategy
                explanation += " Defaulting to current strategy."
            
            # Check if the recommendation is different from current
            if recommended_strategy == self.current_strategy:
                explanation = "Current strategy remains optimal for market conditions."
            
            return recommended_strategy, explanation
        
        except Exception as e:
            logger.error(f"Error getting strategy recommendation: {e}")
            return self.current_strategy, "Error analyzing market conditions. Continuing with current strategy."
    
    def should_change_strategy(self, market_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if a strategy change is necessary.
        
        Args:
            market_data: Optional dict containing market data for analysis
        
        Returns:
            Boolean indicating if strategy change is recommended
        """
        recommended_strategy, _ = self.get_strategy_recommendation(market_data)
        return recommended_strategy != self.current_strategy
    
    def verify_risk_parameters(self, portfolio_value: float, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify that current positions adhere to risk parameters.
        
        Args:
            portfolio_value: Current portfolio value
            positions: List of current positions
        
        Returns:
            Dict containing verification results
        """
        try:
            risk_params = self.risk_parameters
            verification = {
                'adheres_to_max_position_size': True,
                'adheres_to_max_open_positions': True,
                'violations': [],
                'warnings': []
            }
            
            # Check number of open positions
            max_positions = risk_params['max_open_positions']
            if len(positions) > max_positions:
                verification['adheres_to_max_open_positions'] = False
                verification['violations'].append(f"Too many open positions: {len(positions)}/{max_positions}")
            
            # Check position sizes
            max_position_size = risk_params['max_position_size'] * portfolio_value
            for position in positions:
                position_value = float(position.get('market_value', 0))
                if position_value > max_position_size:
                    verification['adheres_to_max_position_size'] = False
                    symbol = position.get('symbol', 'Unknown')
                    verification['violations'].append(
                        f"Position {symbol} exceeds max size: ${position_value:.2f}/${max_position_size:.2f}"
                    )
            
            # Add overall status
            verification['status'] = 'compliant' if (
                verification['adheres_to_max_position_size'] and 
                verification['adheres_to_max_open_positions']
            ) else 'non_compliant'
            
            return verification
        
        except Exception as e:
            logger.error(f"Error verifying risk parameters: {e}")
            return {
                'status': 'error',
                'message': f"Error verifying risk parameters: {e}",
                'adheres_to_max_position_size': False,
                'adheres_to_max_open_positions': False,
                'violations': ["Error during verification"],
                'warnings': []
            }
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open (US stock market hours).
        
        Returns:
            Boolean indicating if market is open
        """
        now = datetime.now(EST_TIMEZONE)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            return False
        
        # Check if it's between 9:30 AM and 4:00 PM EST
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def get_market_hours(self) -> Dict[str, datetime]:
        """
        Get market open and close times for today.
        
        Returns:
            Dict containing market open and close times
        """
        now = datetime.now(EST_TIMEZONE)
        
        # Market hours (9:30 AM to 4:00 PM EST)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return {
            'market_open': market_open,
            'market_close': market_close
        }
    
    def time_to_market_open(self) -> timedelta:
        """
        Get time remaining until market open.
        
        Returns:
            Timedelta until market open (negative if market is already open)
        """
        now = datetime.now(EST_TIMEZONE)
        market_hours = self.get_market_hours()
        
        return market_hours['market_open'] - now
    
    def time_to_market_close(self) -> timedelta:
        """
        Get time remaining until market close.
        
        Returns:
            Timedelta until market close (negative if market is already closed)
        """
        now = datetime.now(EST_TIMEZONE)
        market_hours = self.get_market_hours()
        
        return market_hours['market_close'] - now

# Example usage
if __name__ == "__main__":
    strategy_manager = StrategyManager()
    
    # Print available strategies
    print("Available Strategies:")
    for strategy in strategy_manager.list_strategies():
        print(f"- {strategy['name']} ({strategy['id']}): {strategy['description']}")
    
    # Print current strategy
    current = strategy_manager.get_current_strategy_details()
    print(f"\nCurrent Strategy: {current.get('name', 'Unknown')}")
    
    # Print risk parameters
    risk_params = strategy_manager.get_risk_parameters()
    print(f"\nRisk Parameters:")
    print(f"- Max Position Size: {risk_params['max_position_size'] * 100}%")
    print(f"- Stop Loss: {risk_params['stop_loss_percentage'] * 100}%")
    print(f"- Take Profit: {risk_params['take_profit_percentage'] * 100}%")
    
    # Check if market is open
    is_open = strategy_manager.is_market_open()
    print(f"\nMarket is {'open' if is_open else 'closed'}")
    
    # Get market hours
    market_hours = strategy_manager.get_market_hours()
    print(f"Market opens at: {market_hours['market_open'].strftime('%H:%M:%S')}")
    print(f"Market closes at: {market_hours['market_close'].strftime('%H:%M:%S')}") 