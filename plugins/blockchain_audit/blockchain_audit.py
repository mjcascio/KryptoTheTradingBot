"""
Blockchain Audit Plugin Implementation.

This module implements the BlockchainAuditPlugin class, which provides
blockchain-based audit trail capabilities for the KryptoBot trading system.
"""

import logging
import json
import os
import time
import hashlib
import datetime
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Define the PluginInterface class here to avoid import issues
class PluginInterface(ABC):
    """
    Base interface that all plugins must implement.
    
    This abstract class defines the required methods that all plugins
    must implement to be compatible with the plugin system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            str: The name of the plugin
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the version of the plugin.
        
        Returns:
            str: The version of the plugin
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            str: The description of the plugin
        """
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """
        Get the category of the plugin.
        
        Returns:
            str: The category of the plugin (e.g., 'strategy', 'analysis', 'integration')
        """
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with the provided context.
        
        Args:
            context (Dict[str, Any]): Context data for initialization
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin's main functionality.
        
        Args:
            data (Dict[str, Any]): Input data for the plugin
            
        Returns:
            Dict[str, Any]: Output data from the plugin
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Perform cleanup operations before shutting down the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        pass

class Block:
    """
    Represents a block in the blockchain.
    
    Attributes:
        index (int): Block index
        timestamp (float): Block creation timestamp
        data (Dict[str, Any]): Block data
        previous_hash (str): Hash of the previous block
        hash (str): Hash of the current block
        nonce (int): Nonce used for mining
    """
    
    def __init__(self, index: int, timestamp: float, data: Dict[str, Any], previous_hash: str):
        """
        Initialize a block.
        
        Args:
            index (int): Block index
            timestamp (float): Block creation timestamp
            data (Dict[str, Any]): Block data
            previous_hash (str): Hash of the previous block
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate the hash of the block.
        
        Returns:
            str: Block hash
        """
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int):
        """
        Mine the block with the given difficulty.
        
        Args:
            difficulty (int): Mining difficulty (number of leading zeros)
        """
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the block to a dictionary.
        
        Returns:
            Dict[str, Any]: Block as a dictionary
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'nonce': self.nonce
        }
    
    @classmethod
    def from_dict(cls, block_dict: Dict[str, Any]) -> 'Block':
        """
        Create a block from a dictionary.
        
        Args:
            block_dict (Dict[str, Any]): Block as a dictionary
            
        Returns:
            Block: Block instance
        """
        block = cls(
            block_dict['index'],
            block_dict['timestamp'],
            block_dict['data'],
            block_dict['previous_hash']
        )
        block.hash = block_dict['hash']
        block.nonce = block_dict['nonce']
        
        return block

class Blockchain:
    """
    Represents a blockchain.
    
    Attributes:
        chain (List[Block]): Chain of blocks
        difficulty (int): Mining difficulty
    """
    
    def __init__(self, difficulty: int = 2):
        """
        Initialize a blockchain.
        
        Args:
            difficulty (int, optional): Mining difficulty
        """
        self.chain = []
        self.difficulty = difficulty
        
        # Create genesis block
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """
        Create the genesis block.
        """
        genesis_block = Block(0, time.time(), {'message': 'Genesis Block'}, '0')
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        
        logger.info(f"Genesis block created with hash: {genesis_block.hash}")
    
    def get_latest_block(self) -> Block:
        """
        Get the latest block in the chain.
        
        Returns:
            Block: Latest block
        """
        return self.chain[-1]
    
    def add_block(self, data: Dict[str, Any]) -> Block:
        """
        Add a new block to the chain.
        
        Args:
            data (Dict[str, Any]): Block data
            
        Returns:
            Block: New block
        """
        latest_block = self.get_latest_block()
        new_block = Block(
            latest_block.index + 1,
            time.time(),
            data,
            latest_block.hash
        )
        
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        
        logger.info(f"Block {new_block.index} added to the chain with hash: {new_block.hash}")
        
        return new_block
    
    def is_chain_valid(self) -> bool:
        """
        Check if the chain is valid.
        
        Returns:
            bool: True if the chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if the current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                logger.warning(f"Block {current_block.index} has an invalid hash")
                return False
            
            # Check if the current block's previous hash matches the previous block's hash
            if current_block.previous_hash != previous_block.hash:
                logger.warning(f"Block {current_block.index} has an invalid previous hash")
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the blockchain to a dictionary.
        
        Returns:
            Dict[str, Any]: Blockchain as a dictionary
        """
        return {
            'chain': [block.to_dict() for block in self.chain],
            'difficulty': self.difficulty
        }
    
    @classmethod
    def from_dict(cls, blockchain_dict: Dict[str, Any]) -> 'Blockchain':
        """
        Create a blockchain from a dictionary.
        
        Args:
            blockchain_dict (Dict[str, Any]): Blockchain as a dictionary
            
        Returns:
            Blockchain: Blockchain instance
        """
        blockchain = cls(blockchain_dict['difficulty'])
        blockchain.chain = [Block.from_dict(block_dict) for block_dict in blockchain_dict['chain']]
        
        return blockchain

