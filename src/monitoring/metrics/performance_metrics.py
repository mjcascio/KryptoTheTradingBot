"""
Performance metrics module for tracking and calculating trading performance metrics.
"""

from typing import Dict, Any
from datetime import datetime
import numpy as np
import pytz

from ...monitoring.logging.logger import get_logger
from ...utils.config import Config


logger = get_logger(__name__)


class PerformanceMetrics:
    """
    Tracks and calculates trading performance metrics.
    """
    
    def __init__(self, config: Config) -> None:
        """
        Initialize the performance metrics tracker.
        
        Args:
            config: Configuration object containing metrics settings
        """
        self.config = config
        
        # Initialize tracking variables
        self.daily_returns = []
        self.trade_returns = []
        self.win_count = 0
        self.loss_count = 0
        self.total_trades = 0
        self.profitable_trades = 0
        self.last_reset = datetime.now(pytz.UTC)
        
        # Load historical data if available
        self._load_historical_data()
    
    def _load_historical_data(self) -> None:
        """Load historical performance data if available."""
        try:
            # TODO: Implement loading historical data from storage
            pass
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}", exc_info=True)
    
    def update_daily_return(self, daily_pl: float, equity: float) -> None:
        """
        Update daily return metrics.
        
        Args:
            daily_pl: Daily profit/loss
            equity: Current equity value
        """
        try:
            if equity > 0:
                daily_return = daily_pl / equity
                self.daily_returns.append(daily_return)
                
        except Exception as e:
            logger.error(f"Error updating daily return: {str(e)}", exc_info=True)
    
    def update_trade_metrics(self, trade: Dict[str, Any]) -> None:
        """
        Update metrics with a new trade.
        
        Args:
            trade: Trade information dictionary
        """
        try:
            # Extract trade metrics
            entry_price = float(trade.get('entry_price', 0))
            exit_price = float(trade.get('exit_price', 0))
            quantity = float(trade.get('quantity', 0))
            
            if entry_price > 0 and quantity > 0:
                # Calculate trade return
                trade_pl = (exit_price - entry_price) * quantity
                trade_return = trade_pl / (entry_price * quantity)
                self.trade_returns.append(trade_return)
                
                # Update win/loss counts
                self.total_trades += 1
                if trade_pl > 0:
                    self.win_count += 1
                    self.profitable_trades += 1
                else:
                    self.loss_count += 1
                
        except Exception as e:
            logger.error(f"Error updating trade metrics: {str(e)}", exc_info=True)
    
    def calculate_sharpe_ratio(
        self,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate the Sharpe ratio.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
            
        Returns:
            float: Sharpe ratio
        """
        try:
            if len(self.daily_returns) < 2:
                return 0.0
            
            # Convert to numpy array for calculations
            returns = np.array(self.daily_returns)
            
            # Calculate annualized metrics
            annual_return = np.mean(returns) * 252
            annual_volatility = np.std(returns) * np.sqrt(252)
            
            # Calculate Sharpe ratio
            if annual_volatility > 0:
                sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
                return float(sharpe_ratio)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}", exc_info=True)
            return 0.0
    
    def calculate_sortino_ratio(
        self,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate the Sortino ratio.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
            
        Returns:
            float: Sortino ratio
        """
        try:
            if len(self.daily_returns) < 2:
                return 0.0
            
            # Convert to numpy array for calculations
            returns = np.array(self.daily_returns)
            
            # Calculate annualized return
            annual_return = np.mean(returns) * 252
            
            # Calculate downside deviation
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 0:
                downside_deviation = np.std(negative_returns) * np.sqrt(252)
                
                # Calculate Sortino ratio
                if downside_deviation > 0:
                    sortino_ratio = (annual_return - risk_free_rate) / downside_deviation
                    return float(sortino_ratio)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {str(e)}", exc_info=True)
            return 0.0
    
    def calculate_max_drawdown(self) -> float:
        """
        Calculate the maximum drawdown.
        
        Returns:
            float: Maximum drawdown as a percentage
        """
        try:
            if len(self.daily_returns) < 2:
                return 0.0
            
            # Calculate cumulative returns
            cumulative_returns = np.cumprod(1 + np.array(self.daily_returns))
            
            # Calculate running maximum
            running_max = np.maximum.accumulate(cumulative_returns)
            
            # Calculate drawdowns
            drawdowns = (cumulative_returns - running_max) / running_max
            
            # Get maximum drawdown
            max_drawdown = float(np.min(drawdowns))
            return abs(max_drawdown)
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {str(e)}", exc_info=True)
            return 0.0
    
    def get_win_rate(self) -> float:
        """
        Calculate the win rate.
        
        Returns:
            float: Win rate as a percentage
        """
        try:
            if self.total_trades > 0:
                return (self.win_count / self.total_trades) * 100
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating win rate: {str(e)}", exc_info=True)
            return 0.0
    
    def get_profit_factor(self) -> float:
        """
        Calculate the profit factor.
        
        Returns:
            float: Profit factor
        """
        try:
            if len(self.trade_returns) < 1:
                return 0.0
            
            # Convert to numpy array
            returns = np.array(self.trade_returns)
            
            # Calculate gross profits and losses
            gross_profits = np.sum(returns[returns > 0])
            gross_losses = abs(np.sum(returns[returns < 0]))
            
            # Calculate profit factor
            if gross_losses > 0:
                return float(gross_profits / gross_losses)
            
            return 0.0 if gross_profits == 0 else float('inf')
            
        except Exception as e:
            logger.error(f"Error calculating profit factor: {str(e)}", exc_info=True)
            return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all performance metrics.
        
        Returns:
            Dict containing performance metrics
        """
        return {
            'total_trades': self.total_trades,
            'win_rate': self.get_win_rate(),
            'profit_factor': self.get_profit_factor(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'max_drawdown': self.calculate_max_drawdown(),
            'profitable_trades': self.profitable_trades,
            'last_reset': self.last_reset.isoformat(),
            'last_update': datetime.now(pytz.UTC).isoformat()
        }
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        try:
            self.daily_returns = []
            self.trade_returns = []
            self.win_count = 0
            self.loss_count = 0
            self.total_trades = 0
            self.profitable_trades = 0
            self.last_reset = datetime.now(pytz.UTC)
            logger.info("Performance metrics reset")
            
        except Exception as e:
            logger.error(f"Error resetting metrics: {str(e)}", exc_info=True) 