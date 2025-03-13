"""Tests for Coinbase WebSocket client."""

import pytest
import json
import aiohttp
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from ..api.websocket import CoinbaseWebSocketClient
from ..models.market import MarketData, Trade
from ..models.order import OrderSide
from ..utils.exceptions import CoinbaseConnectionError, CoinbaseAuthError

@pytest.fixture
def ws_client():
    """Create test WebSocket client."""
    return CoinbaseWebSocketClient(
        api_key="test_key",
        api_secret="test_secret",
        passphrase="test_pass"
    )

@pytest.mark.asyncio
async def test_connect_and_close(ws_client):
    """Test WebSocket connection and closure."""
    mock_session = AsyncMock()
    mock_ws = AsyncMock()
    mock_session.ws_connect.return_value = mock_ws
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await ws_client.connect()
        assert ws_client._session is not None
        assert ws_client._ws is not None
        assert ws_client._running is True
        
        await ws_client.close()
        assert ws_client._session is None
        assert ws_client._ws is None
        assert ws_client._running is False

@pytest.mark.asyncio
async def test_subscribe(ws_client):
    """Test channel subscription."""
    mock_session = AsyncMock()
    mock_ws = AsyncMock()
    mock_session.ws_connect.return_value = mock_ws
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await ws_client.connect()
        
        channels = ["ticker", "matches"]
        products = ["BTC-USD"]
        
        await ws_client.subscribe(channels, products)
        
        # Verify subscription message
        subscription = json.loads(mock_ws.send_json.call_args[0][0])
        assert subscription["type"] == "subscribe"
        assert subscription["channels"] == channels
        assert subscription["product_ids"] == products
        
        await ws_client.close()

@pytest.mark.asyncio
async def test_unsubscribe(ws_client):
    """Test channel unsubscription."""
    mock_session = AsyncMock()
    mock_ws = AsyncMock()
    mock_session.ws_connect.return_value = mock_ws
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await ws_client.connect()
        
        channels = ["ticker"]
        products = ["BTC-USD"]
        
        # Subscribe first
        await ws_client.subscribe(channels, products)
        
        # Then unsubscribe
        await ws_client.unsubscribe(channels, products)
        
        # Verify unsubscription message
        unsubscription = json.loads(mock_ws.send_json.call_args[0][0])
        assert unsubscription["type"] == "unsubscribe"
        assert unsubscription["channels"] == channels
        assert unsubscription["product_ids"] == products
        
        await ws_client.close()

@pytest.mark.asyncio
async def test_handle_ticker_message(ws_client):
    """Test handling ticker messages."""
    mock_callback = AsyncMock()
    ws_client.on_ticker(mock_callback)
    
    message = {
        "type": "ticker",
        "product_id": "BTC-USD",
        "price": "50000.00",
        "best_bid": "49900.00",
        "best_ask": "50100.00",
        "volume_24h": "100.0",
        "time": "2023-01-01T00:00:00Z"
    }
    
    await ws_client._handle_message(message)
    
    mock_callback.assert_called_once()
    market_data = mock_callback.call_args[0][0]
    assert isinstance(market_data, MarketData)
    assert market_data.symbol == "BTC-USD"
    assert market_data.price == 50000.00

@pytest.mark.asyncio
async def test_handle_trade_message(ws_client):
    """Test handling trade messages."""
    mock_callback = AsyncMock()
    ws_client.on_trade(mock_callback)
    
    message = {
        "type": "match",
        "trade_id": "test-id",
        "product_id": "BTC-USD",
        "price": "50000.00",
        "size": "1.0",
        "side": "buy",
        "time": "2023-01-01T00:00:00Z"
    }
    
    await ws_client._handle_message(message)
    
    mock_callback.assert_called_once()
    trade = mock_callback.call_args[0][0]
    assert isinstance(trade, Trade)
    assert trade.symbol == "BTC-USD"
    assert trade.price == 50000.00
    assert trade.side == OrderSide.BUY

@pytest.mark.asyncio
async def test_handle_error_message(ws_client):
    """Test handling error messages."""
    message = {
        "type": "error",
        "message": "Test error"
    }
    
    with patch('logging.Logger.error') as mock_logger:
        await ws_client._handle_message(message)
        mock_logger.assert_called_once_with("WebSocket error: Test error")

@pytest.mark.asyncio
async def test_handle_heartbeat(ws_client):
    """Test handling heartbeat messages."""
    mock_callback = AsyncMock()
    ws_client.on_heartbeat(mock_callback)
    
    message = {
        "type": "heartbeat",
        "sequence": 123,
        "last_trade_id": 456,
        "product_id": "BTC-USD",
        "time": "2023-01-01T00:00:00Z"
    }
    
    await ws_client._handle_message(message)
    mock_callback.assert_called_once_with(message)

@pytest.mark.asyncio
async def test_connection_error(ws_client):
    """Test connection error handling."""
    mock_session = AsyncMock()
    mock_session.ws_connect.side_effect = aiohttp.ClientError()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(CoinbaseConnectionError):
            await ws_client.connect()

@pytest.mark.asyncio
async def test_authentication_error(ws_client):
    """Test authentication error handling."""
    # Clear credentials to trigger auth error
    ws_client.api_key = None
    ws_client.api_secret = None
    ws_client.passphrase = None
    
    with pytest.raises(CoinbaseAuthError):
        await ws_client.subscribe(["user"], ["BTC-USD"])

@pytest.mark.asyncio
async def test_reconnect(ws_client):
    """Test WebSocket reconnection."""
    mock_session = AsyncMock()
    mock_ws = AsyncMock()
    mock_session.ws_connect.return_value = mock_ws
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await ws_client.connect()
        
        # Subscribe to channels
        channels = ["ticker"]
        products = ["BTC-USD"]
        await ws_client.subscribe(channels, products)
        
        # Simulate reconnection
        await ws_client.reconnect()
        
        # Verify that we resubscribed to channels
        subscription = json.loads(mock_ws.send_json.call_args[0][0])
        assert subscription["type"] == "subscribe"
        assert subscription["channels"] == channels
        assert subscription["product_ids"] == products
        
        await ws_client.close()

@pytest.mark.asyncio
async def test_process_messages(ws_client):
    """Test message processing loop."""
    mock_session = AsyncMock()
    mock_ws = AsyncMock()
    mock_session.ws_connect.return_value = mock_ws
    
    # Set up message sequence
    messages = [
        Mock(type=aiohttp.WSMsgType.TEXT, data=json.dumps({
            "type": "ticker",
            "product_id": "BTC-USD",
            "price": "50000.00",
            "best_bid": "49900.00",
            "best_ask": "50100.00",
            "volume_24h": "100.0",
            "time": "2023-01-01T00:00:00Z"
        })),
        Mock(type=aiohttp.WSMsgType.CLOSED)
    ]
    mock_ws.receive.side_effect = messages
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await ws_client.connect()
        
        # Add ticker callback
        mock_callback = AsyncMock()
        ws_client.on_ticker(mock_callback)
        
        # Start message processing
        await ws_client._process_messages()
        
        # Verify callback was called
        mock_callback.assert_called_once()
        market_data = mock_callback.call_args[0][0]
        assert isinstance(market_data, MarketData)
        assert market_data.price == 50000.00
        
        await ws_client.close() 