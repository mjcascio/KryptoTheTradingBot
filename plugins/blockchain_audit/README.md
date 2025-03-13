# Blockchain Audit Trail Plugin

A blockchain-based audit trail plugin for the KryptoBot Trading System that provides immutable records of trades, orders, and system changes for regulatory compliance and system integrity verification.

## Features

- **Immutable Audit Trail**: Records trading activities and system changes in a tamper-proof blockchain.
- **Proof of Work**: Uses a simple proof-of-work algorithm to secure the blockchain.
- **Persistent Storage**: Stores blockchain data in an SQLite database for durability.
- **Flexible Record Types**: Supports various record types including trades, orders, system changes, logins, and configuration changes.
- **Comprehensive API**: Provides methods for recording events, retrieving audit trails, and verifying blockchain integrity.
- **Command-Line Interface**: Includes a CLI tool for interacting with the blockchain audit trail.
- **Reporting**: Generates audit reports with filtering capabilities.

## Installation

The plugin is included as part of the KryptoBot Trading System. No additional installation steps are required.

## Configuration

The plugin can be configured through the `config.yaml` file located in the plugin directory. Here's an example configuration:

```yaml
# General plugin settings
enabled: true
name: blockchain_audit
description: "Blockchain-based audit trail for KryptoBot"
version: "1.0.0"
category: audit

# Blockchain settings
mining_interval: 300  # Time in seconds between mining operations (5 minutes)
difficulty: 2  # Number of leading zeros required for proof of work
db_path: "data/blockchain/audit_chain.db"  # Path to SQLite database for blockchain storage
auto_mine: true  # Automatically mine blocks in background

# Record types to include in the blockchain
record_types:
  - trade  # Trading activity
  - order  # Order placement/cancellation
  - system_change  # System configuration changes
  - login  # User login events
  - config_change  # Configuration changes

# Retention settings
max_chain_size: 10000  # Maximum number of blocks to keep (0 for unlimited)
prune_older_than: 0  # Prune blocks older than X days (0 for no pruning)

# Security settings
encrypt_sensitive_data: false  # Whether to encrypt sensitive data in the blockchain
hash_algorithm: "sha256"  # Hash algorithm to use

# API settings
expose_api: true  # Whether to expose blockchain data via API
api_endpoints:
  - get_audit_trail
  - verify_integrity
  - get_stats

# Logging settings
log_level: info  # Logging level (debug, info, warning, error)
log_to_file: true  # Whether to log to a separate file
log_file: "logs/blockchain_audit.log"  # Path to log file
```

## Usage

### Using the Plugin in Code

```python
from plugins.blockchain_audit.blockchain_audit_plugin import BlockchainAuditPlugin

# Initialize the plugin
config = {
    "enabled": True,
    "mining_interval": 300,
    "difficulty": 2,
    "db_path": "data/blockchain/audit_chain.db",
    "auto_mine": True
}
audit_plugin = BlockchainAuditPlugin(config)
audit_plugin.initialize()

# Record a trade
trade_data = {
    "id": "trade123",
    "symbol": "BTC/USD",
    "side": "buy",
    "quantity": 1.5,
    "price": 50000.0,
    "timestamp": "2023-01-01T12:00:00"
}
audit_plugin.record_trade(trade_data)

# Record a system change
change_data = {
    "component": "trading_bot",
    "change_type": "config_update",
    "user": "admin",
    "details": {"parameter": "risk_level", "old_value": "medium", "new_value": "low"}
}
audit_plugin.record_system_change(change_data)

# Force mining of pending transactions
block = audit_plugin.force_mine()
if block:
    print(f"Mined new block #{block['index']} with hash {block['hash']}")

# Get audit trail
records = audit_plugin.get_audit_trail(
    record_type="trade",
    start_time="2023-01-01T00:00:00",
    end_time="2023-01-31T23:59:59",
    limit=100
)

# Verify blockchain integrity
is_valid = audit_plugin.verify_chain_integrity()
print(f"Blockchain integrity: {'Valid' if is_valid else 'Invalid'}")

# Get blockchain statistics
stats = audit_plugin.get_chain_stats()
print(f"Chain length: {stats['chain_length']}")
print(f"Total transactions: {stats['total_transactions']}")

# Shutdown the plugin
audit_plugin.shutdown()
```

### Using the Command-Line Interface

The plugin includes a command-line interface for interacting with the blockchain audit trail:

```bash
# Get help
./plugins/blockchain_audit/cli.py --help

# Get a specific block
./plugins/blockchain_audit/cli.py get-block --index 1

# Get the entire blockchain
./plugins/blockchain_audit/cli.py get-chain --format json

# Verify blockchain integrity
./plugins/blockchain_audit/cli.py verify-chain

# Get blockchain statistics
./plugins/blockchain_audit/cli.py get-stats

# Get audit trail records
./plugins/blockchain_audit/cli.py get-audit-trail --type trade --start-time 2023-01-01T00:00:00 --limit 50

# Record an event
./plugins/blockchain_audit/cli.py record-event --type trade --data '{"id": "trade123", "symbol": "BTC/USD", "side": "buy", "quantity": 1.5, "price": 50000.0}'

# Force mining of pending transactions
./plugins/blockchain_audit/cli.py force-mine

# Generate an audit report
./plugins/blockchain_audit/cli.py generate-report --type trade --start-time 2023-01-01T00:00:00 --detailed --output report.json
```

## Integration with KryptoBot

The plugin integrates with the KryptoBot Trading System through the plugin system. It automatically records trading activities and system changes when enabled.

### Recording Trades

Trades are automatically recorded when the trading bot executes a trade. The following information is recorded:

- Trade ID
- Symbol
- Side (buy/sell)
- Quantity
- Price
- Timestamp
- Order type
- Execution details

### Recording Orders

Orders are automatically recorded when the trading bot places or cancels an order. The following information is recorded:

- Order ID
- Symbol
- Side (buy/sell)
- Quantity
- Price
- Order type
- Status
- Timestamp

### Recording System Changes

System changes are automatically recorded when the trading bot's configuration is modified. The following information is recorded:

- Component
- Change type
- User
- Details (parameters changed, old values, new values)
- Timestamp

## Security Considerations

- The blockchain uses a simple proof-of-work algorithm to secure the chain, but it's not as robust as public blockchains like Bitcoin or Ethereum.
- The blockchain is stored locally, so physical access to the server could potentially allow tampering with the database file.
- Sensitive data can be encrypted, but the encryption key must be properly secured.
- The plugin does not implement a distributed consensus mechanism, so it's not suitable for multi-node deployments without additional security measures.

## Testing

The plugin includes a comprehensive test suite. To run the tests:

```bash
# Run all tests
python -m unittest plugins/blockchain_audit/test_blockchain_audit.py

# Run specific test case
python -m unittest plugins.blockchain_audit.test_blockchain_audit.TestBlockchainAuditPlugin
```

## Dependencies

- Python 3.7+
- SQLite3
- cryptography
- PyYAML

## License

This plugin is part of the KryptoBot Trading System and is subject to the same license terms.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 