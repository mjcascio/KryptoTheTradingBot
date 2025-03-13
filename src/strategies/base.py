#!/usr/bin/env python3
"""
Base Strategy Module

This module defines the base strategy class that all trading strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, description: str):
        """Initialize the strategy
        
        Args:
            name (str): Strategy name
            description (str): Strategy description
        """
        self.name = name
        self.description = description
        self.positions: Dict[str, Dict] = {}
        self.orders: Dict[str, Dict] = {}
        logger.info(f"Initialized strategy: {name}")

    @abstractmethod
    def analyze_market(self, market_data: Dict) -> List[Dict]:
        """Analyze market data and generate trading signals
        
        Args:
            market_data (Dict): Current market data
            
        Returns:
            List of trading signals
        """
        pass

    @abstractmethod
    def calculate_position_size(self, signal: Dict, account_info: Dict) -> float:
        """Calculate the position size for a trading signal
        
        Args:
            signal (Dict): Trading signal
            account_info (Dict): Account information
            
        Returns:
            Position size
        """
        pass

    @abstractmethod
    def set_stop_loss(self, position: Dict) -> float:
        """Set stop loss price for a position
        
        Args:
            position (Dict): Position information
            
        Returns:
            Stop loss price
        """
        pass

    @abstractmethod
    def set_take_profit(self, position: Dict) -> float:
        """Set take profit price for a position
        
        Args:
            position (Dict): Position information
            
        Returns:
            Take profit price
        """
        pass

    def update_position(self, position: Dict) -> None:
        """Update position information
        
        Args:
            position (Dict): Updated position information
        """
        self.positions[position['symbol']] = position
        logger.debug(f"Updated position: {position['symbol']}")

    def update_order(self, order: Dict) -> None:
        """Update order information
        
        Args:
            order (Dict): Updated order information
        """
        self.orders[order['id']] = order
        logger.debug(f"Updated order: {order['id']}")

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position information for a symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Position information if exists, None otherwise
        """
        return self.positions.get(symbol)

    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order information
        
        Args:
            order_id (str): Order ID
            
        Returns:
            Order information if exists, None otherwise
        """
        return self.orders.get(order_id)

    def get_all_positions(self) -> List[Dict]:
        """Get all current positions
        
        Returns:
            List of position dictionaries
        """
        return list(self.positions.values())

    def get_all_orders(self) -> List[Dict]:
        """Get all current orders
        
        Returns:
            List of order dictionaries
        """
        return list(self.orders.values())

    def close_position(self, symbol: str) -> None:
        """Close a position
        
        Args:
            symbol (str): Trading symbol
        """
        if symbol in self.positions:
            del self.positions[symbol]
            logger.info(f"Closed position: {symbol}")

    def cancel_order(self, order_id: str) -> None:
        """Cancel an order
        
        Args:
            order_id (str): Order ID
        """
        if order_id in self.orders:
            del self.orders[order_id]
            logger.info(f"Cancelled order: {order_id}")

    def get_strategy_info(self) -> Dict:
        """Get strategy information
        
        Returns:
            Strategy information dictionary
        """
        return {
            'name': self.name,
            'description': self.description,
            'num_positions': len(self.positions),
            'num_orders': len(self.orders)
        } 