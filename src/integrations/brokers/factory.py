"""Broker factory for creating broker instances."""

from typing import Dict, Any, Type, Optional
from .base import BaseBroker
from .alpaca import AlpacaBroker
import logging

# Configure logging
logger = logging.getLogger(__name__)


class BrokerFactory:
    """Factory class for creating broker instances."""

    def __init__(self):
        """Initialize the broker factory."""
        self._brokers: Dict[str, BaseBroker] = {}
        self._active_broker: Optional[BaseBroker] = None
        self._broker_classes: Dict[str, Type[BaseBroker]] = {
            'alpaca': AlpacaBroker
        }

    def create(self, broker_type: str, config: Dict[str, Any]) -> Optional[BaseBroker]:
        """
        Create a broker instance.

        Args:
            broker_type: Type of broker to create ('alpaca', etc.)
            config: Broker configuration

        Returns:
            BaseBroker: Instance of the specified broker

        Raises:
            ValueError: If broker_type is not supported
        """
        broker_type = broker_type.lower()
        broker_class = self._broker_classes.get(broker_type)
        
        if not broker_class:
            raise ValueError(
                f"Unsupported broker type: {broker_type}. "
                f"Supported types: {list(self._broker_classes.keys())}"
            )

        broker = broker_class(config)
        self._brokers[broker_type] = broker

        # Set as active broker if it's the first one
        if not self._active_broker:
            self._active_broker = broker
            logger.info(f"Set {broker_type} as active broker")

        return broker

    def get_broker(self, broker_type: str) -> Optional[BaseBroker]:
        """
        Get a broker instance by type.

        Args:
            broker_type: Type of broker to get

        Returns:
            Optional[BaseBroker]: The broker instance or None if not found
        """
        return self._brokers.get(broker_type.lower())

    def set_active_broker(self, broker_type: str) -> bool:
        """
        Set the active broker.

        Args:
            broker_type: Type of broker to set as active

        Returns:
            bool: True if successful, False otherwise
        """
        broker_type = broker_type.lower()
        broker = self._brokers.get(broker_type)
        
        if not broker:
            logger.error(f"Cannot set active broker: Broker not found: {broker_type}")
            return False

        self._active_broker = broker
        logger.info(f"Set {broker_type} as active broker")
        return True

    def get_active_broker(self) -> Optional[BaseBroker]:
        """
        Get the currently active broker.

        Returns:
            Optional[BaseBroker]: The active broker or None if no broker is active
        """
        return self._active_broker

    def get_available_brokers(self) -> Dict[str, str]:
        """
        Get available broker types.

        Returns:
            Dict[str, str]: Dictionary of broker types and their class names
        """
        return {
            broker_type: broker_class.__name__
            for broker_type, broker_class in self._broker_classes.items()
        }

    async def connect_all_brokers(self) -> Dict[str, bool]:
        """
        Connect to all available brokers.

        Returns:
            Dict[str, bool]: Dictionary of broker types and their connection status
        """
        results = {}
        for broker_type, broker in self._brokers.items():
            try:
                results[broker_type] = await broker.connect()
            except Exception as e:
                logger.error(f"Error connecting to {broker_type}: {e}")
                results[broker_type] = False
        return results

    async def disconnect_all_brokers(self) -> Dict[str, bool]:
        """
        Disconnect from all brokers.

        Returns:
            Dict[str, bool]: Dictionary of broker types and their disconnection status
        """
        results = {}
        for broker_type, broker in self._brokers.items():
            try:
                await broker.disconnect()
                results[broker_type] = True
            except Exception as e:
                logger.error(f"Error disconnecting from {broker_type}: {e}")
                results[broker_type] = False
        return results