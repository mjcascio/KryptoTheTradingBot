"""
Blockchain Audit Trail Plugin for KryptoBot Trading System

This plugin implements a blockchain-based audit trail for recording trades and system changes,
providing immutable records for regulatory compliance and system integrity verification.
"""

import hashlib
import json
import time
from datetime import datetime
import os
import logging
from typing import Dict, List, Any, Optional, Union
import threading
import sqlite3

from core.plugin import Plugin

logger = logging.getLogger(__name__)

class Block:
    """Represents a block in the blockchain."""
    
    def __init__(self, index: int, timestamp: float, data: Dict[str, Any], 
                 previous_hash: str, nonce: int = 0):
        """
        Initialize a new block.
        
        Args:
            index: Block index in the chain
            timestamp: Block creation timestamp
            data: Data to be stored in the block
            previous_hash: Hash of the previous block
            nonce: Nonce value for proof of work
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate the hash of the block."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        """
        Mine the block with proof of work.
        
        Args:
            difficulty: Number of leading zeros required in hash
        """
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }


class Blockchain:
    """Simple blockchain implementation for audit trail."""
    
    def __init__(self, difficulty: int = 2, db_path: str = None):
        """
        Initialize the blockchain.
        
        Args:
            difficulty: Mining difficulty (number of leading zeros)
            db_path: Path to SQLite database for persistence
        """
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.pending_transactions: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.db_path = db_path
        
        # Initialize database if path provided
        if db_path:
            self._init_db()
        
        # Create genesis block if chain is empty
        if not self.chain:
            self._create_genesis_block()
        
        # Load from database if path provided
        if db_path:
            self._load_from_db()
    
    def _create_genesis_block(self) -> None:
        """Create the genesis block."""
        genesis_block = Block(0, time.time(), {
            "message": "Genesis Block",
            "timestamp": datetime.now().isoformat()
        }, "0")
        self.chain.append(genesis_block)
        
        if self.db_path:
            self._save_block_to_db(genesis_block)
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create blocks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY,
            block_index INTEGER,
            block_timestamp REAL,
            block_data TEXT,
            previous_hash TEXT,
            nonce INTEGER,
            hash TEXT
        )
        ''')
        
        # Create transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_transactions (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_from_db(self) -> None:
        """Load blockchain from database."""
        if not os.path.exists(self.db_path):
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load blocks
        cursor.execute("SELECT block_index, block_timestamp, block_data, previous_hash, nonce, hash FROM blocks ORDER BY block_index")
        rows = cursor.fetchall()
        
        self.chain = []
        for row in rows:
            index, timestamp, data_str, previous_hash, nonce, hash_val = row
            data = json.loads(data_str)
            
            block = Block(index, timestamp, data, previous_hash, nonce)
            block.hash = hash_val
            self.chain.append(block)
        
        # Load pending transactions
        cursor.execute("SELECT data FROM pending_transactions")
        rows = cursor.fetchall()
        
        self.pending_transactions = []
        for row in rows:
            data_str = row[0]
            data = json.loads(data_str)
            self.pending_transactions.append(data)
        
        conn.close()
    
    def _save_block_to_db(self, block: Block) -> None:
        """Save a block to the database."""
        if not self.db_path:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO blocks (block_index, block_timestamp, block_data, previous_hash, nonce, hash) VALUES (?, ?, ?, ?, ?, ?)",
            (block.index, block.timestamp, json.dumps(block.data), block.previous_hash, block.nonce, block.hash)
        )
        
        conn.commit()
        conn.close()
    
    def _save_pending_transactions(self) -> None:
        """Save pending transactions to database."""
        if not self.db_path:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing pending transactions
        cursor.execute("DELETE FROM pending_transactions")
        
        # Insert current pending transactions
        for tx in self.pending_transactions:
            cursor.execute(
                "INSERT INTO pending_transactions (data) VALUES (?)",
                (json.dumps(tx),)
            )
        
        conn.commit()
        conn.close()
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the chain."""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict[str, Any]) -> None:
        """
        Add a transaction to pending transactions.
        
        Args:
            transaction: Transaction data to add
        """
        with self.lock:
            # Add timestamp if not present
            if "timestamp" not in transaction:
                transaction["timestamp"] = datetime.now().isoformat()
            
            self.pending_transactions.append(transaction)
            
            if self.db_path:
                self._save_pending_transactions()
    
    def mine_pending_transactions(self) -> Optional[Block]:
        """
        Mine pending transactions into a new block.
        
        Returns:
            The newly created block or None if no transactions
        """
        with self.lock:
            if not self.pending_transactions:
                return None
            
            latest_block = self.get_latest_block()
            new_block = Block(
                latest_block.index + 1,
                time.time(),
                {
                    "transactions": self.pending_transactions,
                    "mined_at": datetime.now().isoformat()
                },
                latest_block.hash
            )
            
            new_block.mine_block(self.difficulty)
            self.chain.append(new_block)
            self.pending_transactions = []
            
            if self.db_path:
                self._save_block_to_db(new_block)
                self._save_pending_transactions()
            
            return new_block
    
    def is_chain_valid(self) -> bool:
        """
        Validate the integrity of the blockchain.
        
        Returns:
            True if valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Validate current block hash
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Validate chain linkage
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_chain(self) -> List[Dict[str, Any]]:
        """
        Get the entire blockchain.
        
        Returns:
            List of blocks as dictionaries
        """
        return [block.to_dict() for block in self.chain]
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a block by its index.
        
        Args:
            index: Block index to retrieve
            
        Returns:
            Block as dictionary or None if not found
        """
        if 0 <= index < len(self.chain):
            return self.chain[index].to_dict()
        return None
    
    def get_block_by_hash(self, hash_value: str) -> Optional[Dict[str, Any]]:
        """
        Get a block by its hash.
        
        Args:
            hash_value: Block hash to retrieve
            
        Returns:
            Block as dictionary or None if not found
        """
        for block in self.chain:
            if block.hash == hash_value:
                return block.to_dict()
        return None
    
    def get_transactions_by_type(self, tx_type: str) -> List[Dict[str, Any]]:
        """
        Get all transactions of a specific type.
        
        Args:
            tx_type: Transaction type to filter by
            
        Returns:
            List of matching transactions
        """
        transactions = []
        for block in self.chain:
            if "transactions" in block.data:
                for tx in block.data["transactions"]:
                    if tx.get("type") == tx_type:
                        transactions.append(tx)
        return transactions


