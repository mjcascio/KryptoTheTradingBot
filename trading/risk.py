"""Risk management module for the KryptoBot Trading System."""

from __future__ import annotations

import logging
import numpy as np
from typing import Dict, Any, List, Tuple, TypedDict, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from config.settings import (
    MAX_DAILY_LOSS_PCT,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT
)
from utils.logging import setup_logging

# Set up module logger
logger = setup_logging(__name__)

class TradeResult(TypedDict, total=False):
    """Type definition for trade result data."""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    profit: float
    commission: float
    equity: float
    timestamp: str

class RiskMetrics(TypedDict):
    """Type definition for risk metrics."""
    portfolio_heat: float
    drawdown: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    win_loss_ratio: float
    avg_win: float
    avg_loss: float

class RiskManager:
    """Risk management class for trading operations."""
    
    def __init__(self, 
                 max_position_size_pct: float = 0.05,
                 max_portfolio_risk_pct: float = 0.02,
                 max_daily_loss_pct: float = 0.03,
                 max_drawdown_pct: float = 0.15):
        """Initialize the risk manager.
        
        Args:
            max_position_size_pct: Maximum position size as percentage of portfolio
            max_portfolio_risk_pct: Maximum portfolio risk percentage
            max_daily_loss_pct: Maximum daily loss percentage
            max_drawdown_pct: Maximum drawdown percentage
        """
        self.max_position_size_pct = max_position_size_pct
        self.max_portfolio_risk_pct = max_portfolio_risk_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        
        # Risk metrics
        self.current_drawdown_pct = 0.0
        self.daily_loss_pct = 0.0
        self.portfolio_risk_pct = 0.0
        
        # Risk state
        self.risk_level = "normal"  # normal, elevated, high, extreme
        self.trading_allowed = True
        self.last_update = datetime.now()
        
        logger.info("Risk manager initialized")
    
    def update_metrics(self, portfolio_metrics: Dict[str, Any]) -> None:
        """Update risk metrics based on portfolio data.
        
        Args:
            portfolio_metrics: Dictionary containing portfolio metrics
        """
        # Extract relevant metrics
        if 'drawdown_pct' in portfolio_metrics:
            self.current_drawdown_pct = portfolio_metrics['drawdown_pct']
        
        if 'daily_pnl_pct' in portfolio_metrics and portfolio_metrics['daily_pnl_pct'] < 0:
            self.daily_loss_pct = abs(portfolio_metrics['daily_pnl_pct'])
        
        if 'portfolio_risk_pct' in portfolio_metrics:
            self.portfolio_risk_pct = portfolio_metrics['portfolio_risk_pct']
        
        # Update risk level
        self._update_risk_level()
        
        # Update trading allowed status
        self._update_trading_allowed()
        
        self.last_update = datetime.now()
        logger.debug(f"Risk metrics updated: level={self.risk_level}, trading_allowed={self.trading_allowed}")
    
    def can_trade(self, signal: Dict[str, Any]) -> bool:
        """Check if a trade meets risk requirements.
        
        Args:
            signal: Trading signal with symbol, side, etc.
            
        Returns:
            True if the trade meets risk requirements, False otherwise
        """
        # Check if trading is allowed
        if not self.trading_allowed:
            logger.warning(f"Trading not allowed due to risk level: {self.risk_level}")
            return False
        
        # Check position size
        if 'position_size_pct' in signal and signal['position_size_pct'] > self.max_position_size_pct:
            logger.warning(f"Position size too large: {signal['position_size_pct']:.2%} > {self.max_position_size_pct:.2%}")
            return False
        
        # Check if we're already at maximum risk
        if self.portfolio_risk_pct >= self.max_portfolio_risk_pct:
            logger.warning(f"Portfolio risk too high: {self.portfolio_risk_pct:.2%} >= {self.max_portfolio_risk_pct:.2%}")
            return False
        
        return True
    
    def get_position_size(self, equity: float, price: float, risk_per_trade: Optional[float] = None) -> float:
        """Calculate position size based on risk parameters.
        
        Args:
            equity: Current portfolio equity
            price: Current price of the asset
            risk_per_trade: Risk per trade (optional, uses max_position_size_pct if not provided)
            
        Returns:
            Position size in units/shares
        """
        # Use provided risk per trade or default
        risk_pct = risk_per_trade if risk_per_trade is not None else self.max_position_size_pct
        
        # Adjust risk based on current risk level
        if self.risk_level == "elevated":
            risk_pct *= 0.75
        elif self.risk_level == "high":
            risk_pct *= 0.5
        elif self.risk_level == "extreme":
            risk_pct *= 0.25
        
        # Calculate position size
        position_value = equity * risk_pct
        position_size = position_value / price
        
        return position_size
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics.
        
        Returns:
            Dictionary containing risk metrics
        """
        return {
            'risk_level': self.risk_level,
            'trading_allowed': self.trading_allowed,
            'current_drawdown_pct': self.current_drawdown_pct,
            'daily_loss_pct': self.daily_loss_pct,
            'portfolio_risk_pct': self.portfolio_risk_pct,
            'max_position_size_pct': self.max_position_size_pct,
            'max_portfolio_risk_pct': self.max_portfolio_risk_pct,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'max_drawdown_pct': self.max_drawdown_pct,
            'last_update': self.last_update.isoformat()
        }
    
    def _update_risk_level(self) -> None:
        """Update risk level based on current metrics."""
        # Default risk level
        risk_level = "normal"
        
        # Check drawdown
        if self.current_drawdown_pct >= self.max_drawdown_pct:
            risk_level = "extreme"
        elif self.current_drawdown_pct >= self.max_drawdown_pct * 0.75:
            risk_level = "high"
        elif self.current_drawdown_pct >= self.max_drawdown_pct * 0.5:
            risk_level = "elevated"
        
        # Check daily loss
        if self.daily_loss_pct >= self.max_daily_loss_pct:
            risk_level = "extreme"
        elif self.daily_loss_pct >= self.max_daily_loss_pct * 0.75 and risk_level != "extreme":
            risk_level = "high"
        elif self.daily_loss_pct >= self.max_daily_loss_pct * 0.5 and risk_level == "normal":
            risk_level = "elevated"
        
        # Check portfolio risk
        if self.portfolio_risk_pct >= self.max_portfolio_risk_pct:
            risk_level = max(risk_level, "high")
        elif self.portfolio_risk_pct >= self.max_portfolio_risk_pct * 0.75 and risk_level == "normal":
            risk_level = "elevated"
        
        # Update risk level if changed
        if risk_level != self.risk_level:
            logger.info(f"Risk level changed: {self.risk_level} -> {risk_level}")
            self.risk_level = risk_level
    
    def _update_trading_allowed(self) -> None:
        """Update trading allowed status based on risk level."""
        # Determine if trading is allowed based on risk level
        trading_allowed = True
        
        if self.risk_level == "extreme":
            trading_allowed = False
        elif self.risk_level == "high" and self.daily_loss_pct >= self.max_daily_loss_pct * 0.9:
            trading_allowed = False
        
        # Update trading allowed if changed
        if trading_allowed != self.trading_allowed:
            logger.info(f"Trading allowed changed: {self.trading_allowed} -> {trading_allowed}")
            self.trading_allowed = trading_allowed

    def can_place_trade(self, symbol: str, position_value: float) -> Tuple[bool, str]:
        """Check if a trade can be placed based on risk parameters.
        
        Args:
            symbol: The trading symbol
            position_value: Value of the position to be taken
            
        Returns:
            Tuple of (can_trade, reason)
        """
        # Check daily loss limit
        if self.daily_loss_pct > 0 and self.daily_loss_pct > self.max_daily_loss_pct:
            return False, f"Daily loss limit reached: {self.daily_loss_pct:.2%}"
        
        # Check portfolio heat (total risk exposure)
        if self.portfolio_risk_pct + (position_value / self.max_position_size_pct) > self.max_portfolio_risk_pct:
            return False, "Maximum portfolio exposure reached"
        
        return True, ""
    
    def calculate_stop_loss(self, entry_price: float, side: str = 'long') -> float:
        """Calculate stop loss price.
        
        Args:
            entry_price: Position entry price
            side: Trade side ('long' or 'short')
            
        Returns:
            Stop loss price
        """
        if side.lower() == 'long':
            return entry_price * (1 - STOP_LOSS_PCT)
        return entry_price * (1 + STOP_LOSS_PCT)
    
    def calculate_take_profit(self, entry_price: float, side: str = 'long') -> float:
        """Calculate take profit price.
        
        Args:
            entry_price: Position entry price
            side: Trade side ('long' or 'short')
            
        Returns:
            Take profit price
        """
        if side.lower() == 'long':
            return entry_price * (1 + TAKE_PROFIT_PCT)
        return entry_price * (1 - TAKE_PROFIT_PCT)
    
    def update_trade_result(self, trade_result: TradeResult) -> None:
        """Update risk metrics with trade result.
        
        Args:
            trade_result: Dictionary containing trade details and P/L
        """
        # Update daily P/L
        self.daily_loss_pct += trade_result.get('profit', 0)
        
        # Update risk metrics
        self.portfolio_risk_pct = self._calculate_portfolio_heat()
        self.current_drawdown_pct = self._calculate_drawdown()
        self.max_drawdown_pct = max(self.max_drawdown_pct, self.current_drawdown_pct)
        self.risk_level = self._update_risk_level()
        self.trading_allowed = self._update_trading_allowed()
    
    def _calculate_portfolio_heat(self) -> float:
        """Calculate current portfolio heat (risk exposure).
        
        Returns:
            Current portfolio heat value
        """
        # This could be enhanced to consider position correlations
        return (self.max_position_size_pct - self.max_position_size_pct) / self.max_position_size_pct
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage.
        
        Returns:
            Current drawdown as a percentage
        """
        peak = max(trade.get('equity', self.max_position_size_pct) for trade in self.trades_history)
        return (peak - self.max_position_size_pct) / peak
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio.
        
        Returns:
            Annualized Sharpe ratio
        """
        if len(self.trades_history) < 2:
            return 0.0
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(self.trades_history)):
            prev_equity = self.trades_history[i-1].get('equity', self.max_position_size_pct)
            curr_equity = self.trades_history[i].get('equity', self.max_position_size_pct)
            returns.append((curr_equity - prev_equity) / prev_equity)
        
        if not returns:
            return 0.0
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0 for simplicity)
        returns_array = np.array(returns)
        if returns_array.std() == 0:
            return 0.0
        
        return (returns_array.mean() / returns_array.std()) * np.sqrt(252)  # Annualized
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics.
        
        Returns:
            Dictionary containing all risk metrics
        """
        return self.risk_metrics.copy() 