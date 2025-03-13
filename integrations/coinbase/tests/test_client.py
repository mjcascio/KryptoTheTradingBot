"""Tests for Coinbase API client."""

import pytest
import aiohttp
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from ..api.client import CoinbaseClient
from ..models.market import MarketData, OrderBook, Trade
from ..models.account import Account, Position
from ..models.order import Order, OrderSide, OrderType, OrderStatus
from ..utils.exceptions import CoinbaseAuthError, CoinbaseAPIError, CoinbaseRateLimitError

@pytest.fixture
def client():
    """Create test client."""
    return CoinbaseClient(
        api_key="test_key",
        api_secret="test_secret",
        passphrase="test_pass"
    )

@pytest.mark.asyncio
async def test_connect_and_close(client):
    """Test client connection and closure."""
    assert client._session is None
    await client.connect()
    assert isinstance(client._session, aiohttp.ClientSession)
    await client.close()
    assert client._session is None

@pytest.mark.asyncio
async def test_get_accounts(client):
    """Test getting account information."""
    mock_response = [
        {
            "id": "test-id",
            "currency": "BTC",
            "balance": "1.0",
            "available": "0.5",
            "hold": "0.5"
        }
    ]
    
    with patch.object(client, '_request', return_value=mock_response):
        accounts = await client.get_accounts()
        assert len(accounts) == 1
        assert isinstance(accounts[0], Account)
        assert accounts[0].currency == "BTC"
        assert accounts[0].balance == 1.0

@pytest.mark.asyncio
async def test_get_positions(client):
    """Test getting positions."""
    mock_accounts = [
        {
            "id": "test-id",
            "currency": "BTC",
            "balance": "1.0",
            "available": "0.5",
            "hold": "0.5"
        }
    ]
    
    with patch.object(client, '_request', return_value=mock_accounts):
        positions = await client.get_positions()
        assert len(positions) == 1
        assert isinstance(positions[0], Position)
        assert positions[0].symbol == "BTC"
        assert positions[0].quantity == 1.0

@pytest.mark.asyncio
async def test_get_order_book(client):
    """Test getting order book."""
    mock_response = {
        "bids": [["50000.00", "1.0", "test-id"]],
        "asks": [["50100.00", "0.5", "test-id"]]
    }
    
    with patch.object(client, '_request', return_value=mock_response):
        order_book = await client.get_order_book("BTC-USD")
        assert isinstance(order_book, OrderBook)
        assert len(order_book.bids) == 1
        assert len(order_book.asks) == 1
        assert order_book.bids[0][0] == 50000.00
        assert order_book.asks[0][0] == 50100.00

@pytest.mark.asyncio
async def test_get_trades(client):
    """Test getting trades."""
    mock_response = [
        {
            "trade_id": "test-id",
            "product_id": "BTC-USD",
            "price": "50000.00",
            "size": "1.0",
            "side": "buy",
            "time": "2023-01-01T00:00:00Z"
        }
    ]
    
    with patch.object(client, '_request', return_value=mock_response):
        trades = await client.get_trades("BTC-USD")
        assert len(trades) == 1
        assert isinstance(trades[0], Trade)
        assert trades[0].price == 50000.00
        assert trades[0].size == 1.0
        assert trades[0].side == OrderSide.BUY

@pytest.mark.asyncio
async def test_place_order(client):
    """Test placing orders."""
    mock_response = {
        "id": "test-id",
        "product_id": "BTC-USD",
        "side": "buy",
        "type": "limit",
        "size": "1.0",
        "price": "50000.00",
        "status": "pending",
        "created_at": "2023-01-01T00:00:00Z"
    }
    
    with patch.object(client, '_request', return_value=mock_response):
        order = await client.place_order(
            product_id="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            size=1.0,
            price=50000.00
        )
        assert isinstance(order, Order)
        assert order.symbol == "BTC-USD"
        assert order.side == OrderSide.BUY
        assert order.type == OrderType.LIMIT
        assert order.size == 1.0
        assert order.price == 50000.00

@pytest.mark.asyncio
async def test_cancel_order(client):
    """Test canceling orders."""
    with patch.object(client, '_request', return_value=None):
        result = await client.cancel_order("test-id")
        assert result is True

@pytest.mark.asyncio
async def test_get_product_ticker(client):
    """Test getting product ticker."""
    mock_response = {
        "product_id": "BTC-USD",
        "price": "50000.00",
        "bid": "49900.00",
        "ask": "50100.00",
        "volume": "100.0",
        "time": "2023-01-01T00:00:00Z"
    }
    
    with patch.object(client, '_request', return_value=mock_response):
        ticker = await client.get_product_ticker("BTC-USD")
        assert isinstance(ticker, MarketData)
        assert ticker.symbol == "BTC-USD"
        assert ticker.price == 50000.00
        assert ticker.bid == 49900.00
        assert ticker.ask == 50100.00
        assert ticker.volume == 100.0

@pytest.mark.asyncio
async def test_authentication_error(client):
    """Test authentication error handling."""
    async def mock_request(*args, **kwargs):
        raise CoinbaseAuthError("Invalid API credentials")
    
    with patch.object(client, '_request', side_effect=mock_request):
        with pytest.raises(CoinbaseAuthError):
            await client.get_accounts()

@pytest.mark.asyncio
async def test_rate_limit_error(client):
    """Test rate limit error handling."""
    async def mock_request(*args, **kwargs):
        raise CoinbaseRateLimitError("Rate limit exceeded")
    
    with patch.object(client, '_request', side_effect=mock_request):
        with pytest.raises(CoinbaseRateLimitError):
            await client.get_accounts()

@pytest.mark.asyncio
async def test_api_error(client):
    """Test API error handling."""
    async def mock_request(*args, **kwargs):
        raise CoinbaseAPIError("API error")
    
    with patch.object(client, '_request', side_effect=mock_request):
        with pytest.raises(CoinbaseAPIError):
            await client.get_accounts()

@pytest.mark.asyncio
async def test_invalid_order_parameters(client):
    """Test invalid order parameter handling."""
    with pytest.raises(ValueError):
        await client.place_order(
            product_id="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            size=1.0
        )  # Missing price for limit order 