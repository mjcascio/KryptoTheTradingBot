"""Tests for order functionality."""

import pytest
from datetime import datetime, timezone
from ..models.order import (
    Order, OrderSide, OrderType, OrderStatus, 
    StopPrice, TrailingStop, TimeInForce
)
from ..api.client import CoinbaseClient
from ..utils.exceptions import CoinbaseAPIError

@pytest.fixture
def client():
    """Create test client."""
    return CoinbaseClient("test_key", "test_secret", sandbox=True)

@pytest.mark.asyncio
async def test_market_order(client):
    """Test market order placement."""
    order = await client.place_market_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01
    )
    assert order.type == OrderType.MARKET
    assert order.side == OrderSide.BUY
    assert order.size == 0.01
    assert order.symbol == "BTC-USD"

@pytest.mark.asyncio
async def test_limit_order(client):
    """Test limit order placement."""
    order = await client.place_limit_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01,
        price=50000.0,
        time_in_force=TimeInForce.GTC,
        post_only=True
    )
    assert order.type == OrderType.LIMIT
    assert order.side == OrderSide.BUY
    assert order.size == 0.01
    assert order.price == 50000.0
    assert order.time_in_force == TimeInForce.GTC
    assert order.post_only is True

@pytest.mark.asyncio
async def test_stop_order(client):
    """Test stop order placement."""
    order = await client.place_stop_order(
        symbol="BTC-USD",
        side=OrderSide.SELL,
        size=0.01,
        stop_price=45000.0
    )
    assert order.type == OrderType.STOP
    assert order.side == OrderSide.SELL
    assert order.size == 0.01
    assert order.stop_price.stop_price == 45000.0
    assert order.stop_price.limit_price is None

@pytest.mark.asyncio
async def test_stop_limit_order(client):
    """Test stop-limit order placement."""
    order = await client.place_stop_limit_order(
        symbol="BTC-USD",
        side=OrderSide.SELL,
        size=0.01,
        stop_price=45000.0,
        limit_price=44900.0
    )
    assert order.type == OrderType.STOP_LIMIT
    assert order.side == OrderSide.SELL
    assert order.size == 0.01
    assert order.stop_price.stop_price == 45000.0
    assert order.stop_price.limit_price == 44900.0
    assert order.price == 44900.0

@pytest.mark.asyncio
async def test_trailing_stop_order(client):
    """Test trailing stop order placement."""
    order = await client.place_trailing_stop_order(
        symbol="BTC-USD",
        side=OrderSide.SELL,
        size=0.01,
        trail_value=5.0,
        trail_type="percentage"
    )
    assert order.type == OrderType.TRAILING_STOP
    assert order.side == OrderSide.SELL
    assert order.size == 0.01
    assert order.trailing_stop.trail_value == 5.0
    assert order.trailing_stop.trail_type == "percentage"

@pytest.mark.asyncio
async def test_order_cancellation(client):
    """Test order cancellation."""
    # Place an order first
    order = await client.place_limit_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01,
        price=50000.0
    )
    
    # Cancel the order
    success = await client.cancel_order(order.id)
    assert success is True
    
    # Verify order is cancelled
    updated_order = await client.get_order(order.id)
    assert updated_order.status == OrderStatus.CANCELLED

@pytest.mark.asyncio
async def test_get_orders(client):
    """Test getting orders."""
    # Place multiple orders
    await client.place_limit_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01,
        price=50000.0
    )
    await client.place_stop_order(
        symbol="BTC-USD",
        side=OrderSide.SELL,
        size=0.01,
        stop_price=45000.0
    )
    
    # Get all orders
    orders = await client.get_orders()
    assert len(orders) >= 2
    
    # Get orders for specific symbol
    btc_orders = await client.get_orders(symbol="BTC-USD")
    assert all(order.symbol == "BTC-USD" for order in btc_orders)

@pytest.mark.asyncio
async def test_order_status_updates(client):
    """Test order status updates."""
    # Place a limit order
    order = await client.place_limit_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01,
        price=50000.0
    )
    
    # Check initial status
    assert order.status in [OrderStatus.OPEN, OrderStatus.PENDING]
    
    # Get updated order status
    updated_order = await client.get_order(order.id)
    assert updated_order.status in [
        OrderStatus.OPEN,
        OrderStatus.PENDING,
        OrderStatus.DONE,
        OrderStatus.REJECTED
    ]

@pytest.mark.asyncio
async def test_time_in_force_options(client):
    """Test time in force options."""
    # Test GTC order
    gtc_order = await client.place_limit_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01,
        price=50000.0,
        time_in_force=TimeInForce.GTC
    )
    assert gtc_order.time_in_force == TimeInForce.GTC
    
    # Test IOC order
    ioc_order = await client.place_limit_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01,
        price=50000.0,
        time_in_force=TimeInForce.IOC
    )
    assert ioc_order.time_in_force == TimeInForce.IOC
    
    # Test FOK order
    fok_order = await client.place_limit_order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        size=0.01,
        price=50000.0,
        time_in_force=TimeInForce.FOK
    )
    assert fok_order.time_in_force == TimeInForce.FOK

@pytest.mark.asyncio
async def test_order_validation(client):
    """Test order validation."""
    # Test invalid size
    with pytest.raises(ValueError):
        await client.place_market_order(
            symbol="BTC-USD",
            side=OrderSide.BUY,
            size=0
        )
    
    # Test invalid price
    with pytest.raises(ValueError):
        await client.place_limit_order(
            symbol="BTC-USD",
            side=OrderSide.BUY,
            size=0.01,
            price=-1
        )
    
    # Test invalid stop price
    with pytest.raises(ValueError):
        await client.place_stop_order(
            symbol="BTC-USD",
            side=OrderSide.SELL,
            size=0.01,
            stop_price=-1
        )
    
    # Test invalid trail value
    with pytest.raises(ValueError):
        await client.place_trailing_stop_order(
            symbol="BTC-USD",
            side=OrderSide.SELL,
            size=0.01,
            trail_value=-1
        ) 