"""
Brokers Package - Broker implementations for various trading platforms.

This package provides broker implementations for various trading platforms,
including Alpaca and MetaTrader. It also provides a factory for creating
broker instances.
"""

from kryptobot.brokers.base import BaseBroker
from kryptobot.brokers.factory import BrokerFactory

# Create a broker factory instance for convenience
broker_factory = BrokerFactory()

# For backward compatibility
def create_broker(platform_id, api_key, api_secret, base_url=None):
    """
    Create a broker instance.
    
    Args:
        platform_id (str): Platform ID
        api_key (str): API key
        api_secret (str): API secret
        base_url (str, optional): Base URL
        
    Returns:
        BaseBroker: Broker instance
    """
    return broker_factory.create_broker(platform_id, api_key, api_secret, base_url)


