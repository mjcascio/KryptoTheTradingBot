"""MetaTrader market data streaming components for KryptoBot Trading System."""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Optional, Dict, List, Callable, Awaitable
from dataclasses import dataclass

from utils.logging import setup_logging
from utils.profiler import performance_monitor

logger = setup_logging(__name__)

@dataclass
class MetaTraderConfig:
    """MetaTrader connection configuration."""
    host: str = "localhost"
    port: int = 5000
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []

@performance_monitor.profile_async
async def stream_metatrader(
    symbol: str,
    callback: Callable[[Dict], Awaitable[None]],
    config: Optional[MetaTraderConfig] = None
) -> None:
    """Stream market data from MetaTrader.
    
    Args:
        symbol: Trading symbol
        callback: Async callback function for data updates
        config: Optional MetaTrader configuration
    """
    if config is None:
        config = MetaTraderConfig()
    
    url = f"ws://{config.host}:{config.port}/mt5/{symbol}"
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    # Create market data object
                    market_data = {
                        "symbol": symbol,
                        "timestamp": datetime.now(),
                        "price": float(data['price']),
                        "volume": float(data['volume']),
                        "bid": float(data['bid']),
                        "ask": float(data['ask']),
                        "high": float(data['high']),
                        "low": float(data['low'])
                    }
                    
                    await callback(market_data)

# Rate limiting configuration for MetaTrader
METATRADER_RATE_LIMIT = {
    'calls': 100,
    'period': 60,  # 1 minute
    'retry_after': 60  # Wait 1 minute after limit is hit
} 