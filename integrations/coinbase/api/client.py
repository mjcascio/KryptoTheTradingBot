"""Coinbase API client for the KryptoBot Trading System."""

import hmac
import hashlib
import time
import json
import base64
from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime, timezone

from ..utils.logging import setup_logging
from ..models.market import MarketData, OrderBook, Trade
from ..models.account import Account, Position
from ..models.order import Order, OrderStatus, OrderSide, OrderType, StopPrice, TrailingStop, TimeInForce
from ..utils.exceptions import (
    CoinbaseAuthError,
    CoinbaseAPIError,
    CoinbaseRateLimitError,
    AuthenticationError
)

logger = setup_logging(__name__)

class CoinbaseClient:
    """Asynchronous Coinbase Pro API client."""
    
    BASE_URL = "https://api.pro.coinbase.com"
    WS_URL = "wss://ws-feed.pro.coinbase.com"
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str,
        sandbox: bool = False
    ) -> None:
        """Initialize Coinbase client.
        
        Args:
            api_key: API key
            api_secret: API secret
            passphrase: API passphrase
            sandbox: Use sandbox environment
        """
        self.api_key = api_key
        self.api_secret = base64.b64decode(api_secret)
        self.passphrase = passphrase
        
        if sandbox:
            self.BASE_URL = "https://api-public.sandbox.pro.coinbase.com"
            self.WS_URL = "wss://ws-feed-public.sandbox.pro.coinbase.com"
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None

    async def __aenter__(self):
        """Enter async context."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.close()

    def _generate_signature(
        self,
        timestamp: str,
        method: str,
        request_path: str,
        body: str = ""
    ) -> str:
        """Generate signature for request authentication.
        
        Args:
            timestamp: Request timestamp
            method: HTTP method
            request_path: Request path
            body: Request body
            
        Returns:
            Request signature
        """
        message = f"{timestamp}{method}{request_path}{body}"
        signature = hmac.new(
            self.api_secret,
            message.encode(),
            hashlib.sha256
        )
        return base64.b64encode(signature.digest()).decode()

    def _get_auth_headers(
        self,
        method: str,
        request_path: str,
        body: str = ""
    ) -> Dict[str, str]:
        """Get authentication headers for request.
        
        Args:
            method: HTTP method
            request_path: Request path
            body: Request body
            
        Returns:
            Authentication headers
        """
        timestamp = str(int(time.time()))
        signature = self._generate_signature(timestamp, method, request_path, body)
        
        return {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

    async def connect(self) -> None:
        """Connect to Coinbase API."""
        if not self._session:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close API connection."""
        if self._session:
            await self._session.close()
            self._session = None
        
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated request to Coinbase API.
        
        Args:
            method: HTTP method
            path: API endpoint path
            params: Query parameters
            data: Request data
            
        Returns:
            API response
            
        Raises:
            CoinbaseAuthError: Authentication error
            CoinbaseAPIError: API error
            CoinbaseRateLimitError: Rate limit exceeded
        """
        if not self._session:
            await self.connect()
        
        url = f"{self.BASE_URL}{path}"
        body = json.dumps(data) if data else ""
        headers = self._get_auth_headers(method, path, body)
        
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data
            ) as response:
                if response.status == 429:
                    raise CoinbaseRateLimitError("Rate limit exceeded")
                
                if response.status == 401:
                    raise CoinbaseAuthError("Invalid API credentials")
                
                if response.status >= 400:
                    error = await response.text()
                    raise CoinbaseAPIError(f"API error: {error}")
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise CoinbaseAPIError(f"Request failed: {str(e)}")

    async def get_accounts(self) -> List[Account]:
        """Get trading accounts.
        
        Returns:
            List of trading accounts
        """
        response = await self._request("GET", "/accounts")
        return [
            Account(
                id=acc["id"],
                currency=acc["currency"],
                balance=float(acc["balance"]),
                available=float(acc["available"]),
                hold=float(acc["hold"])
            )
            for acc in response
        ]

    async def get_positions(self) -> List[Position]:
        """Get open positions.
        
        Returns:
            List of open positions
        """
        accounts = await self.get_accounts()
        return [
            Position(
                symbol=acc.currency,
                quantity=acc.balance,
                entry_price=0.0  # Coinbase doesn't provide entry price
            )
            for acc in accounts
            if acc.balance > 0
        ]

    async def get_order_book(self, product_id: str) -> OrderBook:
        """Get order book for a product.
        
        Args:
            product_id: Product ID (e.g., "BTC-USD")
            
        Returns:
            Order book
        """
        response = await self._request("GET", f"/products/{product_id}/book", params={"level": 2})
        return OrderBook(
            symbol=product_id,
            bids=[(float(p), float(s)) for p, s, _ in response["bids"]],
            asks=[(float(p), float(s)) for p, s, _ in response["asks"]],
            timestamp=datetime.now(timezone.utc)
        )

    async def get_trades(self, product_id: str, limit: int = 100) -> List[Trade]:
        """Get recent trades for a product.
        
        Args:
            product_id: Product ID (e.g., "BTC-USD")
            limit: Number of trades to return
            
        Returns:
            List of trades
        """
        response = await self._request(
            "GET",
            f"/products/{product_id}/trades",
            params={"limit": limit}
        )
        return [
            Trade(
                id=trade["trade_id"],
                symbol=product_id,
                price=float(trade["price"]),
                size=float(trade["size"]),
                side=OrderSide.BUY if trade["side"] == "buy" else OrderSide.SELL,
                timestamp=datetime.fromisoformat(trade["time"].replace("Z", "+00:00"))
            )
            for trade in response
        ]

    async def place_market_order(self, symbol: str, side: OrderSide, size: float) -> Order:
        """Place market order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            size: Order size
            
        Returns:
            Order information
        """
        order = Order(
            id="",  # Will be set by exchange
            symbol=symbol,
            side=side,
            type=OrderType.MARKET,
            size=size,
            price=0,  # Market orders don't specify price
            status=None,  # Will be set by exchange
            created_at=None  # Will be set by exchange
        )
        response = await self._request("POST", "/orders", order.to_api_params())
        return Order.from_api_response(response)

    async def place_limit_order(
        self, 
        symbol: str, 
        side: OrderSide, 
        size: float, 
        price: float,
        time_in_force: TimeInForce = TimeInForce.GTC,
        post_only: bool = False
    ) -> Order:
        """Place limit order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            size: Order size
            price: Limit price
            time_in_force: Time in force
            post_only: Post only flag
            
        Returns:
            Order information
        """
        order = Order(
            id="",
            symbol=symbol,
            side=side,
            type=OrderType.LIMIT,
            size=size,
            price=price,
            status=None,
            created_at=None,
            time_in_force=time_in_force,
            post_only=post_only
        )
        response = await self._request("POST", "/orders", order.to_api_params())
        return Order.from_api_response(response)

    async def place_stop_order(
        self, 
        symbol: str, 
        side: OrderSide, 
        size: float,
        stop_price: float
    ) -> Order:
        """Place stop order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            size: Order size
            stop_price: Stop price
            
        Returns:
            Order information
        """
        order = Order(
            id="",
            symbol=symbol,
            side=side,
            type=OrderType.STOP,
            size=size,
            price=0,
            status=None,
            created_at=None,
            stop_price=StopPrice(stop_price=stop_price)
        )
        response = await self._request("POST", "/orders", order.to_api_params())
        return Order.from_api_response(response)

    async def place_stop_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        size: float,
        stop_price: float,
        limit_price: float
    ) -> Order:
        """Place stop-limit order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            size: Order size
            stop_price: Stop price
            limit_price: Limit price
            
        Returns:
            Order information
        """
        order = Order(
            id="",
            symbol=symbol,
            side=side,
            type=OrderType.STOP_LIMIT,
            size=size,
            price=limit_price,
            status=None,
            created_at=None,
            stop_price=StopPrice(stop_price=stop_price, limit_price=limit_price)
        )
        response = await self._request("POST", "/orders", order.to_api_params())
        return Order.from_api_response(response)

    async def place_trailing_stop_order(
        self,
        symbol: str,
        side: OrderSide,
        size: float,
        trail_value: float,
        trail_type: str = "percentage"
    ) -> Order:
        """Place trailing stop order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            size: Order size
            trail_value: Trail value
            trail_type: Trail type (percentage or value)
            
        Returns:
            Order information
        """
        order = Order(
            id="",
            symbol=symbol,
            side=side,
            type=OrderType.TRAILING_STOP,
            size=size,
            price=0,
            status=None,
            created_at=None,
            trailing_stop=TrailingStop(trail_value=trail_value, trail_type=trail_type)
        )
        response = await self._request("POST", "/orders", order.to_api_params())
        return Order.from_api_response(response)

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if order was cancelled
        """
        try:
            await self._request("DELETE", f"/orders/{order_id}")
            return True
        except CoinbaseAPIError:
            return False

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details or None if not found
        """
        try:
            response = await self._request("GET", f"/orders/{order_id}")
            return Order.from_api_response(response)
        except CoinbaseAPIError:
            return None

    async def get_product_ticker(self, product_id: str) -> MarketData:
        """Get current ticker for a product.
        
        Args:
            product_id: Product ID (e.g., "BTC-USD")
            
        Returns:
            Market data
        """
        response = await self._request("GET", f"/products/{product_id}/ticker")
        return MarketData(
            symbol=product_id,
            price=float(response["price"]),
            bid=float(response["bid"]),
            ask=float(response["ask"]),
            volume=float(response["volume"]),
            timestamp=datetime.fromisoformat(response["time"].replace("Z", "+00:00"))
        )

    async def get_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of orders
        """
        path = f"/orders?product_id={symbol}" if symbol else "/orders"
        response = await self._request("GET", path)
        return [Order.from_api_response(order) for order in response] 