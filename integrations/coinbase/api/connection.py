"""WebSocket connection manager with exponential backoff and health monitoring."""

import asyncio
import time
import random
from typing import Optional, Callable, Awaitable, Dict, Any
import aiohttp
from ..utils.logging import setup_logging

logger = setup_logging(__name__)

class ConnectionManager:
    """WebSocket connection manager with automatic reconnection."""
    
    def __init__(
        self,
        url: str,
        on_connect: Optional[Callable[[], Awaitable[None]]] = None,
        on_disconnect: Optional[Callable[[], Awaitable[None]]] = None,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        jitter: float = 0.1
    ) -> None:
        """Initialize connection manager.
        
        Args:
            url: WebSocket URL
            on_connect: Callback when connection is established
            on_disconnect: Callback when connection is lost
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
            jitter: Random jitter factor (0-1)
        """
        self.url = url
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.jitter = jitter
        
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._current_backoff = initial_backoff
        self._last_message_time = 0.0
        self._running = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    @property
    def connected(self) -> bool:
        """Check if WebSocket is connected.
        
        Returns:
            True if connected
        """
        return self._ws is not None and not self._ws.closed
    
    async def connect(self) -> None:
        """Connect to WebSocket with automatic reconnection."""
        if self._running:
            return
        
        self._running = True
        await self._connect()
        
        # Start heartbeat monitoring
        self._heartbeat_task = asyncio.create_task(self._monitor_heartbeat())
    
    async def _connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            self._ws = await self._session.ws_connect(self.url)
            logger.info("WebSocket connected")
            
            # Reset backoff on successful connection
            self._current_backoff = self.initial_backoff
            
            if self.on_connect:
                await self.on_connect()
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            await self._handle_disconnect()
    
    async def _handle_disconnect(self) -> None:
        """Handle connection loss and initiate reconnection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        if self.on_disconnect:
            await self.on_disconnect()
        
        if self._running:
            # Calculate next backoff with jitter
            jitter_amount = random.uniform(-self.jitter, self.jitter)
            backoff = self._current_backoff * (1 + jitter_amount)
            
            logger.info(f"Reconnecting in {backoff:.1f} seconds...")
            await asyncio.sleep(backoff)
            
            # Increase backoff for next attempt
            self._current_backoff = min(
                self._current_backoff * 2,
                self.max_backoff
            )
            
            # Attempt reconnection
            self._reconnect_task = asyncio.create_task(self._connect())
    
    async def _monitor_heartbeat(self) -> None:
        """Monitor connection health using message timestamps."""
        while self._running:
            await asyncio.sleep(1)
            
            if self.connected:
                current_time = time.time()
                if current_time - self._last_message_time > 30:  # No messages for 30s
                    logger.warning("No messages received, reconnecting...")
                    await self._handle_disconnect()
    
    async def send(self, message: Dict[str, Any]) -> None:
        """Send message through WebSocket.
        
        Args:
            message: Message to send
            
        Raises:
            ConnectionError: If not connected
        """
        if not self.connected:
            raise ConnectionError("WebSocket not connected")
        
        await self._ws.send_json(message)
    
    async def receive(self) -> Optional[Dict[str, Any]]:
        """Receive message from WebSocket.
        
        Returns:
            Received message or None if connection closed
            
        Raises:
            ConnectionError: If not connected
        """
        if not self.connected:
            raise ConnectionError("WebSocket not connected")
        
        try:
            msg = await self._ws.receive()
            
            if msg.type == aiohttp.WSMsgType.TEXT:
                self._last_message_time = time.time()
                return msg.json()
            
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                await self._handle_disconnect()
                return None
            
        except Exception as e:
            logger.error(f"Error receiving message: {str(e)}")
            await self._handle_disconnect()
            return None
    
    async def close(self) -> None:
        """Close WebSocket connection."""
        self._running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("WebSocket connection closed") 