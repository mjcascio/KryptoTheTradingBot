"""
Risk management module for the trading bot.
Handles position risk assessment, portfolio risk, and risk limits.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from ..monitoring.logging.logger import get_logger
from ..utils.config import Config


logger = get_logger(__name__)


class RiskManager:
    """
    Manages trading risk assessment and risk limits.
    """
    
    def __init__(self, config: Config) -> None:
        """
        Initialize the risk manager.
        
        Args:
            config: Configuration object containing risk parameters
        """
        self.config = config
        
        # Initialize risk limits
        self.max_position_size = self.config.get('risk.max_position_size', 0.1)
        self.max_portfolio_risk = self.config.get('risk.max_portfolio_risk', 0.02)
        self.stop_loss_pct = self.config.get('risk.stop_loss_pct', 0.02)
        self.take_profit_pct = self.config.get('risk.take_profit_pct', 0.05)
        self.max_drawdown = self.config.get('risk.max_drawdown', 0.1)
        
        # Initialize tracking variables
        self.peak_equity = 0.0
        self.current_drawdown = 0.0
    
    def should_exit_position(self, position: Dict[str, Any]) -> bool:
        """
        Check if a position should be exited based on risk criteria.
        
        Args:
            position: Position information dictionary
            
        Returns:
            bool: True if position should be exited based on risk
        """
        try:
            # Check stop loss
            if position['unrealized_pl_pct'] <= -self.stop_loss_pct:
                logger.info(f"Stop loss triggered for position {position.get('symbol')}")
                return True
            
            # Check take profit
            if position['unrealized_pl_pct'] >= self.take_profit_pct:
                logger.info(f"Take profit triggered for position {position.get('symbol')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking risk exit conditions: {str(e)}", exc_info=True)
            return False
    
    def can_open_position(
        self,
        symbol: str,
        position_size: float,
        account_value: float,
        current_positions: Dict[str, Any]
    ) -> bool:
        """
        Check if a new position can be opened based on risk limits.
        
        Args:
            symbol: Symbol to trade
            position_size: Proposed position size
            account_value: Current account value
            current_positions: Dictionary of current positions
            
        Returns:
            bool: True if position can be opened
        """
        try:
            # Check position size limit
            position_value = position_size * account_value
            if position_value / account_value > self.max_position_size:
                logger.warning(
                    f"Position size {position_value/account_value:.2%} exceeds limit "
                    f"of {self.max_position_size:.2%}"
                )
                return False
            
            # Check portfolio risk limit
            total_risk = self._calculate_portfolio_risk(current_positions)
            new_position_risk = position_value * self.stop_loss_pct
            if (total_risk + new_position_risk) / account_value > self.max_portfolio_risk:
                logger.warning(
                    f"Portfolio risk {(total_risk + new_position_risk)/account_value:.2%} "
                    f"would exceed limit of {self.max_portfolio_risk:.2%}"
                )
                return False
            
            # Check drawdown limit
            if self.current_drawdown >= self.max_drawdown:
                logger.warning(
                    f"Current drawdown {self.current_drawdown:.2%} exceeds limit "
                    f"of {self.max_drawdown:.2%}"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking position risk limits: {str(e)}", exc_info=True)
            return False
    
    def update_metrics(self, account_value: float) -> None:
        """
        Update risk metrics based on current account value.
        
        Args:
            account_value: Current account value
        """
        try:
            # Update peak equity
            if account_value > self.peak_equity:
                self.peak_equity = account_value
            
            # Update drawdown
            if self.peak_equity > 0:
                self.current_drawdown = (self.peak_equity - account_value) / self.peak_equity
                
        except Exception as e:
            logger.error(f"Error updating risk metrics: {str(e)}", exc_info=True)
    
    def get_position_size(
        self,
        symbol: str,
        account_value: float,
        volatility: Optional[float] = None
    ) -> float:
        """
        Calculate the appropriate position size based on risk parameters.
        
        Args:
            symbol: Symbol to trade
            account_value: Current account value
            volatility: Optional volatility measure for the symbol
            
        Returns:
            float: Recommended position size as a fraction of account value
        """
        try:
            # Base position size on account risk
            base_size = self.max_position_size
            
            # Adjust for volatility if provided
            if volatility:
                # Reduce position size for higher volatility
                volatility_factor = 1.0 - min(volatility, 0.5)  # Cap at 50% reduction
                base_size *= volatility_factor
            
            # Ensure position size doesn't exceed limits
            return min(base_size, self.max_position_size)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}", exc_info=True)
            return 0.0
    
    def _calculate_portfolio_risk(self, positions: Dict[str, Any]) -> float:
        """
        Calculate the current portfolio risk.
        
        Args:
            positions: Dictionary of current positions
            
        Returns:
            float: Total portfolio risk in currency units
        """
        try:
            total_risk = 0.0
            for position in positions.values():
                position_value = float(position.get('market_value', 0))
                # Risk is the potential loss at stop loss
                position_risk = position_value * self.stop_loss_pct
                total_risk += position_risk
            return total_risk
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {str(e)}", exc_info=True)
            return 0.0
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics.
        
        Returns:
            Dict containing risk metrics
        """
        return {
            'max_position_size': self.max_position_size,
            'max_portfolio_risk': self.max_portfolio_risk,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'max_drawdown': self.max_drawdown,
            'current_drawdown': self.current_drawdown,
            'peak_equity': self.peak_equity,
            'last_update': datetime.now(pytz.UTC).isoformat()
        } 