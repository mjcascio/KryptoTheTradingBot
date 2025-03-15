"""Base broker class that defines the interface for all brokers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class BaseBroker(ABC):
    """Abstract base class for broker implementations."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the broker with configuration."""
        self.config = config
        self.is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the broker."""
        pass

    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        pass

    @abstractmethod
    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get open orders."""
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "day"
    ) -> Dict[str, Any]:
        """Place an order."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        pass

    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a specific symbol."""
        pass

    @abstractmethod
    async def close_position(self, symbol: str) -> bool:
        """Close position for a specific symbol."""
        pass

    @abstractmethod
    async def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get historical bars for a symbol."""
        pass

    @abstractmethod
    async def get_last_quote(self, symbol: str) -> Dict[str, Any]:
        """Get last quote for a symbol."""
        pass

    @abstractmethod
    async def get_last_trade(self, symbol: str) -> Dict[str, Any]:
        """Get last trade for a symbol."""
        pass

    @abstractmethod
    async def get_account_history(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get account history."""
        pass

    @abstractmethod
    async def get_market_hours(self) -> Dict[str, Any]:
        """Get market hours."""
        pass 