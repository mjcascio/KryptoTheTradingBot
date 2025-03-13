"""Asynchronous market data streaming for the KryptoBot Trading System."""

import asyncio
import aiohttp
import json
import hmac
import hashlib
import time
from typing import Dict, List, Set, Any, Optional, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
import base64

from utils.logging import setup_logging
from utils.profiler import performance_monitor
from utils.secure_config import secure_config, ApiCredentials
from market.rate_limiter import rate_limiter
from market.persistence import market_store

logger = setup_logging(__name__)

@dataclass
class MarketData:
    """Container for market data."""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None

class DataStreamError(Exception):
    """Exception raised for data streaming errors."""
    pass

class MarketDataStream:
    """Asynchronous market data streaming manager."""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the market data stream.
        
        Args:
            session: Optional aiohttp session
        """
        self.session = session or aiohttp.ClientSession()
        self.running = False
        self._queue = asyncio.Queue()
        self._subscribers: Dict[str, Set[Callable[[MarketData], Awaitable[None]]]] = defaultdict(set)
        self._active_streams: Set[str] = set()
        self._last_data: Dict[str, MarketData] = {}
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._reconnect_delays: Dict[str, float] = defaultdict(lambda: 1.0)
    
    async def start(self, symbols: List[str]) -> None:
        """Start streaming market data for the specified symbols.
        
        Args:
            symbols: List of trading pair symbols
        """
        if self.running:
            logger.warning("Market data stream already running")
            return
        
        self.running = True
        logger.info(f"Starting market data stream for symbols: {symbols}")
        
        # Start processing queue
        asyncio.create_task(self._process_queue())
        
        # Start streams for each symbol
        for symbol in symbols:
            if symbol not in self._active_streams:
                self._active_streams.add(symbol)
                asyncio.create_task(self._stream_market_data(symbol))
    
    async def stop(self) -> None:
        """Stop all market data streams."""
        self.running = False
        self._active_streams.clear()
        await self.session.close()
        logger.info("Market data stream stopped")
    
    async def subscribe(self, symbol: str, callback: Callable[[MarketData], Awaitable[None]]) -> None:
        """Subscribe to market data updates for a symbol.
        
        Args:
            symbol: Trading pair symbol
            callback: Async callback function to handle market data updates
        """
        self._subscribers[symbol].add(callback)
        logger.debug(f"Added subscriber for {symbol}")
        
        # Send latest data if available
        if symbol in self._last_data:
            await callback(self._last_data[symbol])
    
    async def unsubscribe(self, symbol: str, callback: Callable[[MarketData], Awaitable[None]]) -> None:
        """Unsubscribe from market data updates for a symbol.
        
        Args:
            symbol: Trading pair symbol
            callback: Callback function to remove
        """
        if symbol in self._subscribers:
            self._subscribers[symbol].discard(callback)
            logger.debug(f"Removed subscriber for {symbol}")
    
    @performance_monitor.profile_async
    async def _process_queue(self) -> None:
        """Process the market data queue."""
        while self.running:
            try:
                market_data = await self._queue.get()
                
                # Store latest data
                self._last_data[market_data.symbol] = market_data
                
                # Store in persistence layer
                await market_store.store_market_data(market_data)
                
                # Notify subscribers
                if market_data.symbol in self._subscribers:
                    for callback in self._subscribers[market_data.symbol]:
                        try:
                            await callback(market_data)
                        except Exception as e:
                            logger.error(f"Error in subscriber callback: {e}")
                
                self._queue.task_done()
            except Exception as e:
                logger.error(f"Error processing market data queue: {e}")
                await asyncio.sleep(1)
    
    @performance_monitor.profile_async
    @rate_limiter.rate_limited('market_data')
    async def _stream_market_data(self, symbol: str) -> None:
        """Stream market data for a symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        while self.running and symbol in self._active_streams:
            try:
                # Get credentials for the appropriate exchange
                credentials = await secure_config.get_credentials(symbol)
                
                # Choose appropriate streaming method based on symbol
                if symbol.endswith('USDT'):
                    await self._stream_binance(symbol)
                elif symbol.endswith('USD'):
                    await self._stream_coinbase(symbol)
                else:
                    await self._stream_alpaca(symbol)
                
                # Reset error count and delay on successful connection
                self._error_counts[symbol] = 0
                self._reconnect_delays[symbol] = 1.0
                
            except Exception as e:
                logger.error(f"Error streaming market data for {symbol}: {e}")
                
                # Increment error count and increase delay
                self._error_counts[symbol] += 1
                self._reconnect_delays[symbol] = min(300, self._reconnect_delays[symbol] * 2)
                
                # Wait before reconnecting
                await asyncio.sleep(self._reconnect_delays[symbol])
    
    @performance_monitor.profile_async
    @rate_limiter.rate_limited('binance')
    async def _stream_binance(self, symbol: str) -> None:
        """Stream market data from Binance.
        
        Args:
            symbol: Trading pair symbol
        """
        # Get credentials
        credentials = await secure_config.get_credentials('binance')
        
        # Create signature
        timestamp = str(int(time.time() * 1000))
        signature = hmac.new(
            credentials.api_secret.encode('utf-8'),
            f"timestamp={timestamp}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Connect to WebSocket
        url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@trade"
        
        async with self.session.ws_connect(url) as ws:
            # Authenticate
            await ws.send_json({
                "method": "AUTH",
                "params": [
                    credentials.api_key,
                    timestamp,
                    signature
                ]
            })
            
            # Subscribe to trade stream
            await ws.send_json({
                "method": "SUBSCRIBE",
                "params": [f"{symbol.lower()}@trade"],
                "id": 1
            })
            
            async for msg in ws:
                if not self.running:
                    break
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    if 'e' in data and data['e'] == 'trade':
                        # Create market data object
                        market_data = MarketData(
                            symbol=symbol,
                            timestamp=datetime.fromtimestamp(data['T'] / 1000),
                            price=float(data['p']),
                            volume=float(data['q']),
                            bid=None,  # Binance trade stream doesn't include bid/ask
                            ask=None
                        )
                        
                        # Add to processing queue
                        await self._queue.put(market_data)
    
    @performance_monitor.profile_async
    @rate_limiter.rate_limited('coinbase')
    async def _stream_coinbase(self, symbol: str) -> None:
        """Stream market data from Coinbase.
        
        Args:
            symbol: Trading pair symbol
        """
        # Get credentials
        credentials = await secure_config.get_credentials('coinbase')
        
        # Connect to WebSocket
        url = "wss://ws-feed.pro.coinbase.com"
        
        async with self.session.ws_connect(url) as ws:
            # Subscribe to channels
            await ws.send_json({
                "type": "subscribe",
                "product_ids": [symbol],
                "channels": ["matches", "level2"]
            })
            
            async for msg in ws:
                if not self.running:
                    break
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    if data['type'] == 'match':
                        # Create market data object
                        market_data = MarketData(
                            symbol=symbol,
                            timestamp=datetime.fromisoformat(data['time'].replace('Z', '+00:00')),
                            price=float(data['price']),
                            volume=float(data['size']),
                            bid=None,  # Will be updated from level2 data
                            ask=None
                        )
                        
                        # Add to processing queue
                        await self._queue.put(market_data)
                    
                    elif data['type'] == 'l2update':
                        # Update bid/ask in latest data
                        if symbol in self._last_data:
                            latest_data = self._last_data[symbol]
                            for change in data['changes']:
                                side, price, size = change
                                if side == 'buy':
                                    latest_data.bid = float(price)
                                elif side == 'sell':
                                    latest_data.ask = float(price)
    
    @performance_monitor.profile_async
    @rate_limiter.rate_limited('alpaca')
    async def _stream_alpaca(self, symbol: str) -> None:
        """Stream market data from Alpaca.
        
        Args:
            symbol: Trading pair symbol
        """
        # Get credentials
        credentials = await secure_config.get_credentials('alpaca')
        
        # Connect to WebSocket
        url = "wss://stream.data.alpaca.markets/v2/iex"
        
        async with self.session.ws_connect(url) as ws:
            # Authenticate
            await ws.send_json({
                "action": "auth",
                "key": credentials.api_key,
                "secret": credentials.api_secret
            })
            
            # Subscribe to trades
            await ws.send_json({
                "action": "subscribe",
                "trades": [symbol],
                "quotes": [symbol]
            })
            
            async for msg in ws:
                if not self.running:
                    break
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    if data[0]['T'] == 't':  # Trade
                        trade = data[0]
                        # Create market data object
                        market_data = MarketData(
                            symbol=symbol,
                            timestamp=datetime.fromtimestamp(trade['t'] / 1e9),
                            price=float(trade['p']),
                            volume=float(trade['s']),
                            bid=self._last_data.get(symbol, MarketData(symbol, datetime.now(), 0, 0)).bid,
                            ask=self._last_data.get(symbol, MarketData(symbol, datetime.now(), 0, 0)).ask
                        )
                        
                        # Add to processing queue
                        await self._queue.put(market_data)
                    
                    elif data[0]['T'] == 'q':  # Quote
                        quote = data[0]
                        if symbol in self._last_data:
                            self._last_data[symbol].bid = float(quote['bp'])
                            self._last_data[symbol].ask = float(quote['ap'])
    
    async def get_latest_data(self, symbol: str) -> Optional[MarketData]:
        """Get the latest market data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Latest market data or None if not available
        """
        return self._last_data.get(symbol)
    
    def get_active_symbols(self) -> Set[str]:
        """Get the set of symbols with active streams.
        
        Returns:
            Set of active symbols
        """
        return self._active_streams.copy()
    
    def get_error_count(self, symbol: str) -> int:
        """Get the error count for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Number of consecutive errors
        """
        return self._error_counts[symbol]

# Create global instance
market_stream = MarketDataStream() 