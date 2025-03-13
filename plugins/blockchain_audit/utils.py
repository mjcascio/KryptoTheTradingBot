"""
Utility functions for the Blockchain Audit Trail Plugin.
"""

import json
import hashlib
import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

def generate_hash(data: Any) -> str:
    """
    Generate a SHA-256 hash of the provided data.
    
    Args:
        data: Data to hash (will be converted to JSON if not a string)
        
    Returns:
        Hexadecimal hash string
    """
    if not isinstance(data, str):
        data = json.dumps(data, sort_keys=True)
    
    return hashlib.sha256(data.encode()).hexdigest()

def validate_timestamp(timestamp_str: str) -> bool:
    """
    Validate that a timestamp string is in ISO format.
    
    Args:
        timestamp_str: Timestamp string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.fromisoformat(timestamp_str)
        return True
    except (ValueError, TypeError):
        return False

def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        Current timestamp string
    """
    return datetime.now().isoformat()

def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    Derive a key from a password using PBKDF2.
    
    Args:
        password: Password to derive key from
        salt: Salt for key derivation (generated if None)
        
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_data(data: Dict[str, Any], key: bytes) -> str:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: Data to encrypt
        key: Encryption key
        
    Returns:
        Base64-encoded encrypted data
    """
    f = Fernet(key)
    json_data = json.dumps(data).encode()
    encrypted_data = f.encrypt(json_data)
    return base64.b64encode(encrypted_data).decode()

def decrypt_data(encrypted_data: str, key: bytes) -> Dict[str, Any]:
    """
    Decrypt data using Fernet symmetric encryption.
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        key: Decryption key
        
    Returns:
        Decrypted data as dictionary
    """
    f = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_data)
    decrypted_data = f.decrypt(encrypted_bytes)
    return json.loads(decrypted_data.decode())

def sanitize_sensitive_data(data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
    """
    Sanitize sensitive data by replacing values with asterisks.
    
    Args:
        data: Data to sanitize
        sensitive_fields: List of field names to sanitize
        
    Returns:
        Sanitized data
    """
    sanitized = data.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            if isinstance(sanitized[field], str):
                sanitized[field] = "********"
            elif isinstance(sanitized[field], dict):
                sanitized[field] = sanitize_sensitive_data(sanitized[field], sensitive_fields)
            elif isinstance(sanitized[field], list):
                sanitized[field] = [
                    sanitize_sensitive_data(item, sensitive_fields) if isinstance(item, dict) else item
                    for item in sanitized[field]
                ]
    
    return sanitized

def format_block_for_display(block: Dict[str, Any], include_transactions: bool = True) -> Dict[str, Any]:
    """
    Format a block for display in UI or API responses.
    
    Args:
        block: Block data
        include_transactions: Whether to include transaction details
        
    Returns:
        Formatted block data
    """
    formatted = {
        "index": block["index"],
        "hash": block["hash"],
        "previous_hash": block["previous_hash"],
        "timestamp": datetime.fromtimestamp(block["timestamp"]).isoformat(),
        "nonce": block["nonce"],
    }
    
    if include_transactions and "transactions" in block["data"]:
        formatted["transactions"] = []
        for tx in block["data"]["transactions"]:
            formatted_tx = {
                "type": tx.get("type", "unknown"),
                "timestamp": tx.get("timestamp", "unknown"),
            }
            
            if "data" in tx:
                if tx.get("type") == "trade":
                    trade_data = tx["data"]
                    formatted_tx["symbol"] = trade_data.get("symbol", "unknown")
                    formatted_tx["side"] = trade_data.get("side", "unknown")
                    formatted_tx["quantity"] = trade_data.get("quantity", 0)
                    formatted_tx["price"] = trade_data.get("price", 0)
                elif tx.get("type") == "system_change":
                    formatted_tx["component"] = tx["data"].get("component", "unknown")
                    formatted_tx["change_type"] = tx["data"].get("change_type", "unknown")
            
            formatted["transactions"].append(formatted_tx)
    
    return formatted

def calculate_chain_stats(chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for a blockchain.
    
    Args:
        chain: List of blocks
        
    Returns:
        Dictionary of statistics
    """
    if not chain:
        return {
            "block_count": 0,
            "transaction_count": 0,
            "avg_transactions_per_block": 0,
            "avg_mining_time": 0,
        }
    
    # Count transactions
    transaction_count = 0
    transaction_types = {}
    
    # Calculate mining times
    mining_times = []
    
    for i, block in enumerate(chain):
        if i > 0:  # Skip genesis block
            prev_time = chain[i-1]["timestamp"]
            curr_time = block["timestamp"]
            mining_time = curr_time - prev_time
            mining_times.append(mining_time)
        
        if "transactions" in block["data"]:
            block_txs = block["data"]["transactions"]
            transaction_count += len(block_txs)
            
            for tx in block_txs:
                tx_type = tx.get("type", "unknown")
                transaction_types[tx_type] = transaction_types.get(tx_type, 0) + 1
    
    # Calculate averages
    avg_transactions_per_block = transaction_count / len(chain) if len(chain) > 0 else 0
    avg_mining_time = sum(mining_times) / len(mining_times) if mining_times else 0
    
    # Get time range
    first_block_time = datetime.fromtimestamp(chain[0]["timestamp"]).isoformat() if chain else None
    last_block_time = datetime.fromtimestamp(chain[-1]["timestamp"]).isoformat() if chain else None
    
    return {
        "block_count": len(chain),
        "transaction_count": transaction_count,
        "transaction_types": transaction_types,
        "avg_transactions_per_block": avg_transactions_per_block,
        "avg_mining_time": avg_mining_time,
        "first_block_time": first_block_time,
        "last_block_time": last_block_time,
    }

