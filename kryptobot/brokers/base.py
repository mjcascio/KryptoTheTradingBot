"""
Base Broker Module - Abstract base class for broker implementations.

This module defines the BaseBroker abstract base class that all broker
implementations must inherit from. It defines the interface that all
brokers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

class BaseBroker(ABC):
    """
    Abstract base class for broker implementations.
    
    This class defines the interface that all brokers must implement.
    Concrete broker implementations should inherit from this class and
    implement all abstract methods.
    
    Attributes:
        name (str): Name of the broker
        connected (bool): Whether the broker is connected
        api_key (str): API key for the broker
        api_secret (str): API secret for the broker
        base_url (str): Base URL for the broker API
    """
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = None):
        """
        Initialize the broker.
        
        Args:
            api_key (str): API key for the broker
            api_secret (str): API secret for the broker
            base_url (str, optional): Base URL for the broker API
        """
        self.name = "BaseBroker"
        self.connected = False
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the broker.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dict[str, Any]: Account information with the following keys:
                - equity (float): Account equity
                - buying_power (float): Buying power
                - cash (float): Cash balance
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List[Dict[str, Any]]: List of positions with the following keys:
                - symbol (str): Symbol
                - quantity (float): Position quantity
                - entry_price (float): Entry price
                - current_price (float): Current price
                - market_value (float): Market value
                - unrealized_pl (float): Unrealized profit/loss
                - unrealized_plpc (float): Unrealized profit/loss percentage
                - stop_loss (float, optional): Stop loss price
                - take_profit (float, optional): Take profit price
        """
        pass
    
    @abstractmethod
    def get_trades(self) -> List[Dict[str, Any]]:
        """
        Get recent trades.
        
        Returns:
            List[Dict[str, Any]]: List of trades with the following keys:
                - symbol (str): Symbol
                - side (str): Trade side ('buy' or 'sell')
                - quantity (float): Trade quantity
                - entry_price (float): Entry price
                - exit_price (float): Exit price
                - entry_time (str): Entry time
                - exit_time (str): Exit time
                - profit_loss (float): Profit/loss
                - profit_loss_pct (float): Profit/loss percentage
        """
        pass
    
    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """
        Get market data bars.
        
        Args:
            symbol (str): Symbol
            timeframe (str): Timeframe (e.g., '1Min', '5Min', '1H', '1D')
            limit (int): Number of bars to get
            
        Returns:
            pd.DataFrame: Market data with the following columns:
                - timestamp (datetime): Bar timestamp
                - open (float): Open price
                - high (float): High price
                - low (float): Low price
                - close (float): Close price
                - volume (int): Volume
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the current price for a symbol.
        
        Args:
            symbol (str): Symbol
            
        Returns:
            Optional[float]: Current price
        """
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, quantity: float, side: str, order_type: str = 'market',
                   time_in_force: str = 'day', limit_price: float = None, stop_price: float = None,
                   stop_loss: float = None, take_profit: float = None) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            symbol (str): Symbol
            quantity (float): Order quantity
            side (str): Order side ('buy' or 'sell')
            order_type (str, optional): Order type ('market', 'limit', 'stop', 'stop_limit')
            time_in_force (str, optional): Time in force ('day', 'gtc', 'ioc', 'fok')
            limit_price (float, optional): Limit price for limit orders
            stop_price (float, optional): Stop price for stop orders
            stop_loss (float, optional): Stop loss price
            take_profit (float, optional): Take profit price
            
        Returns:
            Dict[str, Any]: Order information with the following keys:
                - id (str): Order ID
                - symbol (str): Symbol
                - quantity (float): Order quantity
                - side (str): Order side
                - type (str): Order type
                - status (str): Order status
                - filled_quantity (float): Filled quantity
                - filled_price (float): Filled price
                - created_at (str): Creation time
                - updated_at (str): Last update time
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id (str): Order ID
            
        Returns:
            bool: True if cancellation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get order information.
        
        Args:
            order_id (str): Order ID
            
        Returns:
            Dict[str, Any]: Order information with the following keys:
                - id (str): Order ID
                - symbol (str): Symbol
                - quantity (float): Order quantity
                - side (str): Order side
                - type (str): Order type
                - status (str): Order status
                - filled_quantity (float): Filled quantity
                - filled_price (float): Filled price
                - created_at (str): Creation time
                - updated_at (str): Last update time
        """
        pass
    
    @abstractmethod
    def get_orders(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get orders.
        
        Args:
            status (str, optional): Order status filter
            
        Returns:
            List[Dict[str, Any]]: List of orders with the following keys:
                - id (str): Order ID
                - symbol (str): Symbol
                - quantity (float): Order quantity
                - side (str): Order side
                - type (str): Order type
                - status (str): Order status
                - filled_quantity (float): Filled quantity
                - filled_price (float): Filled price
                - created_at (str): Creation time
                - updated_at (str): Last update time
        """
        pass
    
    @abstractmethod
    def update_position(self, symbol: str, stop_loss: float = None, take_profit: float = None) -> bool:
        """
        Update a position.
        
        Args:
            symbol (str): Symbol
            stop_loss (float, optional): Stop loss price
            take_profit (float, optional): Take profit price
            
        Returns:
            bool: True if update successful, False otherwise
        """
        pass
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        
        Returns:
            bool: True if the market is open, False otherwise
        """
        # Default implementation, should be overridden by concrete brokers
        return False
    
    def get_next_market_times(self) -> tuple:
        """
        Get the next market open and close times.
        
        Returns:
            tuple: (next_open, next_close) as datetime objects
        """
        # Default implementation, should be overridden by concrete brokers
        return None, None 