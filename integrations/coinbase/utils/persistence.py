"""Data persistence system for historical analysis."""

import sqlite3
import json
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: str) -> None:
        """Initialize database.
        
        Args:
            db_path: Database file path
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        
        # Create tables if they don't exist
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Market data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    data_type TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_market_data_lookup (symbol, timestamp, data_type)
                )
            """)
            
            # Performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    response_time REAL NOT NULL,
                    request_count INTEGER NOT NULL,
                    error_count INTEGER NOT NULL,
                    cache_hits INTEGER NOT NULL,
                    cache_misses INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_performance_metrics_timestamp (timestamp)
                )
            """)
            
            # Trade history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    type TEXT NOT NULL,
                    size REAL NOT NULL,
                    price REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    order_id TEXT,
                    trade_id TEXT,
                    fees REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_trade_history_lookup (symbol, timestamp)
                )
            """)
            
            conn.commit()
    
    @asynccontextmanager
    async def connection(self):
        """Get database connection with async lock."""
        async with self._lock:
            if not self._conn:
                self._conn = sqlite3.connect(self.db_path)
            try:
                yield self._conn
            finally:
                pass
    
    async def store_market_data(
        self,
        symbol: str,
        data_type: str,
        data: Any,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Store market data.
        
        Args:
            symbol: Trading pair symbol
            data_type: Type of data
            data: Market data
            timestamp: Data timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        async with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO market_data (symbol, timestamp, data_type, data)
                VALUES (?, ?, ?, ?)
                """,
                (
                    symbol,
                    timestamp.isoformat(),
                    data_type,
                    json.dumps(data)
                )
            )
            conn.commit()
    
    async def get_market_data(
        self,
        symbol: str,
        data_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get historical market data.
        
        Args:
            symbol: Trading pair symbol
            data_type: Type of data
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of records
            
        Returns:
            List of market data records
        """
        query = """
            SELECT timestamp, data
            FROM market_data
            WHERE symbol = ? AND data_type = ?
        """
        params = [symbol, data_type]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.connection() as conn:
            cursor = conn.execute(query, params)
            return [
                {
                    "timestamp": datetime.fromisoformat(row[0]),
                    "data": json.loads(row[1])
                }
                for row in cursor.fetchall()
            ]
    
    async def store_performance_metrics(
        self,
        metrics: Dict[str, Any]
    ) -> None:
        """Store performance metrics.
        
        Args:
            metrics: Performance metrics
        """
        async with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO performance_metrics (
                    timestamp,
                    cpu_percent,
                    memory_percent,
                    response_time,
                    request_count,
                    error_count,
                    cache_hits,
                    cache_misses
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics["timestamp"].isoformat(),
                    metrics["cpu_percent"],
                    metrics["memory_percent"],
                    metrics["response_time"],
                    metrics["request_count"],
                    metrics["error_count"],
                    metrics["cache_hits"],
                    metrics["cache_misses"]
                )
            )
            conn.commit()
    
    async def get_performance_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Get historical performance metrics.
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of records
            
        Returns:
            DataFrame of performance metrics
        """
        query = "SELECT * FROM performance_metrics"
        params = []
        
        if start_time or end_time:
            query += " WHERE"
            if start_time:
                query += " timestamp >= ?"
                params.append(start_time.isoformat())
            if end_time:
                query += " AND" if start_time else ""
                query += " timestamp <= ?"
                params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
    
    async def store_trade(
        self,
        symbol: str,
        side: str,
        type: str,
        size: float,
        price: float,
        timestamp: datetime,
        order_id: Optional[str] = None,
        trade_id: Optional[str] = None,
        fees: Optional[float] = None
    ) -> None:
        """Store trade record.
        
        Args:
            symbol: Trading pair symbol
            side: Trade side
            type: Order type
            size: Trade size
            price: Trade price
            timestamp: Trade timestamp
            order_id: Order ID
            trade_id: Trade ID
            fees: Trade fees
        """
        async with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO trade_history (
                    symbol,
                    side,
                    type,
                    size,
                    price,
                    timestamp,
                    order_id,
                    trade_id,
                    fees
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    side,
                    type,
                    size,
                    price,
                    timestamp.isoformat(),
                    order_id,
                    trade_id,
                    fees
                )
            )
            conn.commit()
    
    async def get_trade_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Get trade history.
        
        Args:
            symbol: Trading pair symbol filter
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of records
            
        Returns:
            DataFrame of trade history
        """
        query = "SELECT * FROM trade_history"
        params = []
        
        conditions = []
        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        async with self.connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
    
    async def cleanup_old_data(
        self,
        older_than: timedelta
    ) -> None:
        """Clean up old data.
        
        Args:
            older_than: Age threshold for deletion
        """
        cutoff = datetime.now() - older_than
        
        async with self.connection() as conn:
            conn.execute(
                "DELETE FROM market_data WHERE timestamp < ?",
                (cutoff.isoformat(),)
            )
            conn.execute(
                "DELETE FROM performance_metrics WHERE timestamp < ?",
                (cutoff.isoformat(),)
            )
            conn.commit()
    
    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None 