def export_blockchain_to_json(chain: List[Dict[str, Any]], output_file: str) -> bool:
    """
    Export blockchain to a JSON file.
    
    Args:
        chain: List of blocks
        output_file: Path to output file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(chain, f, indent=2)
        
        logger.info(f"Exported blockchain to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to export blockchain: {str(e)}")
        return False

def import_blockchain_from_json(input_file: str) -> List[Dict[str, Any]]:
    """
    Import blockchain from a JSON file.
    
    Args:
        input_file: Path to input file
        
    Returns:
        List of blocks
    """
    try:
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return []
        
        with open(input_file, 'r') as f:
            chain = json.load(f)
        
        logger.info(f"Imported blockchain from {input_file}")
        return chain
    except Exception as e:
        logger.error(f"Failed to import blockchain: {str(e)}")
        return []

def filter_transactions_by_criteria(transactions: List[Dict[str, Any]], 
                                   criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter transactions by various criteria.
    
    Args:
        transactions: List of transactions
        criteria: Dictionary of filter criteria
        
    Returns:
        Filtered list of transactions
    """
    filtered = transactions
    
    # Filter by type
    if "type" in criteria:
        filtered = [tx for tx in filtered if tx.get("type") == criteria["type"]]
    
    # Filter by time range
    if "start_time" in criteria:
        start_dt = datetime.fromisoformat(criteria["start_time"])
        filtered = [
            tx for tx in filtered 
            if datetime.fromisoformat(tx.get("timestamp", "1970-01-01T00:00:00")) >= start_dt
        ]
    
    if "end_time" in criteria:
        end_dt = datetime.fromisoformat(criteria["end_time"])
        filtered = [
            tx for tx in filtered 
            if datetime.fromisoformat(tx.get("timestamp", "2099-12-31T23:59:59")) <= end_dt
        ]
    
    # Filter by specific fields in data
    if "data_criteria" in criteria:
        for key, value in criteria["data_criteria"].items():
            filtered = [
                tx for tx in filtered 
                if "data" in tx and key in tx["data"] and tx["data"][key] == value
            ]
    
    return filtered

def generate_audit_report(transactions: List[Dict[str, Any]], 
                         report_type: str = "summary") -> Dict[str, Any]:
    """
    Generate an audit report from transactions.
    
    Args:
        transactions: List of transactions
        report_type: Type of report (summary, detailed)
        
    Returns:
        Report data
    """
    if not transactions:
        return {
            "report_type": report_type,
            "generated_at": get_timestamp(),
            "transaction_count": 0,
            "message": "No transactions found"
        }
    
    # Count by type
    type_counts = {}
    for tx in transactions:
        tx_type = tx.get("type", "unknown")
        type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
    
    # Get time range
    timestamps = [datetime.fromisoformat(tx.get("timestamp", "1970-01-01T00:00:00")) 
                 for tx in transactions if "timestamp" in tx]
    
    start_time = min(timestamps).isoformat() if timestamps else None
    end_time = max(timestamps).isoformat() if timestamps else None
    
    report = {
        "report_type": report_type,
        "generated_at": get_timestamp(),
        "transaction_count": len(transactions),
        "transaction_types": type_counts,
        "time_range": {
            "start": start_time,
            "end": end_time
        }
    }
    
    if report_type == "detailed":
        # Group transactions by day
        daily_counts = {}
        for tx in transactions:
            if "timestamp" in tx:
                dt = datetime.fromisoformat(tx["timestamp"])
                day = dt.date().isoformat()
                daily_counts[day] = daily_counts.get(day, 0) + 1
        
        report["daily_counts"] = daily_counts
        
        # Add transaction details (limited to avoid huge reports)
        report["transactions"] = transactions[:100]  # Limit to 100 transactions
        if len(transactions) > 100:
            report["note"] = f"Showing 100 of {len(transactions)} transactions"
    
    return report 