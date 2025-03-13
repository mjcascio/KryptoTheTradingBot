"""
Broker Factory Module - Factory for creating broker instances.

This module provides a factory for creating broker instances based on
the platform ID. It abstracts the creation of broker instances and
provides a unified interface for creating brokers.
"""

import logging
from typing import Dict, Optional, Type
import importlib

from kryptobot.brokers.base import BaseBroker

# Configure logging
logger = logging.getLogger(__name__)

class BrokerFactory:
    """
    Factory for creating broker instances.
    
    This class provides a factory for creating broker instances based on
    the platform ID. It abstracts the creation of broker instances and
    provides a unified interface for creating brokers.
    
    Attributes:
        broker_classes (Dict[str, Type[BaseBroker]]): Mapping of platform IDs to broker classes
    """
    
    def __init__(self):
        """
        Initialize the broker factory.
        """
        self.broker_classes = {}
        self._register_default_brokers()
    
    def _register_default_brokers(self):
        """
        Register default broker implementations.
        """
        try:
            # Import broker implementations
            from kryptobot.brokers.alpaca import AlpacaBroker
            self.register_broker('alpaca', AlpacaBroker)
            
            # Try to import MetaTrader broker if available
            try:
                from kryptobot.brokers.metatrader import MetaTraderBroker
                self.register_broker('metatrader', MetaTraderBroker)
                logger.info("Registered MetaTrader broker")
            except ImportError:
                logger.info("MetaTrader broker not available")
            
            logger.info("Registered default brokers")
        except ImportError as e:
            logger.warning(f"Error registering default brokers: {e}")
    
    def register_broker(self, platform_id: str, broker_class: Type[BaseBroker]):
        """
        Register a broker implementation.
        
        Args:
            platform_id (str): Platform ID
            broker_class (Type[BaseBroker]): Broker class
        """
        if not issubclass(broker_class, BaseBroker):
            raise ValueError(f"Broker class {broker_class.__name__} must inherit from BaseBroker")
        
        self.broker_classes[platform_id] = broker_class
        logger.info(f"Registered broker {broker_class.__name__} for platform {platform_id}")
    
    def create_broker(self, platform_id: str, api_key: str, api_secret: str, base_url: str = None) -> Optional[BaseBroker]:
        """
        Create a broker instance.
        
        Args:
            platform_id (str): Platform ID
            api_key (str): API key
            api_secret (str): API secret
            base_url (str, optional): Base URL
            
        Returns:
            Optional[BaseBroker]: Broker instance
            
        Raises:
            ValueError: If the platform ID is not registered
        """
        # Check if the platform ID is registered
        if platform_id not in self.broker_classes:
            # Try to dynamically import the broker class
            try:
                module_name = f"kryptobot.brokers.{platform_id}"
                class_name = f"{platform_id.capitalize()}Broker"
                
                module = importlib.import_module(module_name)
                broker_class = getattr(module, class_name)
                
                self.register_broker(platform_id, broker_class)
                logger.info(f"Dynamically registered broker {class_name} for platform {platform_id}")
            except (ImportError, AttributeError) as e:
                logger.error(f"Error dynamically importing broker for platform {platform_id}: {e}")
                raise ValueError(f"Platform {platform_id} is not registered")
        
        # Create the broker instance
        broker_class = self.broker_classes[platform_id]
        
        try:
            broker = broker_class(api_key, api_secret, base_url)
            logger.info(f"Created broker instance for platform {platform_id}")
            return broker
        except Exception as e:
            logger.error(f"Error creating broker instance for platform {platform_id}: {e}")
            return None
    
    def get_available_platforms(self) -> Dict[str, str]:
        """
        Get available platforms.
        
        Returns:
            Dict[str, str]: Mapping of platform IDs to broker class names
        """
        return {platform_id: broker_class.__name__ for platform_id, broker_class in self.broker_classes.items()} 