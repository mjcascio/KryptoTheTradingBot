"""Tests for Coinbase models."""

import pytest
from datetime import datetime, timezone

from ..models.market import MarketData, OrderBook, Trade
from ..models.account import Account, Position
from ..models.order import Order, OrderSide, OrderType, OrderStatus

def test_market_data():
    """Test MarketData model."""
    now = datetime.now(timezone.utc)
    market_data = MarketData(
        symbol="BTC-USD",
        price=50000.0,
        bid=49900.0,
        ask=50100.0,
        volume=100.0,
        timestamp=now
    )
    
    assert market_data.symbol == "BTC-USD"
    assert market_data.price == 50000.0
    assert market_data.bid == 49900.0
    assert market_data.ask == 50100.0
    assert market_data.volume == 100.0
    assert market_data.timestamp == now

def test_order_book():
    """Test OrderBook model."""
    now = datetime.now(timezone.utc)
    order_book = OrderBook(
        symbol="BTC-USD",
        bids=[(50000.0, 1.0), (49900.0, 2.0)],
        asks=[(50100.0, 1.0), (50200.0, 2.0)],
        timestamp=now
    )
    
    assert order_book.symbol == "BTC-USD"
    assert len(order_book.bids) == 2
    assert len(order_book.asks) == 2
    assert order_book.bids[0] == (50000.0, 1.0)
    assert order_book.asks[0] == (50100.0, 1.0)
    assert order_book.timestamp == now

def test_trade():
    """Test Trade model."""
    now = datetime.now(timezone.utc)
    trade = Trade(
        id="test-id",
        symbol="BTC-USD",
        price=50000.0,
        size=1.0,
        side=OrderSide.BUY,
        timestamp=now
    )
    
    assert trade.id == "test-id"
    assert trade.symbol == "BTC-USD"
    assert trade.price == 50000.0
    assert trade.size == 1.0
    assert trade.side == OrderSide.BUY
    assert trade.timestamp == now

def test_account():
    """Test Account model."""
    account = Account(
        id="test-id",
        currency="BTC",
        balance=1.0,
        available=0.5,
        hold=0.5
    )
    
    assert account.id == "test-id"
    assert account.currency == "BTC"
    assert account.balance == 1.0
    assert account.available == 0.5
    assert account.hold == 0.5

def test_position():
    """Test Position model."""
    position = Position(
        symbol="BTC-USD",
        quantity=1.0,
        entry_price=50000.0,
        unrealized_pnl=1000.0,
        realized_pnl=500.0
    )
    
    assert position.symbol == "BTC-USD"
    assert position.quantity == 1.0
    assert position.entry_price == 50000.0
    assert position.unrealized_pnl == 1000.0
    assert position.realized_pnl == 500.0

def test_order():
    """Test Order model."""
    now = datetime.now(timezone.utc)
    order = Order(
        id="test-id",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        size=1.0,
        price=50000.0,
        status=OrderStatus.OPEN,
        created_at=now,
        filled_size=0.5,
        executed_price=50000.0,
        remaining_size=0.5,
        client_order_id="client-test-id"
    )
    
    assert order.id == "test-id"
    assert order.symbol == "BTC-USD"
    assert order.side == OrderSide.BUY
    assert order.type == OrderType.LIMIT
    assert order.size == 1.0
    assert order.price == 50000.0
    assert order.status == OrderStatus.OPEN
    assert order.created_at == now
    assert order.filled_size == 0.5
    assert order.executed_price == 50000.0
    assert order.remaining_size == 0.5
    assert order.client_order_id == "client-test-id"

def test_order_side_enum():
    """Test OrderSide enumeration."""
    assert OrderSide.BUY.value == "buy"
    assert OrderSide.SELL.value == "sell"
    assert OrderSide("buy") == OrderSide.BUY
    assert OrderSide("sell") == OrderSide.SELL

def test_order_type_enum():
    """Test OrderType enumeration."""
    assert OrderType.MARKET.value == "market"
    assert OrderType.LIMIT.value == "limit"
    assert OrderType("market") == OrderType.MARKET
    assert OrderType("limit") == OrderType.LIMIT

def test_order_status_enum():
    """Test OrderStatus enumeration."""
    assert OrderStatus.OPEN.value == "open"
    assert OrderStatus.PENDING.value == "pending"
    assert OrderStatus.ACTIVE.value == "active"
    assert OrderStatus.DONE.value == "done"
    assert OrderStatus.REJECTED.value == "rejected"
    assert OrderStatus.CANCELLED.value == "cancelled"
    
    assert OrderStatus("open") == OrderStatus.OPEN
    assert OrderStatus("pending") == OrderStatus.PENDING
    assert OrderStatus("active") == OrderStatus.ACTIVE
    assert OrderStatus("done") == OrderStatus.DONE
    assert OrderStatus("rejected") == OrderStatus.REJECTED
    assert OrderStatus("cancelled") == OrderStatus.CANCELLED

def test_position_optional_fields():
    """Test Position model with optional fields."""
    position = Position(
        symbol="BTC-USD",
        quantity=1.0,
        entry_price=50000.0
    )
    
    assert position.symbol == "BTC-USD"
    assert position.quantity == 1.0
    assert position.entry_price == 50000.0
    assert position.unrealized_pnl is None
    assert position.realized_pnl is None

def test_order_optional_fields():
    """Test Order model with optional fields."""
    now = datetime.now(timezone.utc)
    order = Order(
        id="test-id",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        size=1.0,
        price=50000.0,
        status=OrderStatus.OPEN,
        created_at=now
    )
    
    assert order.id == "test-id"
    assert order.symbol == "BTC-USD"
    assert order.side == OrderSide.BUY
    assert order.type == OrderType.LIMIT
    assert order.size == 1.0
    assert order.price == 50000.0
    assert order.status == OrderStatus.OPEN
    assert order.created_at == now
    assert order.filled_size is None
    assert order.executed_price is None
    assert order.remaining_size is None
    assert order.client_order_id is None 