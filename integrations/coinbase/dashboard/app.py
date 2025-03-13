"""Flask dashboard application for Coinbase integration."""

import os
import asyncio
import json
from typing import Dict, Any, Set
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify
import aiohttp
from aiohttp import web
from aiohttp.web import WebSocketResponse
from ..api.client import CoinbaseClient
from ..api.websocket import CoinbaseWebSocketClient
from ..utils.logging import setup_logging

logger = setup_logging(__name__)

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Store active WebSocket connections
active_ws: Set[WebSocketResponse] = set()

def get_client() -> CoinbaseClient:
    """Get Coinbase client instance.
    
    Returns:
        Configured Coinbase client
    """
    return CoinbaseClient(
        api_key=os.getenv("COINBASE_API_KEY", ""),
        api_secret=os.getenv("COINBASE_API_SECRET", ""),
        passphrase=os.getenv("COINBASE_PASSPHRASE", ""),
        sandbox=os.getenv("COINBASE_SANDBOX", "false").lower() == "true"
    )

async def broadcast_message(message: Dict[str, Any]) -> None:
    """Broadcast message to all connected WebSocket clients.
    
    Args:
        message: Message to broadcast
    """
    if not active_ws:
        return
    
    data = json.dumps(message)
    dead_ws = set()
    
    for ws in active_ws:
        try:
            await ws.send_str(data)
        except Exception:
            dead_ws.add(ws)
    
    # Remove dead connections
    active_ws.difference_update(dead_ws)

async def handle_market_data(market_data: Dict[str, Any]) -> None:
    """Handle market data updates.
    
    Args:
        market_data: Market data update
    """
    await broadcast_message({
        "type": "ticker",
        "price": str(market_data.price),
        "best_bid": str(market_data.bid),
        "best_ask": str(market_data.ask),
        "volume_24h": str(market_data.volume),
        "time": market_data.timestamp.isoformat()
    })

async def handle_trade(trade: Dict[str, Any]) -> None:
    """Handle trade updates.
    
    Args:
        trade: Trade update
    """
    await broadcast_message({
        "type": "trade",
        "trade_id": trade.id,
        "symbol": trade.symbol,
        "price": str(trade.price),
        "size": str(trade.size),
        "side": trade.side.value,
        "timestamp": trade.timestamp.isoformat()
    })

async def start_market_data_stream() -> None:
    """Start market data WebSocket stream."""
    ws_client = CoinbaseWebSocketClient()
    
    # Register callbacks
    ws_client.on_ticker(handle_market_data)
    ws_client.on_trade(handle_trade)
    
    # Connect and subscribe
    await ws_client.connect()
    await ws_client.subscribe(
        channels=["ticker", "matches"],
        product_ids=["BTC-USD"]
    )

@app.route("/")
def index():
    """Render dashboard index page.
    
    Returns:
        Rendered template
    """
    return render_template("index.html")

@app.route("/api/data")
async def get_dashboard_data() -> Dict[str, Any]:
    """Get dashboard data.
    
    Returns:
        Dashboard data including account info, positions, and recent trades
    """
    try:
        client = get_client()
        
        # Get account information
        accounts = await client.get_accounts()
        
        # Get positions
        positions = await client.get_positions()
        
        # Get recent trades for BTC-USD
        trades = await client.get_trades("BTC-USD", limit=50)
        
        # Get current market data for BTC-USD
        market_data = await client.get_product_ticker("BTC-USD")
        
        await client.close()
        
        return jsonify({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "accounts": [
                {
                    "currency": acc.currency,
                    "balance": acc.balance,
                    "available": acc.available,
                    "hold": acc.hold
                }
                for acc in accounts
            ],
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "realized_pnl": pos.realized_pnl
                }
                for pos in positions
            ],
            "trades": [
                {
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "price": trade.price,
                    "size": trade.size,
                    "side": trade.side,
                    "timestamp": trade.timestamp.isoformat()
                }
                for trade in trades
            ],
            "market_data": {
                "symbol": market_data.symbol,
                "price": market_data.price,
                "bid": market_data.bid,
                "ask": market_data.ask,
                "volume": market_data.volume,
                "timestamp": market_data.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify({
            "error": "Failed to fetch dashboard data",
            "message": str(e)
        }), 500

async def websocket_handler(request):
    """Handle WebSocket connections.
    
    Args:
        request: WebSocket request
        
    Returns:
        WebSocket response
    """
    ws = WebSocketResponse()
    await ws.prepare(request)
    
    # Add to active connections
    active_ws.add(ws)
    
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'WebSocket connection closed with exception {ws.exception()}')
    finally:
        active_ws.remove(ws)
    
    return ws

def run_app():
    """Run the Flask application with WebSocket support."""
    # Create aiohttp application
    aioapp = web.Application()
    aioapp.router.add_get('/ws', websocket_handler)
    
    # Start market data stream
    loop = asyncio.get_event_loop()
    loop.create_task(start_market_data_stream())
    
    # Run the application
    web.run_app(aioapp, host='localhost', port=5001)

if __name__ == "__main__":
    run_app() 