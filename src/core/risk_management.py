#!/usr/bin/env python3
"""
Risk Management Module

This module handles position sizing and risk controls.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RiskManager:
    """Risk management system"""
    
    def __init__(
        self,
        max_position_size: float = 10000,
        max_drawdown: float = 0.02,
        risk_per_trade: float = 0.01,
        max_open_positions: int = 5,
        max_daily_loss: float = 0.02,
        volatility_threshold: float = 0.2
    ):
        """Initialize risk management system
        
        Args:
            max_position_size (float): Maximum position size in dollars
            max_drawdown (float): Maximum allowed drawdown percentage
            risk_per_trade (float): Maximum risk per trade percentage
            max_open_positions (int): Maximum number of open positions
            max_daily_loss (float): Maximum daily loss percentage
            volatility_threshold (float): Volatility threshold for position sizing
        """
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.risk_per_trade = risk_per_trade
        self.max_open_positions = max_open_positions
        self.max_daily_loss = max_daily_loss
        self.volatility_threshold = volatility_threshold
        
        # Account status
        self.current_equity = 0.0
        self.peak_equity = 0.0
        self.daily_pnl = 0.0
        self.open_positions = 0
        
        self.logger.info("Risk manager initialized")

    def update_account_status(self, account_info: Dict) -> None:
        """Update account status
        
        Args:
            account_info (Dict): Account information
        """
        self.current_equity = float(account_info['equity'])
        
        # Initialize peak equity if not set
        if self.peak_equity == 0:
            self.peak_equity = self.current_equity
        
        # Update daily P&L
        self.daily_pnl = self.current_equity - self.peak_equity
        
        self.logger.debug(f"Account status updated: Equity={self.current_equity:.2f}, Peak={self.peak_equity:.2f}")

    def can_open_position(self, position_size: float, account_info: Dict) -> bool:
        """Check if a new position can be opened
        
        Args:
            position_size (float): Proposed position size
            account_info (Dict): Account information
            
        Returns:
            bool: True if position can be opened
        """
        # Update account status
        self.update_account_status(account_info)
        
        # Check maximum position size
        if position_size > self.max_position_size:
            self.logger.warning(f"Position size {position_size:.2f} exceeds maximum allowed {self.max_position_size:.2f}")
            return False
        
        # Check maximum number of open positions
        if self.open_positions >= self.max_open_positions:
            self.logger.warning(f"Maximum number of open positions ({self.max_open_positions}) reached")
            return False
        
        # Check maximum drawdown
        current_drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
        if current_drawdown > self.max_drawdown:
            self.logger.warning(f"Maximum drawdown ({self.max_drawdown:.2%}) exceeded")
            return False
        
        # Check daily loss limit
        if self.daily_pnl < -self.current_equity * self.max_daily_loss:
            self.logger.warning(f"Maximum daily loss ({self.max_daily_loss:.2%}) exceeded")
            return False
        
        return True

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        account_info: Dict,
        volatility: float = 0.0
    ) -> Optional[float]:
        """Calculate position size based on risk parameters
        
        Args:
            entry_price (float): Entry price
            stop_loss (float): Stop loss price
            account_info (Dict): Account information
            volatility (float): Current volatility
            
        Returns:
            Position size if valid, None otherwise
        """
        # Check volatility threshold
        if volatility > self.volatility_threshold:
            self.logger.warning(f"Volatility {volatility:.2%} exceeds threshold {self.volatility_threshold:.2%}")
            return None
        
        # Calculate risk amount
        risk_amount = self.current_equity * self.risk_per_trade
        
        # Calculate position size based on risk
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            self.logger.warning("Invalid stop loss: same as entry price")
            return None
        
        position_size = risk_amount / risk_per_share
        
        # Check if position size is within limits
        if position_size > self.max_position_size:
            position_size = self.max_position_size
        
        return position_size

    def update_position_count(self, count: int) -> None:
        """Update the number of open positions
        
        Args:
            count (int): Number of open positions
        """
        self.open_positions = count
        self.logger.debug(f"Open positions updated: {count}")

    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics
        
        Returns:
            Dictionary with risk metrics
        """
        return {
            'current_equity': self.current_equity,
            'peak_equity': self.peak_equity,
            'drawdown': (self.peak_equity - self.current_equity) / self.peak_equity,
            'daily_pnl': self.daily_pnl,
            'open_positions': self.open_positions,
            'max_position_size': self.max_position_size,
            'max_drawdown': self.max_drawdown,
            'risk_per_trade': self.risk_per_trade,
            'max_open_positions': self.max_open_positions,
            'max_daily_loss': self.max_daily_loss,
            'volatility_threshold': self.volatility_threshold
        } 