class BlockchainAuditPlugin(PluginInterface):
    """
    Plugin for recording trades and system changes in a blockchain ledger.
    
    This plugin provides blockchain-based audit trail capabilities for the KryptoBot trading system.
    It records all trades and system changes in a blockchain ledger for enhanced transparency and immutability.
    
    Attributes:
        _name (str): Name of the plugin
        _version (str): Version of the plugin
        _description (str): Description of the plugin
        _category (str): Category of the plugin
        _blockchain (Blockchain): Blockchain instance
        _blockchain_file (str): Path to the blockchain file
        _difficulty (int): Mining difficulty
        _initialized (bool): Whether the plugin is initialized
    """
    
    def __init__(self):
        """
        Initialize the blockchain audit plugin.
        """
        self._name = "Blockchain Audit"
        self._version = "0.1.0"
        self._description = "Records trades and system changes in a blockchain ledger"
        self._category = "audit"
        self._blockchain = None
        self._blockchain_file = "data/blockchain/audit.json"
        self._difficulty = 2
        self._initialized = False
        
        logger.info(f"Blockchain Audit Plugin v{self._version} created")
    
    @property
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            str: The name of the plugin
        """
        return self._name
    
    @property
    def version(self) -> str:
        """
        Get the version of the plugin.
        
        Returns:
            str: The version of the plugin
        """
        return self._version
    
    @property
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            str: The description of the plugin
        """
        return self._description
    
    @property
    def category(self) -> str:
        """
        Get the category of the plugin.
        
        Returns:
            str: The category of the plugin
        """
        return self._category
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with the provided context.
        
        Args:
            context (Dict[str, Any]): Context data for initialization
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Extract configuration from context
            if 'blockchain_file' in context:
                self._blockchain_file = context['blockchain_file']
            
            if 'difficulty' in context:
                self._difficulty = context['difficulty']
            
            # Create blockchain directory if it doesn't exist
            blockchain_dir = os.path.dirname(self._blockchain_file)
            os.makedirs(blockchain_dir, exist_ok=True)
            
            # Load or create blockchain
            self._blockchain = self._load_blockchain()
            
            self._initialized = True
            logger.info(f"Blockchain Audit Plugin initialized with difficulty: {self._difficulty}")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing Blockchain Audit Plugin: {e}")
            return False
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin's main functionality.
        
        Args:
            data (Dict[str, Any]): Input data for the plugin
            
        Returns:
            Dict[str, Any]: Output data from the plugin
        """
        if not self._initialized:
            logger.error("Plugin not initialized")
            return {'error': 'Plugin not initialized'}
        
        try:
            # Extract event data from input
            event_type = data.get('event_type')
            event_data = data.get('event_data', {})
            
            if not event_type:
                logger.warning("No event type provided for blockchain audit")
                return {'error': 'No event type provided'}
            
            # Add timestamp to event data
            event_data['timestamp'] = datetime.datetime.now().isoformat()
            
            # Create block data
            block_data = {
                'event_type': event_type,
                'event_data': event_data
            }
            
            # Add block to blockchain
            new_block = self._blockchain.add_block(block_data)
            
            # Save blockchain
            self._save_blockchain()
            
            # Return the result
            return {
                'success': True,
                'block_index': new_block.index,
                'block_hash': new_block.hash,
                'timestamp': new_block.timestamp
            }
        
        except Exception as e:
            logger.error(f"Error executing Blockchain Audit Plugin: {e}")
            return {'error': str(e)}
    
    def _load_blockchain(self) -> Blockchain:
        """
        Load blockchain from file or create a new one.
        
        Returns:
            Blockchain: Blockchain instance
        """
        if os.path.exists(self._blockchain_file):
            try:
                with open(self._blockchain_file, 'r') as f:
                    blockchain_dict = json.load(f)
                
                blockchain = Blockchain.from_dict(blockchain_dict)
                logger.info(f"Loaded blockchain with {len(blockchain.chain)} blocks")
                
                return blockchain
            
            except Exception as e:
                logger.error(f"Error loading blockchain: {e}")
                logger.info("Creating new blockchain")
        
        # Create new blockchain
        blockchain = Blockchain(self._difficulty)
        logger.info("Created new blockchain")
        
        return blockchain
    
    def _save_blockchain(self) -> bool:
        """
        Save blockchain to file.
        
        Returns:
            bool: True if blockchain was saved successfully, False otherwise
        """
        try:
            blockchain_dict = self._blockchain.to_dict()
            
            with open(self._blockchain_file, 'w') as f:
                json.dump(blockchain_dict, f, indent=2)
            
            logger.info(f"Saved blockchain with {len(self._blockchain.chain)} blocks")
            return True
        
        except Exception as e:
            logger.error(f"Error saving blockchain: {e}")
            return False
    
    def get_block(self, block_index: int) -> Optional[Dict[str, Any]]:
        """
        Get a block by index.
        
        Args:
            block_index (int): Block index
            
        Returns:
            Optional[Dict[str, Any]]: Block as a dictionary, or None if not found
        """
        if not self._initialized:
            logger.error("Plugin not initialized")
            return None
        
        try:
            if block_index < 0 or block_index >= len(self._blockchain.chain):
                logger.warning(f"Block index out of range: {block_index}")
                return None
            
            block = self._blockchain.chain[block_index]
            return block.to_dict()
        
        except Exception as e:
            logger.error(f"Error getting block: {e}")
            return None
    
    def get_blocks_by_event_type(self, event_type: str) -> List[Dict[str, Any]]:
        """
        Get blocks by event type.
        
        Args:
            event_type (str): Event type
            
        Returns:
            List[Dict[str, Any]]: List of blocks as dictionaries
        """
        if not self._initialized:
            logger.error("Plugin not initialized")
            return []
        
        try:
            blocks = []
            
            for block in self._blockchain.chain:
                if block.data.get('event_type') == event_type:
                    blocks.append(block.to_dict())
            
            return blocks
        
        except Exception as e:
            logger.error(f"Error getting blocks by event type: {e}")
            return []
    
    def verify_blockchain(self) -> bool:
        """
        Verify the integrity of the blockchain.
        
        Returns:
            bool: True if the blockchain is valid, False otherwise
        """
        if not self._initialized:
            logger.error("Plugin not initialized")
            return False
        
        try:
            return self._blockchain.is_chain_valid()
        
        except Exception as e:
            logger.error(f"Error verifying blockchain: {e}")
            return False
    
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """
        Get blockchain statistics.
        
        Returns:
            Dict[str, Any]: Blockchain statistics
        """
        if not self._initialized:
            logger.error("Plugin not initialized")
            return {'error': 'Plugin not initialized'}
        
        try:
            # Count events by type
            event_counts = {}
            
            for block in self._blockchain.chain:
                event_type = block.data.get('event_type')
                
                if event_type:
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Calculate blockchain size
            blockchain_size = os.path.getsize(self._blockchain_file) if os.path.exists(self._blockchain_file) else 0
            
            return {
                'block_count': len(self._blockchain.chain),
                'event_counts': event_counts,
                'blockchain_size': blockchain_size,
                'is_valid': self._blockchain.is_chain_valid()
            }
        
        except Exception as e:
            logger.error(f"Error getting blockchain stats: {e}")
            return {'error': str(e)}
    
    def shutdown(self) -> bool:
        """
        Perform cleanup operations before shutting down the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        if self._initialized:
            # Save blockchain
            self._save_blockchain()
        
        logger.info("Shutting down Blockchain Audit Plugin")
        return True 