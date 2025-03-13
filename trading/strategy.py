"""
Strategy module for the KryptoBot Trading System.

This module defines the Strategy class that serves as a base for all trading strategies.
"""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)

class Strategy:
    """Base class for all trading strategies."""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        """Initialize a trading strategy.
        
        Args:
            name: Name of the strategy
            parameters: Dictionary of strategy parameters
        """
        self.name = name
        self.parameters = parameters or {}
        self.is_active = True
        logger.info(f"Strategy {name} initialized with parameters: {parameters}")
    
    def analyze(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market data and generate trading signals.
        
        Args:
            market_data: DataFrame containing market data
            
        Returns:
            Dictionary containing analysis results and trading signals
        """
        # This is a base implementation that should be overridden by subclasses
        logger.warning(f"Base analyze method called for strategy {self.name}. This should be overridden.")
        return {
            "strategy": self.name,
            "signal": "NEUTRAL",
            "confidence": 0.0,
            "parameters": self.parameters
        }
    
    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters.
        
        Args:
            parameters: Dictionary of parameters to update
        """
        self.parameters.update(parameters)
        logger.info(f"Strategy {self.name} parameters updated: {parameters}")
    
    def activate(self) -> None:
        """Activate the strategy."""
        self.is_active = True
        logger.info(f"Strategy {self.name} activated")
    
    def deactivate(self) -> None:
        """Deactivate the strategy."""
        self.is_active = False
        logger.info(f"Strategy {self.name} deactivated")
    
    def is_valid_for_symbol(self, symbol: str) -> bool:
        """Check if the strategy is valid for the given symbol.
        
        Args:
            symbol: Trading symbol to check
            
        Returns:
            True if the strategy is valid for the symbol, False otherwise
        """
        # Default implementation assumes the strategy is valid for all symbols
        return True 