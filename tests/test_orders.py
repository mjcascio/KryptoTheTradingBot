"""Tests for the order management system."""

import pytest
from datetime import datetime
from trading.orders import (
    Order, OrderManager, OrderType, OrderSide,
    TimeInForce, OrderError, ValidationError
)

@pytest.mark.trading
class TestOrder:
    """Test suite for Order class."""
    
    def test_order_creation(self):
        """Test basic order creation."""
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            price=150.0
        )
        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.quantity == 100
        assert order.price == 150.0
        assert order.status == "new"
    
    def test_order_validation(self):
        """Test order parameter validation."""
        # Test invalid quantity
        with pytest.raises(ValidationError):
            Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=-100
            )
        
        # Test missing price for limit order
        with pytest.raises(ValidationError):
            Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.LIMIT
            )
        
        # Test missing stop price for stop order
        with pytest.raises(ValidationError):
            Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.STOP
            )
    
    def test_order_update(self):
        """Test order update functionality."""
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            price=150.0
        )
        
        # Test partial fill
        order.update({
            'status': 'partially_filled',
            'filled_quantity': 50,
            'filled_avg_price': 149.5
        })
        
        assert order.status == 'partially_filled'
        assert order.filled_quantity == 50
        assert order.filled_avg_price == 149.5
        
        # Test complete fill
        order.update({
            'status': 'filled',
            'filled_quantity': 100,
            'filled_avg_price': 149.75
        })
        
        assert order.status == 'filled'
        assert order.filled_quantity == 100
        assert order.filled_avg_price == 149.75
    
    def test_order_to_dict(self):
        """Test order serialization to dictionary."""
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            price=150.0
        )
        
        order_dict = order.to_dict()
        assert order_dict['symbol'] == "AAPL"
        assert order_dict['side'] == "buy"
        assert order_dict['quantity'] == 100
        assert order_dict['price'] == 150.0
        assert 'created_at' in order_dict
        assert 'updated_at' in order_dict

@pytest.mark.trading
class TestOrderManager:
    """Test suite for OrderManager class."""
    
    def test_create_order(self, order_manager):
        """Test order creation through manager."""
        order = order_manager.create_order(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=150.0
        )
        
        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.quantity == 100
        assert order.price == 150.0
        assert order.client_order_id in order_manager.orders
    
    def test_update_order(self, order_manager):
        """Test order update through manager."""
        order = order_manager.create_order(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=150.0
        )
        
        order_id = order.client_order_id
        
        # Test partial fill
        updated_order = order_manager.update_order(
            order_id,
            {
                'status': 'partially_filled',
                'filled_quantity': 50,
                'filled_avg_price': 149.5
            }
        )
        
        assert updated_order.status == 'partially_filled'
        assert updated_order.filled_quantity == 50
        assert order_id in order_manager.orders
        
        # Test complete fill
        updated_order = order_manager.update_order(
            order_id,
            {
                'status': 'filled',
                'filled_quantity': 100,
                'filled_avg_price': 149.75
            }
        )
        
        assert updated_order.status == 'filled'
        assert updated_order.filled_quantity == 100
        assert order_id in order_manager.filled_orders
        assert order_id not in order_manager.orders
    
    def test_cancel_order(self, order_manager):
        """Test order cancellation."""
        order = order_manager.create_order(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=150.0
        )
        
        order_id = order.client_order_id
        assert order_manager.cancel_order(order_id)
        assert order_id in order_manager.filled_orders
        assert order_id not in order_manager.orders
        
        # Test cancelling non-existent order
        assert not order_manager.cancel_order("nonexistent_id")
    
    def test_get_orders(self, order_manager):
        """Test retrieving orders."""
        # Create multiple orders
        orders = [
            order_manager.create_order(
                symbol="AAPL",
                side="buy",
                quantity=100,
                price=150.0
            ),
            order_manager.create_order(
                symbol="MSFT",
                side="buy",
                quantity=50,
                price=250.0
            )
        ]
        
        # Test getting active orders
        active_orders = order_manager.get_active_orders()
        assert len(active_orders) == 2
        
        # Test filtering by symbol
        aapl_orders = order_manager.get_active_orders(symbol="AAPL")
        assert len(aapl_orders) == 1
        assert list(aapl_orders.values())[0].symbol == "AAPL"
        
        # Complete one order
        order_manager.update_order(
            orders[0].client_order_id,
            {
                'status': 'filled',
                'filled_quantity': 100,
                'filled_avg_price': 150.0
            }
        )
        
        # Test getting filled orders
        filled_orders = order_manager.get_filled_orders()
        assert len(filled_orders) == 1
        assert list(filled_orders.values())[0].symbol == "AAPL" 