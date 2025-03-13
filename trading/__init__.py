"""
Trading module for KryptoBot Trading System.

This module provides comprehensive functionality for managing trading operations,
including order management, risk assessment, and portfolio operations. It serves
as the core trading engine of the system.

Key Components:
    - Order Management: Creation, validation, and tracking of trading orders
    - Risk Management: Position sizing, stop losses, and exposure control
    - Portfolio Management: Position tracking and portfolio metrics

Example:
    from trading.orders import OrderManager
    from trading.risk import RiskManager
    from trading.portfolio import PortfolioManager

    # Initialize components
    order_manager = OrderManager()
    risk_manager = RiskManager(initial_equity=100000.0)
    portfolio_manager = PortfolioManager(max_positions=10)

    # Create and validate an order
    order = order_manager.create_order(
        symbol="AAPL",
        side="buy",
        quantity=100
    )

    # Check risk parameters
    can_trade, reason = risk_manager.can_place_trade(
        symbol="AAPL",
        position_value=15000.0
    )

    if can_trade:
        # Add position to portfolio
        portfolio_manager.add_position("AAPL", {
            "quantity": 100,
            "entry_price": 150.0
        })
"""

from .orders import *
from .risk import *
from .portfolio import * 