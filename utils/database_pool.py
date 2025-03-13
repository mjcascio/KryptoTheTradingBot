"""Database connection pool for the KryptoBot Trading System."""

import logging
import aiosqlite
import asyncio
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class DatabasePool:
    """Connection pool for SQLite database."""
    
    def __init__(self, database: str, min_size: int = 5, max_size: int = 10):
        """Initialize the database pool.
        
        Args:
            database: Path to the SQLite database file
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
        """
        self.database = database
        self.min_size = min_size
        self.max_size = max_size
        self.pool = []
        self.in_use = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        logger.info(f"Database pool created for {database}")
        
    async def initialize(self):
        """Initialize the connection pool."""
        async with self._lock:
            if self._initialized:
                return
                
            logger.info(f"Initializing database pool with {self.min_size} connections")
            
            # Create initial connections
            for _ in range(self.min_size):
                conn = await self._create_connection()
                self.pool.append(conn)
                
            self._initialized = True
            logger.info("Database pool initialized")
            
    async def _create_connection(self):
        """Create a new database connection.
        
        Returns:
            New SQLite connection
        """
        try:
            conn = await aiosqlite.connect(self.database)
            # Enable foreign keys
            await conn.execute("PRAGMA foreign_keys = ON")
            # Set journal mode to WAL for better concurrency
            await conn.execute("PRAGMA journal_mode = WAL")
            # Set synchronous mode to NORMAL for better performance
            await conn.execute("PRAGMA synchronous = NORMAL")
            await conn.commit()
            return conn
        except Exception as e:
            logger.error(f"Error creating database connection: {e}")
            raise
            
    async def acquire(self):
        """Acquire a connection from the pool.
        
        Returns:
            SQLite connection
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            # Check if there's an available connection
            if not self.pool:
                # If we can create more connections
                if len(self.in_use) < self.max_size:
                    conn = await self._create_connection()
                else:
                    # Wait for a connection to be released
                    logger.warning("Database pool exhausted, waiting for a connection")
                    await asyncio.sleep(0.1)
                    return await self.acquire()
            else:
                # Get a connection from the pool
                conn = self.pool.pop(0)
                
            # Mark connection as in use
            self.in_use[id(conn)] = conn
            return conn
            
    async def release(self, conn):
        """Release a connection back to the pool.
        
        Args:
            conn: SQLite connection to release
        """
        async with self._lock:
            # Remove from in-use dict
            conn_id = id(conn)
            if conn_id in self.in_use:
                del self.in_use[conn_id]
                
                # Add back to pool if we're below max_size
                if len(self.pool) < self.max_size:
                    self.pool.append(conn)
                else:
                    # Close the connection if we have enough in the pool
                    await conn.close()
                    
    async def close(self):
        """Close all connections in the pool."""
        async with self._lock:
            # Close all connections in the pool
            for conn in self.pool:
                await conn.close()
                
            # Close all in-use connections
            for conn in self.in_use.values():
                await conn.close()
                
            # Clear the pool and in-use dict
            self.pool = []
            self.in_use = {}
            self._initialized = False
            
            logger.info("Database pool closed")
            
    async def execute(self, query: str, params: tuple = ()):
        """Execute a query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query result
        """
        conn = await self.acquire()
        try:
            cursor = await conn.execute(query, params)
            await conn.commit()
            return cursor
        finally:
            await self.release(conn)
            
    async def execute_many(self, query: str, params_list: List[tuple]):
        """Execute a query with multiple parameter sets.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Returns:
            Query result
        """
        conn = await self.acquire()
        try:
            cursor = await conn.executemany(query, params_list)
            await conn.commit()
            return cursor
        finally:
            await self.release(conn)
            
    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch a single row from a query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Single row or None
        """
        conn = await self.acquire()
        try:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return row
        finally:
            await self.release(conn)
            
    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows from a query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of rows
        """
        conn = await self.acquire()
        try:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return rows
        finally:
            await self.release(conn)
            
    async def transaction(self):
        """Create a transaction context manager.
        
        Returns:
            Transaction context manager
        """
        return Transaction(self) 