"""Strategy manager for handling multiple trading strategies."""

import logging
from typing import Dict, List, Optional, Any

from .base import BaseStrategy
from ..utils.market_time import MarketTime

logger = logging.getLogger(__name__)


class StrategyManager:
    """Manages multiple trading strategies."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the strategy manager.
        
        Args:
            config: Configuration dictionary containing:
                - strategy_configs: List of strategy configurations
                - market_hours: Market hours configuration
        """
        self.config = config
        self.strategies: Dict[str, BaseStrategy] = {}
        self.active_strategies: Dict[str, bool] = {}
        self.market_time = MarketTime(config.get('market_hours', {}))
        
        # Initialize strategies from config
        strategy_configs = config.get('strategy_configs', [])
        for strategy_config in strategy_configs:
            self.add_strategy(strategy_config)

    def add_strategy(self, strategy_config: Dict[str, Any]) -> bool:
        """Add a new strategy.
        
        Args:
            strategy_config: Strategy configuration
            
        Returns:
            bool: True if strategy was added successfully
        """
        try:
            strategy_type = strategy_config.get('type')
            strategy_id = strategy_config.get('id')
            
            if not strategy_type or not strategy_id:
                logger.error("Strategy config missing type or id")
                return False
                
            if strategy_id in self.strategies:
                logger.error(f"Strategy {strategy_id} already exists")
                return False
                
            # Import strategy class dynamically
            module_path = f".{strategy_type.lower()}"
            try:
                strategy_module = __import__(
                    module_path,
                    globals(),
                    locals(),
                    ['Strategy'],
                    1
                )
                strategy_class = getattr(strategy_module, 'Strategy')
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to import strategy {strategy_type}: {e}")
                return False
                
            # Create strategy instance
            strategy = strategy_class(strategy_config)
            self.strategies[strategy_id] = strategy
            self.active_strategies[strategy_id] = False
            
            logger.info(f"Added strategy {strategy_id} of type {strategy_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding strategy: {e}")
            return False

    def remove_strategy(self, strategy_id: str) -> bool:
        """Remove a strategy.
        
        Args:
            strategy_id: ID of strategy to remove
            
        Returns:
            bool: True if strategy was removed successfully
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
            
        try:
            # Stop strategy if running
            if self.active_strategies.get(strategy_id):
                self.stop_strategy(strategy_id)
                
            del self.strategies[strategy_id]
            del self.active_strategies[strategy_id]
            
            logger.info(f"Removed strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing strategy {strategy_id}: {e}")
            return False

    def start_strategy(self, strategy_id: str) -> bool:
        """Start a strategy.
        
        Args:
            strategy_id: ID of strategy to start
            
        Returns:
            bool: True if strategy was started successfully
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
            
        if self.active_strategies.get(strategy_id):
            logger.warning(f"Strategy {strategy_id} already running")
            return True
            
        try:
            strategy = self.strategies[strategy_id]
            if strategy.start():
                self.active_strategies[strategy_id] = True
                logger.info(f"Started strategy {strategy_id}")
                return True
                
            logger.error(f"Failed to start strategy {strategy_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error starting strategy {strategy_id}: {e}")
            return False

    def stop_strategy(self, strategy_id: str) -> bool:
        """Stop a strategy.
        
        Args:
            strategy_id: ID of strategy to stop
            
        Returns:
            bool: True if strategy was stopped successfully
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
            
        if not self.active_strategies.get(strategy_id):
            logger.warning(f"Strategy {strategy_id} not running")
            return True
            
        try:
            strategy = self.strategies[strategy_id]
            if strategy.stop():
                self.active_strategies[strategy_id] = False
                logger.info(f"Stopped strategy {strategy_id}")
                return True
                
            logger.error(f"Failed to stop strategy {strategy_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error stopping strategy {strategy_id}: {e}")
            return False

    def start_all(self) -> bool:
        """Start all strategies.
        
        Returns:
            bool: True if all strategies were started successfully
        """
        success = True
        for strategy_id in self.strategies:
            if not self.start_strategy(strategy_id):
                success = False
        return success

    def stop_all(self) -> bool:
        """Stop all strategies.
        
        Returns:
            bool: True if all strategies were stopped successfully
        """
        success = True
        for strategy_id in self.strategies:
            if not self.stop_strategy(strategy_id):
                success = False
        return success

    def get_active_strategies(self) -> List[str]:
        """Get list of active strategy IDs.
        
        Returns:
            List of active strategy IDs
        """
        return [
            strategy_id
            for strategy_id, active in self.active_strategies.items()
            if active
        ]

    def get_strategy_status(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a strategy.
        
        Args:
            strategy_id: ID of strategy to get status for
            
        Returns:
            Strategy status dictionary or None if not found
        """
        if strategy_id not in self.strategies:
            return None
            
        strategy = self.strategies[strategy_id]
        return {
            'id': strategy_id,
            'type': strategy.__class__.__name__,
            'active': self.active_strategies[strategy_id],
            'metrics': strategy.get_metrics()
        }

    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get status of all strategies.
        
        Returns:
            List of strategy status dictionaries
        """
        return [
            self.get_strategy_status(strategy_id)
            for strategy_id in self.strategies
        ]

    def update(self) -> None:
        """Update all active strategies."""
        if not self.market_time.is_market_open():
            return
            
        for strategy_id, active in self.active_strategies.items():
            if active:
                try:
                    strategy = self.strategies[strategy_id]
                    strategy.update()
                except Exception as e:
                    logger.error(
                        f"Error updating strategy {strategy_id}: {e}"
                    ) 