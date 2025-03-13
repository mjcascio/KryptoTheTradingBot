#!/usr/bin/env python
"""
Command-line interface for the Blockchain Audit Trail Plugin.
"""

import argparse
import json
import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from plugins.blockchain_audit.blockchain_audit_plugin import BlockchainAuditPlugin
from plugins.blockchain_audit.utils import (
    format_block_for_display,
    export_blockchain_to_json,
    import_blockchain_from_json,
    filter_transactions_by_criteria,
    generate_audit_report
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('blockchain_audit_cli')

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    default_config = {
        "enabled": True,
        "mining_interval": 300,
        "difficulty": 2,
        "db_path": "data/blockchain/audit_chain.db",
        "auto_mine": True,
        "record_types": ["trade", "order", "system_change", "login", "config_change"]
    }
    
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return {**default_config, **config}
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
    
    return default_config

def initialize_plugin(config: Dict[str, Any] = None) -> BlockchainAuditPlugin:
    """
    Initialize the blockchain audit plugin.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized plugin instance
    """
    if config is None:
        config = load_config()
    
    plugin = BlockchainAuditPlugin(config)
    plugin.initialize()
    return plugin

def print_json(data: Any) -> None:
    """
    Print data as formatted JSON.
    
    Args:
        data: Data to print
    """
    print(json.dumps(data, indent=2))

def handle_get_block(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the get-block command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    if args.index is not None:
        block = plugin.blockchain.get_block_by_index(args.index)
    elif args.hash:
        block = plugin.blockchain.get_block_by_hash(args.hash)
    else:
        logger.error("Either --index or --hash must be specified")
        return
    
    if block:
        formatted = format_block_for_display(block, include_transactions=not args.no_transactions)
        print_json(formatted)
    else:
        logger.error("Block not found")

def handle_get_chain(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the get-chain command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    chain = plugin.blockchain.get_chain()
    
    if args.start_index is not None:
        chain = chain[args.start_index:]
    
    if args.limit is not None:
        chain = chain[:args.limit]
    
    if args.format == 'json':
        if args.output:
            export_blockchain_to_json(chain, args.output)
            logger.info(f"Exported chain to {args.output}")
        else:
            formatted_chain = [
                format_block_for_display(block, include_transactions=not args.no_transactions)
                for block in chain
            ]
            print_json(formatted_chain)
    elif args.format == 'summary':
        print(f"Chain length: {len(chain)} blocks")
        if chain:
            print(f"Genesis block: {datetime.fromtimestamp(chain[0]['timestamp']).isoformat()}")
            print(f"Latest block: {datetime.fromtimestamp(chain[-1]['timestamp']).isoformat()}")
            
            # Count transactions
            tx_count = 0
            for block in chain:
                if "transactions" in block["data"]:
                    tx_count += len(block["data"]["transactions"])
            
            print(f"Total transactions: {tx_count}")

def handle_verify_chain(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the verify-chain command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    is_valid = plugin.verify_chain_integrity()
    
    if is_valid:
        logger.info("Blockchain integrity verified: VALID")
        print({"status": "valid", "message": "Blockchain integrity verified"})
    else:
        logger.error("Blockchain integrity verification FAILED")
        print({"status": "invalid", "message": "Blockchain integrity verification failed"})

def handle_get_stats(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the get-stats command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    stats = plugin.get_chain_stats()
    print_json(stats)

def handle_get_audit_trail(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the get-audit-trail command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    records = plugin.get_audit_trail(
        record_type=args.type,
        start_time=args.start_time,
        end_time=args.end_time,
        limit=args.limit
    )
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(records, f, indent=2)
        logger.info(f"Exported audit trail to {args.output}")
    else:
        print_json(records)

def handle_record_event(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the record-event command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    event_data = {}
    
    # Parse event data from arguments
    if args.data:
        try:
            event_data = json.loads(args.data)
        except json.JSONDecodeError:
            logger.error("Invalid JSON data")
            return
    
    # Parse event data from file
    elif args.data_file:
        try:
            with open(args.data_file, 'r') as f:
                event_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading data file: {str(e)}")
            return
    
    # Record event based on type
    success = False
    if args.type == 'trade':
        success = plugin.record_trade(event_data)
    elif args.type == 'order':
        success = plugin.record_order(event_data)
    elif args.type == 'system_change':
        success = plugin.record_system_change(event_data)
    elif args.type == 'login':
        success = plugin.record_login(event_data)
    elif args.type == 'config_change':
        success = plugin.record_config_change(event_data)
    else:
        logger.error(f"Unknown event type: {args.type}")
        return
    
    if success:
        logger.info(f"Recorded {args.type} event")
        print({"status": "success", "message": f"Recorded {args.type} event"})
    else:
        logger.error(f"Failed to record {args.type} event")
        print({"status": "error", "message": f"Failed to record {args.type} event"})

def handle_force_mine(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the force-mine command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    block = plugin.force_mine()
    
    if block:
        logger.info(f"Mined new block #{block['index']} with hash {block['hash']}")
        print({"status": "success", "block": block})
    else:
        logger.info("No pending transactions to mine")
        print({"status": "info", "message": "No pending transactions to mine"})

def handle_generate_report(args: argparse.Namespace, plugin: BlockchainAuditPlugin) -> None:
    """
    Handle the generate-report command.
    
    Args:
        args: Command-line arguments
        plugin: Plugin instance
    """
    # Get transactions
    transactions = []
    for block in plugin.blockchain.chain:
        if "transactions" in block["data"]:
            for tx in block["data"]["transactions"]:
                tx["block_index"] = block["index"]
                tx["block_hash"] = block["hash"]
                transactions.append(tx)
    
    # Apply filters
    criteria = {}
    if args.type:
        criteria["type"] = args.type
    if args.start_time:
        criteria["start_time"] = args.start_time
    if args.end_time:
        criteria["end_time"] = args.end_time
    
    filtered_transactions = filter_transactions_by_criteria(transactions, criteria)
    
    # Generate report
    report = generate_audit_report(
        filtered_transactions, 
        report_type="detailed" if args.detailed else "summary"
    )
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Generated report saved to {args.output}")
    else:
        print_json(report)

def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='Blockchain Audit Trail CLI')
    parser.add_argument('--config', help='Path to configuration file')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # get-block command
    get_block_parser = subparsers.add_parser('get-block', help='Get a block by index or hash')
    get_block_parser.add_argument('--index', type=int, help='Block index')
    get_block_parser.add_argument('--hash', help='Block hash')
    get_block_parser.add_argument('--no-transactions', action='store_true', help='Exclude transactions from output')
    
    # get-chain command
    get_chain_parser = subparsers.add_parser('get-chain', help='Get the entire blockchain')
    get_chain_parser.add_argument('--start-index', type=int, help='Starting block index')
    get_chain_parser.add_argument('--limit', type=int, help='Maximum number of blocks to return')
    get_chain_parser.add_argument('--format', choices=['json', 'summary'], default='json', help='Output format')
    get_chain_parser.add_argument('--output', help='Output file path')
    get_chain_parser.add_argument('--no-transactions', action='store_true', help='Exclude transactions from output')
    
    # verify-chain command
    subparsers.add_parser('verify-chain', help='Verify the integrity of the blockchain')
    
    # get-stats command
    subparsers.add_parser('get-stats', help='Get blockchain statistics')
    
    # get-audit-trail command
    get_audit_trail_parser = subparsers.add_parser('get-audit-trail', help='Get audit trail records')
    get_audit_trail_parser.add_argument('--type', help='Filter by record type')
    get_audit_trail_parser.add_argument('--start-time', help='Filter by start time (ISO format)')
    get_audit_trail_parser.add_argument('--end-time', help='Filter by end time (ISO format)')
    get_audit_trail_parser.add_argument('--limit', type=int, default=100, help='Maximum number of records to return')
    get_audit_trail_parser.add_argument('--output', help='Output file path')
    
    # record-event command
    record_event_parser = subparsers.add_parser('record-event', help='Record an event in the blockchain')
    record_event_parser.add_argument('--type', required=True, choices=['trade', 'order', 'system_change', 'login', 'config_change'], help='Event type')
    record_event_parser.add_argument('--data', help='Event data as JSON string')
    record_event_parser.add_argument('--data-file', help='Path to JSON file containing event data')
    
    # force-mine command
    subparsers.add_parser('force-mine', help='Force mining of pending transactions')
    
    # generate-report command
    generate_report_parser = subparsers.add_parser('generate-report', help='Generate an audit report')
    generate_report_parser.add_argument('--type', help='Filter by record type')
    generate_report_parser.add_argument('--start-time', help='Filter by start time (ISO format)')
    generate_report_parser.add_argument('--end-time', help='Filter by end time (ISO format)')
    generate_report_parser.add_argument('--detailed', action='store_true', help='Generate detailed report')
    generate_report_parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load configuration and initialize plugin
    config = load_config(args.config)
    plugin = initialize_plugin(config)
    
    # Handle commands
    if args.command == 'get-block':
        handle_get_block(args, plugin)
    elif args.command == 'get-chain':
        handle_get_chain(args, plugin)
    elif args.command == 'verify-chain':
        handle_verify_chain(args, plugin)
    elif args.command == 'get-stats':
        handle_get_stats(args, plugin)
    elif args.command == 'get-audit-trail':
        handle_get_audit_trail(args, plugin)
    elif args.command == 'record-event':
        handle_record_event(args, plugin)
    elif args.command == 'force-mine':
        handle_force_mine(args, plugin)
    elif args.command == 'generate-report':
        handle_generate_report(args, plugin)
    
    # Shutdown plugin
    plugin.shutdown()

if __name__ == '__main__':
    main() 