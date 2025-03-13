#!/usr/bin/env python
"""
Unit tests for the Blockchain Audit Trail Plugin.
"""

import unittest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
import time
import logging
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from plugins.blockchain_audit.blockchain_audit_plugin import BlockchainAuditPlugin, Block, Blockchain
from plugins.blockchain_audit.utils import (
    generate_hash,
    validate_timestamp,
    get_timestamp,
    sanitize_sensitive_data,
    filter_transactions_by_criteria,
    generate_audit_report
)

# Disable logging for tests
logging.disable(logging.CRITICAL)

class TestBlock(unittest.TestCase):
    """Test cases for the Block class."""
    
    def test_block_initialization(self):
        """Test block initialization and hash calculation."""
        data = {"test": "data"}
        block = Block(1, time.time(), data, "previous_hash")
        
        self.assertEqual(block.index, 1)
        self.assertEqual(block.data, data)
        self.assertEqual(block.previous_hash, "previous_hash")
        self.assertIsNotNone(block.hash)
        self.assertTrue(isinstance(block.hash, str))
        self.assertEqual(len(block.hash), 64)  # SHA-256 hash length
    
    def test_block_mining(self):
        """Test block mining with proof of work."""
        data = {"test": "data"}
        block = Block(1, time.time(), data, "previous_hash")
        
        # Mine block with difficulty 2 (two leading zeros)
        difficulty = 2
        block.mine_block(difficulty)
        
        self.assertTrue(block.hash.startswith("0" * difficulty))
    
    def test_block_to_dict(self):
        """Test conversion of block to dictionary."""
        data = {"test": "data"}
        timestamp = time.time()
        block = Block(1, timestamp, data, "previous_hash")
        
        block_dict = block.to_dict()
        
        self.assertEqual(block_dict["index"], 1)
        self.assertEqual(block_dict["timestamp"], timestamp)
        self.assertEqual(block_dict["data"], data)
        self.assertEqual(block_dict["previous_hash"], "previous_hash")
        self.assertEqual(block_dict["hash"], block.hash)


