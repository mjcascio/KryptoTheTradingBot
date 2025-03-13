# MetaTrader Integration Components Backup

This directory contains the archived MetaTrader integration components from the KryptoBot Trading System. These components have been temporarily removed from the main system but are preserved here for future use.

## Contents

1. `metatrader_stream.py`
   - Core MetaTrader market data streaming functionality
   - Includes configuration class and streaming functions
   - Rate limiting settings

## Integration Points

The following components were removed from the main system:

1. Market Data Stream:
   - Removed `_stream_metatrader` method from `market/data_stream.py`
   - Removed MetaTrader option from `_stream_symbol` method
   - Updated source documentation to remove MetaTrader references

2. Rate Limiting:
   - Removed MetaTrader rate limit configuration from `market/rate_limiter.py`
   - Original settings: 100 calls per minute with 60-second retry period

## Reintegration Steps

To reintegrate MetaTrader functionality:

1. Copy `metatrader_stream.py` to the `market` directory
2. Add MetaTrader rate limit configuration to `RateLimiter` class
3. Add MetaTrader streaming method to `MarketDataStream` class
4. Update source documentation to include MetaTrader options

## Configuration

MetaTrader connection settings:
```python
MetaTraderConfig(
    host="localhost",
    port=5000,
    symbols=[]  # List of symbols to monitor
)
```

Rate limiting configuration:
```python
METATRADER_RATE_LIMIT = {
    'calls': 100,
    'period': 60,  # 1 minute
    'retry_after': 60  # Wait 1 minute after limit is hit
}
```

## Usage Example

```python
from market.metatrader_stream import stream_metatrader, MetaTraderConfig

async def handle_data(data: Dict):
    print(f"Received {data['symbol']}: {data['price']}")

config = MetaTraderConfig(symbols=["EURUSD", "GBPUSD"])
await stream_metatrader("EURUSD", handle_data, config)
```

## Dependencies

- aiohttp
- asyncio
- MetaTrader 5 WebSocket API (running on localhost:5000) 