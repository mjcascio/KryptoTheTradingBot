"""Data persistence for market data."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import asdict
import motor.motor_asyncio
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

from market.data_stream import MarketData
from utils.logging import setup_logging

logger = setup_logging(__name__)

class MarketDataStore:
    """Store for market data using InfluxDB for time series and MongoDB for metadata."""
    
    def __init__(
        self,
        influx_url: str = "http://localhost:8086",
        influx_token: str = "your-token",
        influx_org: str = "kryptobot",
        influx_bucket: str = "market_data",
        mongo_url: str = "mongodb://localhost:27017",
        mongo_db: str = "kryptobot"
    ) -> None:
        """Initialize the market data store.
        
        Args:
            influx_url: InfluxDB URL
            influx_token: InfluxDB API token
            influx_org: InfluxDB organization
            influx_bucket: InfluxDB bucket
            mongo_url: MongoDB URL
            mongo_db: MongoDB database name
        """
        # InfluxDB client for time series data
        self.influx_client = InfluxDBClient(
            url=influx_url,
            token=influx_token,
            org=influx_org
        )
        self.influx_bucket = influx_bucket
        self.influx_org = influx_org
        self.write_api = self.influx_client.write_api(write_options=ASYNCHRONOUS)
        
        # MongoDB client for metadata
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        self.mongo_db = self.mongo_client[mongo_db]
        self.symbols = self.mongo_db.symbols
        self.metadata = self.mongo_db.metadata

    async def store_market_data(self, data: MarketData) -> None:
        """Store market data point.
        
        Args:
            data: Market data to store
        """
        # Store time series data in InfluxDB
        point = (
            Point("market_data")
            .tag("symbol", data.symbol)
            .field("price", data.price)
            .field("volume", data.volume)
            .time(data.timestamp)
        )
        
        if data.bid is not None:
            point = point.field("bid", data.bid)
        if data.ask is not None:
            point = point.field("ask", data.ask)
        if data.high is not None:
            point = point.field("high", data.high)
        if data.low is not None:
            point = point.field("low", data.low)
        
        await self.write_api.write(
            bucket=self.influx_bucket,
            org=self.influx_org,
            record=point
        )
        
        # Update metadata in MongoDB
        await self.metadata.update_one(
            {"symbol": data.symbol},
            {
                "$set": {
                    "last_update": data.timestamp,
                    "last_price": data.price,
                    "last_volume": data.volume
                }
            },
            upsert=True
        )

    async def get_market_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        interval: str = "1m"
    ) -> List[Dict[str, Any]]:
        """Get historical market data.
        
        Args:
            symbol: Trading symbol
            start_time: Start time
            end_time: End time (defaults to now)
            interval: Time interval (e.g., "1m", "5m", "1h")
            
        Returns:
            List of market data points
        """
        if end_time is None:
            end_time = datetime.now()
        
        # Query InfluxDB
        query = f'''
            from(bucket: "{self.influx_bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> aggregateWindow(every: {interval}, fn: mean)
        '''
        
        result = []
        tables = await self.influx_client.query_api().query(query, org=self.influx_org)
        
        for table in tables:
            for record in table.records:
                result.append({
                    "timestamp": record.get_time(),
                    "price": record.get_value(),
                    "volume": record.values.get("volume"),
                    "bid": record.values.get("bid"),
                    "ask": record.values.get("ask"),
                    "high": record.values.get("high"),
                    "low": record.values.get("low")
                })
        
        return result

    async def get_symbol_metadata(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol metadata.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Symbol metadata or None
        """
        return await self.metadata.find_one({"symbol": symbol})

    async def update_symbol_metadata(
        self,
        symbol: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update symbol metadata.
        
        Args:
            symbol: Trading symbol
            metadata: Metadata to update
        """
        await self.metadata.update_one(
            {"symbol": symbol},
            {"$set": metadata},
            upsert=True
        )

    async def get_active_symbols(self) -> List[str]:
        """Get list of active trading symbols.
        
        Returns:
            List of active symbols
        """
        cursor = self.metadata.find(
            {"active": True},
            projection={"symbol": 1, "_id": 0}
        )
        symbols = await cursor.to_list(length=None)
        return [doc["symbol"] for doc in symbols]

    async def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up old market data.
        
        Args:
            days: Number of days of data to keep
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # Delete old data from InfluxDB
        delete_api = self.influx_client.delete_api()
        await delete_api.delete(
            start=datetime.min,
            stop=cutoff,
            bucket=self.influx_bucket,
            org=self.influx_org
        )
        
        # Update metadata in MongoDB
        await self.metadata.update_many(
            {"last_update": {"$lt": cutoff}},
            {"$set": {"active": False}}
        )

    async def close(self) -> None:
        """Close database connections."""
        self.influx_client.close()
        self.mongo_client.close()

# Create global instance
market_store = MarketDataStore() 