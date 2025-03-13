"""
Blockchain Audit Plugin - Records trades and system changes in a blockchain ledger.

This plugin provides blockchain-based audit trail capabilities for the KryptoBot trading system.
It records all trades and system changes in a blockchain ledger for enhanced transparency and immutability.
"""

from .blockchain_audit import BlockchainAuditPlugin

__all__ = ['BlockchainAuditPlugin'] 