class TestBlockchain(unittest.TestCase):
    """Test cases for the Blockchain class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_blockchain.db")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_blockchain_initialization(self):
        """Test blockchain initialization with genesis block."""
        blockchain = Blockchain()
        
        self.assertEqual(len(blockchain.chain), 1)
        self.assertEqual(blockchain.chain[0].index, 0)
        self.assertEqual(blockchain.chain[0].previous_hash, "0")
    
    def test_add_transaction(self):
        """Test adding a transaction to the blockchain."""
        blockchain = Blockchain()
        
        transaction = {"type": "test", "data": "test_data"}
        blockchain.add_transaction(transaction)
        
        self.assertEqual(len(blockchain.pending_transactions), 1)
        self.assertEqual(blockchain.pending_transactions[0]["type"], "test")
        self.assertTrue("timestamp" in blockchain.pending_transactions[0])
    
    def test_mine_pending_transactions(self):
        """Test mining pending transactions into a new block."""
        blockchain = Blockchain()
        
        # Add transactions
        for i in range(3):
            blockchain.add_transaction({"type": "test", "data": f"test_data_{i}"})
        
        # Mine transactions
        new_block = blockchain.mine_pending_transactions()
        
        self.assertIsNotNone(new_block)
        self.assertEqual(len(blockchain.chain), 2)
        self.assertEqual(blockchain.chain[1].index, 1)
        self.assertEqual(len(blockchain.pending_transactions), 0)
        self.assertEqual(len(blockchain.chain[1].data["transactions"]), 3)
    
    def test_chain_validation(self):
        """Test blockchain validation."""
        blockchain = Blockchain()
        
        # Add and mine transactions
        blockchain.add_transaction({"type": "test", "data": "test_data"})
        blockchain.mine_pending_transactions()
        
        # Chain should be valid
        self.assertTrue(blockchain.is_chain_valid())
        
        # Tamper with a block
        blockchain.chain[1].data = {"tampered": "data"}
        
        # Chain should be invalid
        self.assertFalse(blockchain.is_chain_valid())
    
    def test_blockchain_persistence(self):
        """Test blockchain persistence to SQLite database."""
        # Create blockchain with database
        blockchain = Blockchain(db_path=self.db_path)
        
        # Add and mine transactions
        blockchain.add_transaction({"type": "test", "data": "test_data_1"})
        blockchain.add_transaction({"type": "test", "data": "test_data_2"})
        blockchain.mine_pending_transactions()
        
        # Create new blockchain instance with same database
        blockchain2 = Blockchain(db_path=self.db_path)
        
        # Check if data was loaded correctly
        self.assertEqual(len(blockchain2.chain), 2)
        self.assertEqual(blockchain2.chain[1].data["transactions"][0]["data"], "test_data_1")
        self.assertEqual(blockchain2.chain[1].data["transactions"][1]["data"], "test_data_2")


class TestBlockchainAuditPlugin(unittest.TestCase):
    """Test cases for the BlockchainAuditPlugin class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_audit_chain.db")
        
        self.config = {
            "enabled": True,
            "mining_interval": 1,  # 1 second for faster tests
            "difficulty": 1,  # Lower difficulty for faster tests
            "db_path": self.db_path,
            "auto_mine": False,  # Disable auto-mining for tests
            "record_types": ["trade", "order", "system_change", "login", "config_change"]
        }
        
        self.plugin = BlockchainAuditPlugin(self.config)
        self.plugin.initialize()
    
    def tearDown(self):
        """Clean up test environment."""
        self.plugin.shutdown()
        shutil.rmtree(self.temp_dir)
    
    def test_plugin_initialization(self):
        """Test plugin initialization."""
        self.assertEqual(self.plugin.name, "blockchain_audit")
        self.assertEqual(self.plugin.version, "1.0.0")
        self.assertEqual(self.plugin.category, "audit")
        self.assertIsNotNone(self.plugin.blockchain)
        self.assertEqual(len(self.plugin.blockchain.chain), 1)  # Genesis block
    
    def test_record_trade(self):
        """Test recording a trade."""
        trade_data = {
            "id": "trade123",
            "symbol": "BTC/USD",
            "side": "buy",
            "quantity": 1.5,
            "price": 50000.0,
            "timestamp": datetime.now().isoformat()
        }
        
        success = self.plugin.record_trade(trade_data)
        
        self.assertTrue(success)
        self.assertEqual(len(self.plugin.blockchain.pending_transactions), 1)
        self.assertEqual(self.plugin.blockchain.pending_transactions[0]["type"], "trade")
        self.assertEqual(self.plugin.blockchain.pending_transactions[0]["data"]["id"], "trade123")
    
    def test_record_order(self):
        """Test recording an order."""
        order_data = {
            "id": "order456",
            "symbol": "ETH/USD",
            "side": "sell",
            "quantity": 10.0,
            "price": 3000.0,
            "order_type": "limit",
            "timestamp": datetime.now().isoformat()
        }
        
        success = self.plugin.record_order(order_data)
        
        self.assertTrue(success)
        self.assertEqual(len(self.plugin.blockchain.pending_transactions), 1)
        self.assertEqual(self.plugin.blockchain.pending_transactions[0]["type"], "order")
        self.assertEqual(self.plugin.blockchain.pending_transactions[0]["data"]["id"], "order456")
    
    def test_record_system_change(self):
        """Test recording a system change."""
        change_data = {
            "component": "trading_bot",
            "change_type": "config_update",
            "user": "admin",
            "details": {"parameter": "risk_level", "old_value": "medium", "new_value": "low"},
            "timestamp": datetime.now().isoformat()
        }
        
        success = self.plugin.record_system_change(change_data)
        
        self.assertTrue(success)
        self.assertEqual(len(self.plugin.blockchain.pending_transactions), 1)
        self.assertEqual(self.plugin.blockchain.pending_transactions[0]["type"], "system_change")
        self.assertEqual(self.plugin.blockchain.pending_transactions[0]["data"]["component"], "trading_bot")
    
    def test_force_mine(self):
        """Test force mining of transactions."""
        # Add some transactions
        self.plugin.record_trade({"id": "trade1", "symbol": "BTC/USD"})
        self.plugin.record_order({"id": "order1", "symbol": "ETH/USD"})
        
        # Force mine
        block = self.plugin.force_mine()
        
        self.assertIsNotNone(block)
        self.assertEqual(block["index"], 1)
        self.assertEqual(len(self.plugin.blockchain.chain), 2)
        self.assertEqual(len(self.plugin.blockchain.pending_transactions), 0)
    
    def test_get_audit_trail(self):
        """Test getting audit trail with filtering."""
        # Add and mine some transactions
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Yesterday's transactions
        self.plugin.record_trade({
            "id": "trade_yesterday",
            "symbol": "BTC/USD",
            "timestamp": yesterday.isoformat()
        })
        
        # Today's transactions
        self.plugin.record_trade({
            "id": "trade_today",
            "symbol": "ETH/USD",
            "timestamp": now.isoformat()
        })
        self.plugin.record_order({
            "id": "order_today",
            "symbol": "LTC/USD",
            "timestamp": now.isoformat()
        })
        
        # Mine transactions
        self.plugin.force_mine()
        
        # Get all records
        all_records = self.plugin.get_audit_trail()
        self.assertEqual(len(all_records), 3)
        
        # Filter by type
        trade_records = self.plugin.get_audit_trail(record_type="trade")
        self.assertEqual(len(trade_records), 2)
        
        # Filter by time
        today_records = self.plugin.get_audit_trail(start_time=now.date().isoformat())
        self.assertEqual(len(today_records), 2)
    
    def test_verify_chain_integrity(self):
        """Test verifying chain integrity."""
        # Add and mine some transactions
        self.plugin.record_trade({"id": "trade1", "symbol": "BTC/USD"})
        self.plugin.force_mine()
        
        # Chain should be valid
        self.assertTrue(self.plugin.verify_chain_integrity())
        
        # Tamper with a block
        self.plugin.blockchain.chain[1].data = {"tampered": "data"}
        
        # Chain should be invalid
        self.assertFalse(self.plugin.verify_chain_integrity())
    
    def test_get_chain_stats(self):
        """Test getting chain statistics."""
        # Add and mine some transactions
        self.plugin.record_trade({"id": "trade1", "symbol": "BTC/USD"})
        self.plugin.record_order({"id": "order1", "symbol": "ETH/USD"})
        self.plugin.force_mine()
        
        stats = self.plugin.get_chain_stats()
        
        self.assertEqual(stats["chain_length"], 2)
        self.assertEqual(stats["total_transactions"], 2)
        self.assertEqual(stats["transaction_types"]["trade"], 1)
        self.assertEqual(stats["transaction_types"]["order"], 1)
        self.assertTrue(stats["is_valid"])


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_generate_hash(self):
        """Test hash generation."""
        data = {"test": "data"}
        hash1 = generate_hash(data)
        hash2 = generate_hash(data)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hash length
    
    def test_validate_timestamp(self):
        """Test timestamp validation."""
        valid_timestamp = datetime.now().isoformat()
        invalid_timestamp = "not-a-timestamp"
        
        self.assertTrue(validate_timestamp(valid_timestamp))
        self.assertFalse(validate_timestamp(invalid_timestamp))
    
    def test_get_timestamp(self):
        """Test timestamp generation."""
        timestamp = get_timestamp()
        
        self.assertTrue(validate_timestamp(timestamp))
    
    def test_sanitize_sensitive_data(self):
        """Test sanitization of sensitive data."""
        data = {
            "public": "public_value",
            "password": "secret123",
            "nested": {
                "public": "public_nested",
                "api_key": "secret_api_key"
            },
            "list": [
                {"public": "public_list", "token": "secret_token"},
                {"public": "public_list2"}
            ]
        }
        
        sensitive_fields = ["password", "api_key", "token"]
        
        sanitized = sanitize_sensitive_data(data, sensitive_fields)
        
        self.assertEqual(sanitized["public"], "public_value")
        self.assertEqual(sanitized["password"], "********")
        self.assertEqual(sanitized["nested"]["public"], "public_nested")
        self.assertEqual(sanitized["nested"]["api_key"], "********")
        self.assertEqual(sanitized["list"][0]["public"], "public_list")
        self.assertEqual(sanitized["list"][0]["token"], "********")
        self.assertEqual(sanitized["list"][1]["public"], "public_list2")
    
    def test_filter_transactions_by_criteria(self):
        """Test filtering transactions by criteria."""
        transactions = [
            {
                "type": "trade",
                "timestamp": "2023-01-01T12:00:00",
                "data": {"symbol": "BTC/USD", "side": "buy"}
            },
            {
                "type": "trade",
                "timestamp": "2023-01-02T12:00:00",
                "data": {"symbol": "ETH/USD", "side": "sell"}
            },
            {
                "type": "order",
                "timestamp": "2023-01-02T13:00:00",
                "data": {"symbol": "BTC/USD", "side": "buy"}
            }
        ]
        
        # Filter by type
        type_criteria = {"type": "trade"}
        filtered = filter_transactions_by_criteria(transactions, type_criteria)
        self.assertEqual(len(filtered), 2)
        
        # Filter by time range
        time_criteria = {"start_time": "2023-01-02T00:00:00"}
        filtered = filter_transactions_by_criteria(transactions, time_criteria)
        self.assertEqual(len(filtered), 2)
        
        # Filter by data criteria
        data_criteria = {"data_criteria": {"symbol": "BTC/USD"}}
        filtered = filter_transactions_by_criteria(transactions, data_criteria)
        self.assertEqual(len(filtered), 2)
        
        # Combined criteria
        combined_criteria = {
            "type": "trade",
            "data_criteria": {"symbol": "BTC/USD"}
        }
        filtered = filter_transactions_by_criteria(transactions, combined_criteria)
        self.assertEqual(len(filtered), 1)
    
    def test_generate_audit_report(self):
        """Test generating audit reports."""
        transactions = [
            {
                "type": "trade",
                "timestamp": "2023-01-01T12:00:00",
                "data": {"symbol": "BTC/USD", "side": "buy"}
            },
            {
                "type": "trade",
                "timestamp": "2023-01-02T12:00:00",
                "data": {"symbol": "ETH/USD", "side": "sell"}
            },
            {
                "type": "order",
                "timestamp": "2023-01-02T13:00:00",
                "data": {"symbol": "BTC/USD", "side": "buy"}
            }
        ]
        
        # Summary report
        summary_report = generate_audit_report(transactions, "summary")
        self.assertEqual(summary_report["transaction_count"], 3)
        self.assertEqual(summary_report["transaction_types"]["trade"], 2)
        self.assertEqual(summary_report["transaction_types"]["order"], 1)
        self.assertEqual(summary_report["time_range"]["start"], "2023-01-01T12:00:00")
        self.assertEqual(summary_report["time_range"]["end"], "2023-01-02T13:00:00")
        
        # Detailed report
        detailed_report = generate_audit_report(transactions, "detailed")
        self.assertEqual(detailed_report["transaction_count"], 3)
        self.assertTrue("daily_counts" in detailed_report)
        self.assertTrue("transactions" in detailed_report)
        self.assertEqual(len(detailed_report["transactions"]), 3)


if __name__ == '__main__':
    unittest.main() 