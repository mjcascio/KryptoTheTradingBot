import logging
from typing import Dict, Optional, List

from brokers.base_broker import BaseBroker
from brokers.alpaca_broker import AlpacaBroker
# MetaTrader broker is completely disabled
# from brokers.metatrader_broker import MetaTraderBroker

# Configure logging
logger = logging.getLogger(__name__)

class BrokerFactory:
    """
    Factory class for creating and managing broker instances.
    """
    
    def __init__(self):
        """Initialize the broker factory"""
        self.brokers: Dict[str, BaseBroker] = {}
        self.active_broker: Optional[BaseBroker] = None
    
    def create_broker(self, broker_type: str) -> Optional[BaseBroker]:
        """
        Create a broker instance of the specified type.
        
        Args:
            broker_type: The type of broker to create ('alpaca', 'metatrader')
            
        Returns:
            A broker instance or None if the broker type is not supported
        """
        broker_type = broker_type.lower()
        
        if broker_type == 'alpaca' or broker_type == 'metatrader':
            # Always create Alpaca broker regardless of requested type
            if broker_type == 'metatrader':
                logger.warning("MetaTrader broker is disabled. Using Alpaca instead.")
            broker = AlpacaBroker()
        else:
            logger.error(f"Unsupported broker type: {broker_type}")
            return None
        
        # Store the broker instance as 'alpaca' regardless of requested type
        self.brokers['alpaca'] = broker
        
        # If this is the first broker, set it as active
        if self.active_broker is None:
            self.active_broker = broker
        
        return broker
    
    def get_broker(self, broker_type: str) -> Optional[BaseBroker]:
        """
        Get a broker instance of the specified type.
        If the broker doesn't exist, create it.
        
        Args:
            broker_type: The type of broker to get ('alpaca', 'metatrader')
            
        Returns:
            A broker instance or None if the broker type is not supported
        """
        broker_type = broker_type.lower()
        
        # Always redirect to alpaca
        if broker_type == 'metatrader':
            logger.warning("MetaTrader broker is disabled. Using Alpaca instead.")
            broker_type = 'alpaca'
        
        # If the broker already exists, return it
        if broker_type in self.brokers:
            return self.brokers[broker_type]
        
        # Otherwise, create a new broker
        return self.create_broker(broker_type)
    
    def set_active_broker(self, broker_type: str) -> bool:
        """
        Set the active broker.
        
        Args:
            broker_type: The type of broker to set as active ('alpaca', 'metatrader')
            
        Returns:
            True if the broker was set as active, False otherwise
        """
        broker_type = broker_type.lower()
        
        # Always redirect to alpaca
        if broker_type == 'metatrader':
            logger.warning("MetaTrader broker is disabled. Using Alpaca instead.")
            broker_type = 'alpaca'
        
        # Get the broker (create it if it doesn't exist)
        broker = self.get_broker(broker_type)
        
        if broker is None:
            logger.error(f"Cannot set active broker: Unsupported broker type: {broker_type}")
            return False
        
        # Set the broker as active
        self.active_broker = broker
        logger.info(f"Active broker set to: alpaca")
        
        return True
    
    def get_active_broker(self) -> Optional[BaseBroker]:
        """
        Get the active broker.
        
        Returns:
            The active broker or None if no broker is active
        """
        return self.active_broker
    
    def get_available_brokers(self) -> List[str]:
        """
        Get a list of available broker types.
        
        Returns:
            A list of available broker types
        """
        # Only return alpaca
        return ['alpaca']
    
    def connect_broker(self, broker_type: str) -> bool:
        """
        Connect to a broker.
        
        Args:
            broker_type: The type of broker to connect to ('alpaca', 'metatrader')
            
        Returns:
            True if the connection was successful, False otherwise
        """
        # Always redirect to alpaca
        if broker_type.lower() == 'metatrader':
            logger.warning("MetaTrader broker is disabled. Using Alpaca instead.")
            broker_type = 'alpaca'
            
        broker = self.get_broker(broker_type)
        
        if broker is None:
            logger.error(f"Cannot connect: Unsupported broker type: {broker_type}")
            return False
        
        return broker.connect()
    
    def disconnect_broker(self, broker_type: str) -> bool:
        """
        Disconnect from a broker.
        
        Args:
            broker_type: The type of broker to disconnect from ('alpaca', 'metatrader')
            
        Returns:
            True if the disconnection was successful, False otherwise
        """
        # Always redirect to alpaca
        if broker_type.lower() == 'metatrader':
            logger.warning("MetaTrader broker is disabled. Using Alpaca instead.")
            broker_type = 'alpaca'
            
        if broker_type not in self.brokers:
            logger.warning(f"Cannot disconnect: Broker not found: {broker_type}")
            return False
        
        broker = self.brokers[broker_type]
        return broker.disconnect()
    
    def connect_all_brokers(self) -> Dict[str, bool]:
        """
        Connect to all available brokers.
        
        Returns:
            A dictionary with broker types as keys and connection status as values
        """
        results = {}
        
        # Only connect to alpaca
        if 'alpaca' in self.brokers:
            results['alpaca'] = self.brokers['alpaca'].connect()
        
        return results
    
    def disconnect_all_brokers(self) -> Dict[str, bool]:
        """
        Disconnect from all available brokers.
        
        Returns:
            A dictionary with broker types as keys and disconnection status as values
        """
        results = {}
        
        # Only disconnect from alpaca
        if 'alpaca' in self.brokers:
            results['alpaca'] = self.brokers['alpaca'].disconnect()
        
        return results 