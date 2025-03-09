from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

class BaseBroker(ABC):
    """
    Abstract base class for broker implementations.
    All platform-specific brokers must implement these methods.
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the broker's API.
        Returns True if connection is successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the broker's API.
        Returns True if disconnection is successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including equity, cash, buying power, etc.
        Returns a dictionary with account details.
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current positions.
        Returns a dictionary with symbol as key and position details as value.
        """
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, qty: float, side: str, order_type: str, 
                   time_in_force: str = 'day', limit_price: float = None, 
                   stop_price: float = None) -> Dict[str, Any]:
        """
        Place an order.
        Returns order information if successful.
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order by ID.
        Returns True if cancellation is successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get order information by ID.
        Returns order details.
        """
        pass
    
    @abstractmethod
    def get_orders(self, status: str = 'open') -> List[Dict[str, Any]]:
        """
        Get all orders with the specified status.
        Returns a list of order details.
        """
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str, timeframe: str = '15Min', 
                       limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Get market data for a symbol.
        Returns a pandas DataFrame with OHLCV data.
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get the current price of a symbol.
        Returns the current price as a float.
        """
        pass
    
    @abstractmethod
    def check_market_hours(self) -> bool:
        """
        Check if the market is currently open.
        Returns True if market is open, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_next_market_times(self) -> tuple:
        """
        Get the next market open and close times.
        Returns a tuple of (next_open, next_close) as datetime objects.
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the name of the trading platform.
        Returns the platform name as a string.
        """
        pass
    
    @abstractmethod
    def get_platform_type(self) -> str:
        """
        Get the type of the trading platform (e.g., 'stocks', 'forex', 'crypto').
        Returns the platform type as a string.
        """
        pass 