class BlockchainAuditPlugin(Plugin):
    """Plugin for blockchain-based audit trail in KryptoBot."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the blockchain audit plugin.
        
        Args:
            config: Plugin configuration
        """
        super().__init__(config)
        self._name = "blockchain_audit"
        self._description = "Blockchain-based audit trail for KryptoBot"
        self._version = "1.0.0"
        self._category = "audit"
        
        # Default configuration
        self.default_config = {
            "enabled": True,
            "mining_interval": 300,  # 5 minutes
            "difficulty": 2,
            "db_path": "data/blockchain/audit_chain.db",
            "auto_mine": True,
            "record_types": ["trade", "order", "system_change", "login", "config_change"]
        }
        
        # Merge with provided config
        self.config = {**self.default_config, **(config or {})}
        
        # Initialize blockchain
        self.blockchain = Blockchain(
            difficulty=self.config["difficulty"],
            db_path=self.config["db_path"]
        )
        
        # Mining thread
        self.mining_thread = None
        self.stop_mining = threading.Event()
    
    def initialize(self, context: Dict[str, Any] = None) -> bool:
        """
        Initialize the plugin.
        
        Args:
            context: Context data for initialization
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Call parent initialize method
            super().initialize(context or {})
            
            logger.info(f"Initializing {self.name} plugin v{self.version}")
            
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.config["db_path"]), exist_ok=True)
            
            # Start mining thread if auto-mine is enabled
            if self.config["auto_mine"]:
                self._start_mining_thread()
            
            logger.info(f"{self.name} plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.name} plugin: {str(e)}")
            return False
    
    def _start_mining_thread(self) -> None:
        """Start the background mining thread."""
        if self.mining_thread and self.mining_thread.is_alive():
            return
        
        self.stop_mining.clear()
        self.mining_thread = threading.Thread(target=self._mining_worker)
        self.mining_thread.daemon = True
        self.mining_thread.start()
        logger.info("Blockchain mining thread started")
    
    def _mining_worker(self) -> None:
        """Background worker for mining blocks periodically."""
        while not self.stop_mining.is_set():
            try:
                # Mine pending transactions
                with self.blockchain.lock:
                    if self.blockchain.pending_transactions:
                        block = self.blockchain.mine_pending_transactions()
                        if block:
                            logger.info(f"Mined new block #{block.index} with {len(block.data['transactions'])} transactions")
            except Exception as e:
                logger.error(f"Error in mining thread: {str(e)}")
            
            # Sleep until next mining interval
            self.stop_mining.wait(self.config["mining_interval"])
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            True if shutdown successful, False otherwise
        """
        try:
            logger.info(f"Shutting down {self.name} plugin")
            
            # Stop mining thread
            if self.mining_thread and self.mining_thread.is_alive():
                self.stop_mining.set()
                self.mining_thread.join(timeout=5.0)
            
            # Mine any remaining transactions
            if self.blockchain.pending_transactions:
                self.blockchain.mine_pending_transactions()
            
            logger.info(f"{self.name} plugin shutdown complete")
            return True
        except Exception as e:
            logger.error(f"Error during {self.name} plugin shutdown: {str(e)}")
            return False
    
    def record_trade(self, trade_data: Dict[str, Any]) -> bool:
        """
        Record a trade in the blockchain.
        
        Args:
            trade_data: Trade data to record
            
        Returns:
            True if recorded successfully, False otherwise
        """
        try:
            if "trade" not in self.config["record_types"]:
                return False
            
            transaction = {
                "type": "trade",
                "data": trade_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.blockchain.add_transaction(transaction)
            logger.debug(f"Recorded trade transaction: {trade_data.get('id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to record trade: {str(e)}")
            return False
    
    def record_order(self, order_data: Dict[str, Any]) -> bool:
        """
        Record an order in the blockchain.
        
        Args:
            order_data: Order data to record
            
        Returns:
            True if recorded successfully, False otherwise
        """
        try:
            if "order" not in self.config["record_types"]:
                return False
            
            transaction = {
                "type": "order",
                "data": order_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.blockchain.add_transaction(transaction)
            logger.debug(f"Recorded order transaction: {order_data.get('id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to record order: {str(e)}")
            return False
    
    def record_system_change(self, change_data: Dict[str, Any]) -> bool:
        """
        Record a system change in the blockchain.
        
        Args:
            change_data: System change data to record
            
        Returns:
            True if recorded successfully, False otherwise
        """
        try:
            if "system_change" not in self.config["record_types"]:
                return False
            
            transaction = {
                "type": "system_change",
                "data": change_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.blockchain.add_transaction(transaction)
            logger.debug(f"Recorded system change: {change_data.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to record system change: {str(e)}")
            return False
    
    def record_login(self, user_data: Dict[str, Any]) -> bool:
        """
        Record a user login in the blockchain.
        
        Args:
            user_data: User login data to record
            
        Returns:
            True if recorded successfully, False otherwise
        """
        try:
            if "login" not in self.config["record_types"]:
                return False
            
            transaction = {
                "type": "login",
                "data": user_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.blockchain.add_transaction(transaction)
            logger.debug(f"Recorded login: {user_data.get('username', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to record login: {str(e)}")
            return False
    
    def record_config_change(self, config_data: Dict[str, Any]) -> bool:
        """
        Record a configuration change in the blockchain.
        
        Args:
            config_data: Configuration change data to record
            
        Returns:
            True if recorded successfully, False otherwise
        """
        try:
            if "config_change" not in self.config["record_types"]:
                return False
            
            transaction = {
                "type": "config_change",
                "data": config_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.blockchain.add_transaction(transaction)
            logger.debug(f"Recorded config change: {config_data.get('component', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to record config change: {str(e)}")
            return False
    
    def get_audit_trail(self, 
                        record_type: Optional[str] = None, 
                        start_time: Optional[str] = None,
                        end_time: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit trail records with optional filtering.
        
        Args:
            record_type: Filter by record type
            start_time: Filter by start time (ISO format)
            end_time: Filter by end time (ISO format)
            limit: Maximum number of records to return
            
        Returns:
            List of matching audit records
        """
        try:
            # Get all transactions from the blockchain
            all_transactions = []
            for block in self.blockchain.chain:
                if "transactions" in block.data:
                    for tx in block.data["transactions"]:
                        tx["block_index"] = block.index
                        tx["block_hash"] = block.hash
                        all_transactions.append(tx)
            
            # Apply filters
            filtered_transactions = all_transactions
            
            if record_type:
                filtered_transactions = [tx for tx in filtered_transactions if tx.get("type") == record_type]
            
            if start_time:
                start_dt = datetime.fromisoformat(start_time)
                filtered_transactions = [
                    tx for tx in filtered_transactions 
                    if datetime.fromisoformat(tx.get("timestamp", "1970-01-01T00:00:00")) >= start_dt
                ]
            
            if end_time:
                end_dt = datetime.fromisoformat(end_time)
                filtered_transactions = [
                    tx for tx in filtered_transactions 
                    if datetime.fromisoformat(tx.get("timestamp", "2099-12-31T23:59:59")) <= end_dt
                ]
            
            # Sort by timestamp (newest first) and apply limit
            sorted_transactions = sorted(
                filtered_transactions,
                key=lambda tx: tx.get("timestamp", "1970-01-01T00:00:00"),
                reverse=True
            )
            
            return sorted_transactions[:limit]
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {str(e)}")
            return []
    
    def verify_chain_integrity(self) -> bool:
        """
        Verify the integrity of the blockchain.
        
        Returns:
            True if blockchain is valid, False otherwise
        """
        return self.blockchain.is_chain_valid()
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the blockchain.
        
        Returns:
            Dictionary with blockchain statistics
        """
        try:
            chain = self.blockchain.chain
            
            # Count transactions by type
            tx_counts = {}
            total_tx = 0
            
            for block in chain:
                if "transactions" in block.data:
                    block_txs = block.data["transactions"]
                    total_tx += len(block_txs)
                    
                    for tx in block_txs:
                        tx_type = tx.get("type", "unknown")
                        tx_counts[tx_type] = tx_counts.get(tx_type, 0) + 1
            
            # Get timestamps for first and last blocks
            first_block_time = datetime.fromtimestamp(chain[0].timestamp).isoformat() if chain else None
            last_block_time = datetime.fromtimestamp(chain[-1].timestamp).isoformat() if chain else None
            
            return {
                "chain_length": len(chain),
                "total_transactions": total_tx,
                "transaction_types": tx_counts,
                "pending_transactions": len(self.blockchain.pending_transactions),
                "first_block_time": first_block_time,
                "last_block_time": last_block_time,
                "is_valid": self.blockchain.is_chain_valid()
            }
        except Exception as e:
            logger.error(f"Error getting chain stats: {str(e)}")
            return {
                "error": str(e),
                "chain_length": 0,
                "total_transactions": 0
            }
    
    def force_mine(self) -> Optional[Dict[str, Any]]:
        """
        Force mining of pending transactions.
        
        Returns:
            Newly created block as dictionary or None
        """
        try:
            block = self.blockchain.mine_pending_transactions()
            if block:
                return block.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error during force mining: {str(e)}")
            return None
    
    def execute(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the plugin with the given data.
        
        Args:
            data: Input data for the plugin
            
        Returns:
            Result of the plugin execution
        """
        if not data:
            return {"status": "error", "message": "No data provided"}
        
        action = data.get("action")
        
        if action == "record_trade":
            success = self.record_trade(data.get("trade_data", {}))
            return {"status": "success" if success else "error"}
        
        elif action == "record_order":
            success = self.record_order(data.get("order_data", {}))
            return {"status": "success" if success else "error"}
        
        elif action == "record_system_change":
            success = self.record_system_change(data.get("change_data", {}))
            return {"status": "success" if success else "error"}
        
        elif action == "get_audit_trail":
            records = self.get_audit_trail(
                record_type=data.get("record_type"),
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                limit=data.get("limit", 100)
            )
            return {"status": "success", "records": records}
        
        elif action == "verify_integrity":
            is_valid = self.verify_chain_integrity()
            return {"status": "success", "is_valid": is_valid}
        
        elif action == "get_stats":
            stats = self.get_chain_stats()
            return {"status": "success", "stats": stats}
        
        elif action == "force_mine":
            block = self.force_mine()
            return {"status": "success", "block": block}
        
        else:
            return {"status": "error", "message": f"Unknown action: {action}"} 