"""Portfolio management functionality for the KryptoBot Trading System."""

import logging
from typing import Dict, Any, List
from datetime import datetime
from config.settings import MAX_POSITION_SIZE_PCT, MIN_POSITION_SIZE
from market.analysis import get_sector_mappings, calculate_sector_allocation

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, equity: float = 100000.0, max_positions: int = 10):
        """Initialize the portfolio manager
        
        Args:
            equity: Initial portfolio equity
            max_positions: Maximum number of positions allowed
        """
        self.equity = equity
        self.max_positions = max_positions
        self.positions = {}
        self.sector_exposure = {}
        self.last_update = datetime.now()
    
    def add_position(self, symbol: str, position_data: Dict[str, Any]) -> bool:
        """Add a new position to the portfolio
        
        Args:
            symbol: The trading symbol
            position_data: Position details including quantity, entry price, etc.
            
        Returns:
            True if position was added successfully, False otherwise
        """
        if len(self.positions) >= self.max_positions:
            logger.warning(f"Cannot add position {symbol}: Maximum positions reached")
            return False
        
        self.positions[symbol] = position_data
        self._update_sector_exposure()
        self.last_update = datetime.now()
        return True
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]) -> bool:
        """Update an existing position
        
        Args:
            symbol: The trading symbol
            position_data: Updated position details
            
        Returns:
            True if position was updated successfully, False otherwise
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot update position {symbol}: Position not found")
            return False
        
        self.positions[symbol].update(position_data)
        self._update_sector_exposure()
        self.last_update = datetime.now()
        return True
    
    def remove_position(self, symbol: str) -> bool:
        """Remove a position from the portfolio
        
        Args:
            symbol: The trading symbol
            
        Returns:
            True if position was removed successfully, False otherwise
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot remove position {symbol}: Position not found")
            return False
        
        del self.positions[symbol]
        self._update_sector_exposure()
        self.last_update = datetime.now()
        return True
    
    def calculate_position_size(self, symbol: str, current_price: float) -> float:
        """Calculate position size based on equity and risk parameters
        
        Args:
            symbol: The trading symbol
            current_price: Current market price
            
        Returns:
            Position size in units/shares
        """
        # Calculate maximum position value
        max_position_value = self.equity * MAX_POSITION_SIZE_PCT
        
        # Calculate number of shares/units
        position_size = max_position_value / current_price
        
        # Check minimum position size
        if position_size * current_price < MIN_POSITION_SIZE:
            logger.info(f"Position size for {symbol} too small: ${position_size * current_price:.2f} < ${MIN_POSITION_SIZE}")
            return 0
        
        return position_size
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value
        
        Returns:
            Current portfolio value
        """
        total_value = self.equity
        for position in self.positions.values():
            if 'quantity' in position and 'current_price' in position:
                total_value += position['quantity'] * position['current_price']
        return total_value
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary
        
        Returns:
            Dictionary containing portfolio summary information
        """
        return {
            'equity': self.equity,
            'positions_count': len(self.positions),
            'total_value': self.get_portfolio_value(),
            'sector_exposure': self.sector_exposure,
            'last_update': self.last_update.isoformat()
        }
    
    def _update_sector_exposure(self):
        """Update sector exposure calculations"""
        # Get sector mappings for current positions
        symbols = list(self.positions.keys())
        sector_mappings = get_sector_mappings(symbols)
        
        # Calculate sector allocation
        self.sector_exposure = calculate_sector_allocation(
            self.positions,
            sector_mappings
        ) 