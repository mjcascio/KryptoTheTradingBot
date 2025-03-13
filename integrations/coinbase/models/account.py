"""Account and position models for Coinbase integration."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Account:
    """Trading account information."""
    
    id: str
    currency: str
    balance: float
    available: float
    hold: float

@dataclass
class Position:
    """Trading position information."""
    
    symbol: str
    quantity: float
    entry_price: float
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None 