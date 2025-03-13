"""Market data models for Coinbase integration."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

@dataclass
class MarketData:
    """Market data for a trading pair."""
    
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime

@dataclass
class OrderBook:
    """Order book for a trading pair."""
    
    symbol: str
    bids: List[Tuple[float, float]]  # List of (price, size) tuples
    asks: List[Tuple[float, float]]  # List of (price, size) tuples
    timestamp: datetime

@dataclass
class Trade:
    """Trade data."""
    
    id: str
    symbol: str
    price: float
    size: float
    side: str
    timestamp: datetime 