"""Position risk analytics module."""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class RiskMetrics:
    """Risk metrics for a position."""
    
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    value_at_risk: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    volatility: float
    beta: Optional[float] = None

class RiskAnalyzer:
    """Position risk analytics calculator."""
    
    def __init__(
        self,
        price_data: pd.DataFrame,
        risk_free_rate: float = 0.02,
        confidence_level: float = 0.95,
        benchmark_data: Optional[pd.DataFrame] = None
    ) -> None:
        """Initialize risk analyzer.
        
        Args:
            price_data: Historical price data
            risk_free_rate: Annual risk-free rate
            confidence_level: VaR confidence level
            benchmark_data: Benchmark price data for beta calculation
        """
        self.price_data = price_data
        self.risk_free_rate = risk_free_rate
        self.confidence_level = confidence_level
        self.benchmark_data = benchmark_data
        
        # Calculate daily returns
        self.returns = price_data["close"].pct_change().dropna()
        if benchmark_data is not None:
            self.benchmark_returns = benchmark_data["close"].pct_change().dropna()
    
    def calculate_unrealized_pnl(
        self,
        position_size: float,
        entry_price: float,
        current_price: float
    ) -> tuple[float, float]:
        """Calculate unrealized P&L.
        
        Args:
            position_size: Position size
            entry_price: Entry price
            current_price: Current price
            
        Returns:
            Unrealized P&L and percentage P&L
        """
        unrealized_pnl = position_size * (current_price - entry_price)
        unrealized_pnl_pct = (current_price - entry_price) / entry_price
        return unrealized_pnl, unrealized_pnl_pct
    
    def calculate_value_at_risk(
        self,
        position_value: float,
        timeframe_days: int = 1
    ) -> float:
        """Calculate Value at Risk.
        
        Args:
            position_value: Current position value
            timeframe_days: VaR timeframe in days
            
        Returns:
            Value at Risk
        """
        # Calculate daily VaR
        var_daily = -np.percentile(self.returns, (1 - self.confidence_level) * 100)
        
        # Scale to desired timeframe
        var = var_daily * np.sqrt(timeframe_days)
        
        return position_value * var
    
    def calculate_sharpe_ratio(self, window_days: int = 252) -> float:
        """Calculate Sharpe Ratio.
        
        Args:
            window_days: Annualization window
            
        Returns:
            Sharpe Ratio
        """
        # Annualize returns and volatility
        avg_return = self.returns.mean() * window_days
        volatility = self.returns.std() * np.sqrt(window_days)
        
        return (avg_return - self.risk_free_rate) / volatility
    
    def calculate_max_drawdown(self) -> tuple[float, float]:
        """Calculate Maximum Drawdown.
        
        Returns:
            Absolute and percentage maximum drawdown
        """
        prices = self.price_data["close"]
        peak = prices.expanding(min_periods=1).max()
        drawdown = prices - peak
        drawdown_pct = drawdown / peak
        
        max_drawdown = drawdown.min()
        max_drawdown_pct = drawdown_pct.min()
        
        return max_drawdown, max_drawdown_pct
    
    def calculate_volatility(self, window_days: int = 252) -> float:
        """Calculate annualized volatility.
        
        Args:
            window_days: Annualization window
            
        Returns:
            Annualized volatility
        """
        return self.returns.std() * np.sqrt(window_days)
    
    def calculate_beta(self) -> Optional[float]:
        """Calculate beta against benchmark.
        
        Returns:
            Beta or None if no benchmark data
        """
        if self.benchmark_data is None:
            return None
        
        # Calculate covariance and variance
        covariance = self.returns.cov(self.benchmark_returns)
        variance = self.benchmark_returns.var()
        
        return covariance / variance
    
    def get_risk_metrics(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        current_price: float
    ) -> RiskMetrics:
        """Get comprehensive risk metrics for a position.
        
        Args:
            symbol: Trading pair symbol
            position_size: Position size
            entry_price: Entry price
            current_price: Current price
            
        Returns:
            Risk metrics
        """
        # Calculate position metrics
        position_value = position_size * current_price
        unrealized_pnl, unrealized_pnl_pct = self.calculate_unrealized_pnl(
            position_size,
            entry_price,
            current_price
        )
        
        # Calculate risk metrics
        value_at_risk = self.calculate_value_at_risk(position_value)
        sharpe_ratio = self.calculate_sharpe_ratio()
        max_drawdown, max_drawdown_pct = self.calculate_max_drawdown()
        volatility = self.calculate_volatility()
        beta = self.calculate_beta()
        
        return RiskMetrics(
            symbol=symbol,
            position_size=position_size,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            value_at_risk=value_at_risk,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            volatility=volatility,
            beta=beta
        )

class PortfolioRisk:
    """Portfolio-level risk analytics."""
    
    def __init__(
        self,
        positions: List[RiskMetrics],
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> None:
        """Initialize portfolio risk analyzer.
        
        Args:
            positions: List of position risk metrics
            correlation_matrix: Asset correlation matrix
        """
        self.positions = positions
        self.correlation_matrix = correlation_matrix
    
    def calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value.
        
        Returns:
            Portfolio value
        """
        return sum(pos.position_size * pos.current_price for pos in self.positions)
    
    def calculate_portfolio_pnl(self) -> tuple[float, float]:
        """Calculate portfolio P&L.
        
        Returns:
            Absolute and percentage P&L
        """
        total_pnl = sum(pos.unrealized_pnl for pos in self.positions)
        portfolio_value = self.calculate_portfolio_value()
        pnl_pct = total_pnl / (portfolio_value - total_pnl)
        
        return total_pnl, pnl_pct
    
    def calculate_position_weights(self) -> Dict[str, float]:
        """Calculate position weights.
        
        Returns:
            Dictionary of position weights
        """
        portfolio_value = self.calculate_portfolio_value()
        return {
            pos.symbol: (pos.position_size * pos.current_price) / portfolio_value
            for pos in self.positions
        }
    
    def calculate_portfolio_var(self) -> float:
        """Calculate portfolio Value at Risk.
        
        Returns:
            Portfolio VaR
        """
        if not self.correlation_matrix:
            # Simple sum of individual VaRs if no correlation matrix
            return sum(pos.value_at_risk for pos in self.positions)
        
        # Calculate portfolio VaR using correlation matrix
        weights = self.calculate_position_weights()
        position_vars = np.array([pos.value_at_risk for pos in self.positions])
        
        # Create weight matrix
        w = np.array(list(weights.values()))
        
        # Calculate portfolio VaR
        portfolio_var = np.sqrt(
            w.T @ self.correlation_matrix.values @ w
        ) * sum(position_vars)
        
        return portfolio_var
    
    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get comprehensive portfolio metrics.
        
        Returns:
            Portfolio metrics
        """
        portfolio_value = self.calculate_portfolio_value()
        total_pnl, pnl_pct = self.calculate_portfolio_pnl()
        weights = self.calculate_position_weights()
        portfolio_var = self.calculate_portfolio_var()
        
        # Calculate weighted average metrics
        weighted_sharpe = sum(
            pos.sharpe_ratio * weights[pos.symbol]
            for pos in self.positions
        )
        weighted_volatility = sum(
            pos.volatility * weights[pos.symbol]
            for pos in self.positions
        )
        
        return {
            "portfolio_value": portfolio_value,
            "unrealized_pnl": total_pnl,
            "unrealized_pnl_pct": pnl_pct,
            "position_weights": weights,
            "value_at_risk": portfolio_var,
            "sharpe_ratio": weighted_sharpe,
            "volatility": weighted_volatility,
            "positions": len(self.positions)
        } 