"""WebSocket client for real-time market data from Coinbase."""

import asyncio
import json
import time
import hmac
import hashlib
import base64
from typing import Dict, Any, List, Optional, Callable, Set
import aiohttp
from datetime import datetime, timezone

from ..utils.logging import setup_logging
from ..models.market import MarketData, Trade
from ..models.order import OrderSide
from ..utils.exceptions import CoinbaseConnectionError, CoinbaseAuthError

logger = setup_logging(__name__)

class CoinbaseWebSocketClient:
    """Asynchronous WebSocket client for Coinbase Pro."""
    
    WS_URL = "wss://ws-feed.pro.coinbase.com"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        passphrase: Optional[str] = None,
        sandbox: bool = False
    ) -> None:
        """Initialize WebSocket client.
        
        Args:
            api_key: Optional API key for authenticated channels
            api_secret: Optional API secret for authenticated channels
            passphrase: Optional API passphrase for authenticated channels
            sandbox: Use sandbox environment
        """
        self.api_key = api_key
        self.api_secret = api_secret.encode() if api_secret else None
        self.passphrase = passphrase
        
        if sandbox:
            self.WS_URL = "wss://ws-feed-public.sandbox.pro.coinbase.com"
        
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._subscribed_channels: Set[str] = set()
        self._subscribed_products: Set[str] = set()
        self._running = False
        self._callbacks: Dict[str, List[Callable]] = {
            "ticker": [],
            "heartbeat": [],
            "level2": [],
            "matches": [],
            "user": []
        }
        self._last_heartbeat = time.time()
        self._heartbeat_interval = 30  # seconds
    
    async def connect(self) -> None:
        """Connect to WebSocket and start processing messages."""
        if self._running:
            return
        
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        try:
            self._ws = await self._session.ws_connect(self.WS_URL)
            self._running = True
            logger.info("Connected to Coinbase WebSocket")
            
            # Start message processing and heartbeat checking
            asyncio.create_task(self._process_messages())
            asyncio.create_task(self._check_heartbeat())
            
        except aiohttp.ClientError as e:
            raise CoinbaseConnectionError(f"Failed to connect to WebSocket: {str(e)}")
    
    async def close(self) -> None:
        """Close WebSocket connection."""
        self._running = False
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self._subscribed_channels.clear()
        self._subscribed_products.clear()
        logger.info("Disconnected from Coinbase WebSocket")
    
    async def _process_messages(self) -> None:
        """Process incoming WebSocket messages."""
        if not self._ws:
            return
        
        while self._running:
            try:
                msg = await self._ws.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_message(data)
                
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("WebSocket connection closed")
                    break
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg.data}")
                    break
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                if not self._running:
                    break
                await asyncio.sleep(1)  # Prevent tight loop on errors
    
    async def _check_heartbeat(self) -> None:
        """Check for heartbeat messages and reconnect if needed."""
        while self._running:
            await asyncio.sleep(5)
            
            current_time = time.time()
            if current_time - self._last_heartbeat > self._heartbeat_interval:
                logger.warning("No heartbeat received, reconnecting...")
                await self.reconnect()
    
    async def reconnect(self) -> None:
        """Reconnect to WebSocket and resubscribe to channels."""
        # Save current subscriptions
        channels = list(self._subscribed_channels)
        products = list(self._subscribed_products)
        
        # Close current connection
        await self.close()
        
        # Reconnect
        await asyncio.sleep(1)  # Wait before reconnecting
        await self.connect()
        
        # Resubscribe
        if channels and products:
            await self.subscribe(channels, products)
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message.
        
        Args:
            message: Message data
        """
        msg_type = message.get("type")
        
        if msg_type == "error":
            logger.error(f"WebSocket error: {message.get('message')}")
            return
        
        if msg_type == "heartbeat":
            self._last_heartbeat = time.time()
            for callback in self._callbacks["heartbeat"]:
                await callback(message)
            return
        
        if msg_type == "ticker":
            # Create MarketData object
            market_data = MarketData(
                symbol=message.get("product_id", ""),
                price=float(message.get("price", 0)),
                bid=float(message.get("best_bid", 0)),
                ask=float(message.get("best_ask", 0)),
                volume=float(message.get("volume_24h", 0)),
                timestamp=datetime.fromisoformat(message.get("time", "").replace("Z", "+00:00"))
            )
            
            # Call ticker callbacks
            for callback in self._callbacks["ticker"]:
                await callback(market_data)
        
        elif msg_type == "match" or msg_type == "last_match":
            # Create Trade object
            trade = Trade(
                id=message.get("trade_id", ""),
                symbol=message.get("product_id", ""),
                price=float(message.get("price", 0)),
                size=float(message.get("size", 0)),
                side=OrderSide.BUY if message.get("side") == "buy" else OrderSide.SELL,
                timestamp=datetime.fromisoformat(message.get("time", "").replace("Z", "+00:00"))
            )
            
            # Call matches callbacks
            for callback in self._callbacks["matches"]:
                await callback(trade)
        
        elif msg_type == "l2update":
            # Call level2 callbacks
            for callback in self._callbacks["level2"]:
                await callback(message)
        
        elif msg_type in ["received", "open", "done", "match", "change"]:
            # Call user callbacks for order updates
            for callback in self._callbacks["user"]:
                await callback(message)
    
    def _get_auth_signature(self, timestamp: str, channel: str) -> Dict[str, Any]:
        """Generate authentication signature for WebSocket.
        
        Args:
            timestamp: Current timestamp
            channel: Channel to subscribe to
            
        Returns:
            Authentication parameters
        """
        if not all([self.api_key, self.api_secret, self.passphrase]):
            raise CoinbaseAuthError("API credentials required for authenticated channels")
        
        message = f"{timestamp}GET/users/self/verify"
        signature = hmac.new(
            self.api_secret,
            message.encode(),
            hashlib.sha256
        )
        signature_b64 = base64.b64encode(signature.digest()).decode()
        
        return {
            "signature": signature_b64,
            "key": self.api_key,
            "passphrase": self.passphrase,
            "timestamp": timestamp
        }
    
    async def subscribe(
        self,
        channels: List[str],
        product_ids: List[str]
    ) -> None:
        """Subscribe to WebSocket channels.
        
        Args:
            channels: List of channels to subscribe to
                (ticker, heartbeat, level2, matches, user)
            product_ids: List of product IDs (e.g., "BTC-USD")
            
        Raises:
            CoinbaseConnectionError: If not connected
            CoinbaseAuthError: If authentication fails
        """
        if not self._ws or not self._running:
            await self.connect()
        
        # Update subscribed channels and products
        self._subscribed_channels.update(channels)
        self._subscribed_products.update(product_ids)
        
        # Prepare subscription message
        subscription = {
            "type": "subscribe",
            "product_ids": list(self._subscribed_products),
            "channels": list(self._subscribed_channels)
        }
        
        # Add authentication if user channel is requested
        if "user" in channels and self.api_key:
            timestamp = str(int(time.time()))
            auth = self._get_auth_signature(timestamp, "user")
            subscription.update(auth)
        
        # Send subscription request
        await self._ws.send_json(subscription)
        logger.info(f"Subscribed to channels: {channels} for products: {product_ids}")
    
    async def unsubscribe(
        self,
        channels: List[str],
        product_ids: List[str]
    ) -> None:
        """Unsubscribe from WebSocket channels.
        
        Args:
            channels: List of channels to unsubscribe from
            product_ids: List of product IDs
            
        Raises:
            CoinbaseConnectionError: If not connected
        """
        if not self._ws or not self._running:
            raise CoinbaseConnectionError("Not connected to WebSocket")
        
        # Update subscribed channels and products
        for channel in channels:
            self._subscribed_channels.discard(channel)
        
        for product_id in product_ids:
            self._subscribed_products.discard(product_id)
        
        # Prepare unsubscription message
        unsubscription = {
            "type": "unsubscribe",
            "product_ids": product_ids,
            "channels": channels
        }
        
        # Send unsubscription request
        await self._ws.send_json(unsubscription)
        logger.info(f"Unsubscribed from channels: {channels} for products: {product_ids}")
    
    def on_ticker(self, callback: Callable[[MarketData], Any]) -> None:
        """Register callback for ticker updates.
        
        Args:
            callback: Async function to call with MarketData
        """
        self._callbacks["ticker"].append(callback)
    
    def on_trade(self, callback: Callable[[Trade], Any]) -> None:
        """Register callback for trade updates.
        
        Args:
            callback: Async function to call with Trade
        """
        self._callbacks["matches"].append(callback)
    
    def on_level2(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Register callback for order book updates.
        
        Args:
            callback: Async function to call with order book update
        """
        self._callbacks["level2"].append(callback)
    
    def on_user(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Register callback for user updates (orders, fills).
        
        Args:
            callback: Async function to call with user update
        """
        self._callbacks["user"].append(callback)
    
    def on_heartbeat(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Register callback for heartbeat messages.
        
        Args:
            callback: Async function to call with heartbeat message
        """
        self._callbacks["heartbeat"].append(callback) 