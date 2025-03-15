"""
Position management module for the trading bot.
Handles position monitoring, risk management, and position lifecycle.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import pytz

from ..monitoring.logging.logger import get_logger
from ..utils.config import Config
from ..integrations.brokers import BrokerFactory
from ..utils.market_time import MarketTime
from .risk_manager import RiskManager
from ..monitoring.metrics.performance_metrics import PerformanceMetrics


logger = get_logger(__name__)


class PositionManager:
    """
    Manages trading positions, including monitoring, risk management,
    and position lifecycle operations.
    """
    
    def __init__(
        self,
        config: Config,
        broker_factory: BrokerFactory
    ) -> None:
        """
        Initialize the position manager.
        
        Args:
            config: Configuration object containing trading parameters
            broker_factory: Factory for broker operations
        """
        self.config = config
        self.broker_factory = broker_factory
        self.positions = {'stocks': {}, 'options': {}}
        self.daily_trades = {'stocks': 0, 'options': 0}
        self.daily_pl = {'stocks': 0.0, 'options': 0.0}
        self.market_time = MarketTime(config)
        self.risk_manager = RiskManager(config)
        self.performance_metrics = PerformanceMetrics(config)
    
    def monitor_positions(self) -> None:
        """Monitor and manage open positions."""
        try:
            for asset_type in ['stocks', 'options']:
                for position_id, position in self.positions[asset_type].items():
                    if self._should_exit_position(position):
                        self._close_position(position_id, asset_type)
        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}", exc_info=True)
    
    def _should_exit_position(self, position: Dict[str, Any]) -> bool:
        """
        Check if a position should be exited based on various criteria.
        
        Args:
            position: Position information dictionary
            
        Returns:
            bool: True if position should be exited, False otherwise
        """
        try:
            # Check risk-based exit conditions
            if self.risk_manager.should_exit_position(position):
                return True
            
            # Check time-based exit
            entry_time = position.get('entry_time')
            if entry_time and self.market_time.should_exit_by_time(entry_time):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {str(e)}", exc_info=True)
            return False
    
    def can_open_position(
        self,
        symbol: str,
        position_size: float,
        account_value: float
    ) -> bool:
        """
        Check if a new position can be opened based on risk limits.
        
        Args:
            symbol: Symbol to trade
            position_size: Proposed position size
            account_value: Current account value
            
        Returns:
            bool: True if position can be opened
        """
        return self.risk_manager.can_open_position(
            symbol,
            position_size,
            account_value,
            self.positions
        )
    
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
        return self.risk_manager.get_position_size(
            symbol,
            account_value,
            volatility
        )
    
    def _close_position(self, position_id: str, asset_type: str) -> bool:
        """
        Close a position.
        
        Args:
            position_id: ID of the position to close
            asset_type: Type of asset (stocks/options)
            
        Returns:
            bool: True if position was closed successfully, False otherwise
        """
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker:
                logger.error("No active broker available")
                return False
            
            position = self.positions[asset_type].get(position_id)
            if not position:
                logger.error(f"Position {position_id} not found")
                return False
            
            # Close position through broker
            if active_broker.close_position(position_id):
                # Update metrics
                self.daily_trades[asset_type] += 1
                unrealized_pl = position.get('unrealized_pl', 0.0)
                self.daily_pl[asset_type] += unrealized_pl
                
                # Update performance metrics
                self.performance_metrics.update_trade_metrics({
                    'symbol': position.get('symbol'),
                    'entry_price': position.get('entry_price'),
                    'exit_price': position.get('current_price'),
                    'quantity': position.get('quantity'),
                    'pl': unrealized_pl
                })
                
                # Remove from tracked positions
                del self.positions[asset_type][position_id]
                logger.info(f"Closed position {position_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}", exc_info=True)
            return False
    
    def reset_daily_metrics(self) -> None:
        """Reset daily trading metrics."""
        try:
            if self.market_time.should_reset_daily_metrics():
                self.daily_trades = {'stocks': 0, 'options': 0}
                self.daily_pl = {'stocks': 0.0, 'options': 0.0}
                logger.info("Daily metrics reset")
                
        except Exception as e:
            logger.error(f"Error resetting daily metrics: {str(e)}", exc_info=True)
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List[Dict]: List of open positions
        """
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker:
                logger.error("No active broker available")
                return []
            
            positions = active_broker.get_positions()
            return positions if positions else []
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}", exc_info=True)
            return []
    
    def get_recent_trades(self) -> List[Dict[str, Any]]:
        """
        Get recent trades.
        
        Returns:
            List[Dict]: List of recent trades
        """
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker:
                logger.error("No active broker available")
                return []
            
            trades = active_broker.get_recent_trades()
            return trades if trades else []
            
        except Exception as e:
            logger.error(f"Error getting recent trades: {str(e)}", exc_info=True)
            return []
    
    def get_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dict: Performance metrics
        """
        try:
            active_broker = self.broker_factory.get_active_broker()
            if not active_broker:
                logger.error("No active broker available")
                return {}
            
            # Get account information
            account = active_broker.get_account_info()
            if not account:
                return {}
            
            # Calculate daily P&L
            positions = self.get_positions()
            daily_pl = sum(float(pos.get('unrealized_intraday_pl', 0)) for pos in positions)
            
            # Get total equity and cash
            equity = float(account.get('equity', 0))
            cash = float(account.get('cash', 0))
            
            # Update risk metrics
            self.risk_manager.update_metrics(equity)
            
            # Update performance metrics
            self.performance_metrics.update_daily_return(daily_pl, equity)
            
            # Get metrics
            risk_metrics = self.risk_manager.get_risk_metrics()
            performance_metrics = self.performance_metrics.get_metrics()
            
            return {
                'equity': equity,
                'cash': cash,
                'daily_pl': daily_pl,
                'total_positions': len(positions),
                'daily_trades': sum(self.daily_trades.values()),
                'risk_metrics': risk_metrics,
                'performance_metrics': performance_metrics,
                'last_update': datetime.now(pytz.UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}", exc_info=True)
            return {} 