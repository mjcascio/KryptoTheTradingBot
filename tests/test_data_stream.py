"""Unit tests for the market data streaming module."""

import pytest
import asyncio
import aiohttp
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from market.data_stream import MarketDataStream, MarketData, DataStreamError

@pytest.fixture
def market_stream():
    """Create a market stream instance for testing."""
    stream = MarketDataStream()
    yield stream
    # Cleanup
    asyncio.run(stream.stop())

@pytest.fixture
def mock_websocket():
    """Create a mock websocket for testing."""
    mock_ws = AsyncMock()
    mock_ws.__aenter__.return_value = mock_ws
    mock_ws.__aexit__.return_value = None
    return mock_ws

@pytest.mark.asyncio
async def test_start_stop():
    """Test starting and stopping the market stream."""
    stream = MarketDataStream()
    assert not stream.running
    
    await stream.start()
    assert stream.running
    assert stream.session is not None
    assert len(stream.tasks) == 1
    
    await stream.stop()
    assert not stream.running
    assert len(stream.tasks) == 0

@pytest.mark.asyncio
async def test_subscribe_unsubscribe():
    """Test subscribing and unsubscribing to market data."""
    stream = MarketDataStream()
    
    async def callback(data: MarketData):
        pass
    
    await stream.subscribe("BTC/USD", callback)
    assert "BTC/USD" in stream.callbacks
    assert len(stream.tasks) == 2  # Processing task + stream task
    
    await stream.unsubscribe("BTC/USD")
    assert "BTC/USD" not in stream.callbacks

@pytest.mark.asyncio
async def test_alpaca_data_processing(mock_websocket):
    """Test processing Alpaca market data."""
    stream = MarketDataStream()
    received_data = None
    
    async def callback(data: MarketData):
        nonlocal received_data
        received_data = data
    
    # Mock websocket message
    mock_msg = Mock()
    mock_msg.type = aiohttp.WSMsgType.TEXT
    mock_msg.data = '{"t": 1625097600000, "p": 35000.0, "v": 1.5, "b": 34999.0, "a": 35001.0}'
    mock_websocket.__aiter__.return_value = [mock_msg]
    
    with patch('aiohttp.ClientSession.ws_connect', return_value=mock_websocket):
        await stream.subscribe("BTC/USD", callback, source="alpaca")
        await asyncio.sleep(0.1)  # Allow time for processing
        
        assert received_data is not None
        assert received_data.symbol == "BTC/USD"
        assert received_data.price == 35000.0
        assert received_data.volume == 1.5

@pytest.mark.asyncio
async def test_metatrader_data_processing(mock_websocket):
    """Test processing MetaTrader market data."""
    stream = MarketDataStream()
    received_data = None
    
    async def callback(data: MarketData):
        nonlocal received_data
        received_data = data
    
    # Mock websocket message
    mock_msg = Mock()
    mock_msg.type = aiohttp.WSMsgType.TEXT
    mock_msg.data = '{"price": 35000.0, "volume": 1.5, "bid": 34999.0, "ask": 35001.0, "high": 35100.0, "low": 34900.0}'
    mock_websocket.__aiter__.return_value = [mock_msg]
    
    with patch('aiohttp.ClientSession.ws_connect', return_value=mock_websocket):
        await stream.subscribe("BTC/USD", callback, source="metatrader")
        await asyncio.sleep(0.1)  # Allow time for processing
        
        assert received_data is not None
        assert received_data.symbol == "BTC/USD"
        assert received_data.price == 35000.0
        assert received_data.high == 35100.0
        assert received_data.low == 34900.0

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in market data streaming."""
    stream = MarketDataStream()
    error_received = False
    
    async def callback(data: MarketData):
        pass
    
    # Test unknown source
    with pytest.raises(DataStreamError):
        await stream.subscribe("BTC/USD", callback, source="unknown")
    
    # Test connection error
    with patch('aiohttp.ClientSession.ws_connect', side_effect=aiohttp.ClientError):
        await stream.subscribe("BTC/USD", callback)
        await asyncio.sleep(0.1)  # Allow time for error handling
        
        # Should not raise exception but log error and retry
        assert stream.running

@pytest.mark.asyncio
async def test_queue_processing():
    """Test market data queue processing."""
    stream = MarketDataStream()
    processed_data = []
    
    async def callback(data: MarketData):
        processed_data.append(data)
    
    await stream.start()
    
    # Add test data to queue
    test_data = MarketData(
        symbol="BTC/USD",
        timestamp=datetime.now(),
        price=35000.0,
        volume=1.5
    )
    
    await stream._queue.put(test_data)
    await asyncio.sleep(0.1)  # Allow time for processing
    
    assert len(processed_data) == 1
    assert processed_data[0].symbol == "BTC/USD"
    assert processed_data[0].price == 35000.0

@pytest.mark.asyncio
async def test_last_data_storage():
    """Test storage and retrieval of last known market data."""
    stream = MarketDataStream()
    
    test_data = MarketData(
        symbol="BTC/USD",
        timestamp=datetime.now(),
        price=35000.0,
        volume=1.5
    )
    
    stream._last_data["BTC/USD"] = test_data
    
    retrieved_data = stream.get_last_data("BTC/USD")
    assert retrieved_data == test_data
    
    # Test non-existent symbol
    assert stream.get_last_data("NON/EXISTENT") is None 