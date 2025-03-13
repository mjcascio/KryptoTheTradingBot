"""
Blockchain Audit Plugin Integration.

This module provides integration between the Blockchain Audit Plugin and the KryptoBot trading system.
It includes functions for registering event handlers and initializing the plugin.
"""

import logging
import os
import yaml
from typing import Dict, Any, Optional, Callable

# Import the plugin
from plugins.blockchain_audit.blockchain_audit import BlockchainAuditPlugin

# Configure logging
logger = logging.getLogger(__name__)

class BlockchainAuditIntegration:
    """
    Integration class for the Blockchain Audit Plugin.
    
    This class provides methods for integrating the Blockchain Audit Plugin
    with the KryptoBot trading system.
    
    Attributes:
        _plugin (BlockchainAuditPlugin): The blockchain audit plugin instance
        _config (Dict[str, Any]): The plugin configuration
        _event_handlers (Dict[str, Callable]): Registered event handlers
    """
    
    def __init__(self):
        """
        Initialize the blockchain audit integration.
        """
        self._plugin = BlockchainAuditPlugin()
        self._config = {}
        self._event_handlers = {}
        
        logger.info("Blockchain Audit Integration created")
    
    def load_config(self, config_file: str = "plugins/blockchain_audit/config.yaml") -> bool:
        """
        Load the plugin configuration from a YAML file.
        
        Args:
            config_file (str, optional): Path to the configuration file
            
        Returns:
            bool: True if configuration was loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(config_file):
                logger.error(f"Configuration file not found: {config_file}")
                return False
            
            with open(config_file, 'r') as f:
                self._config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def initialize(self) -> bool:
        """
        Initialize the blockchain audit plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            if not self._config:
                logger.error("Configuration not loaded")
                return False
            
            # Extract blockchain configuration
            blockchain_config = self._config.get('blockchain', {})
            
            # Create context for plugin initialization
            context = {
                'blockchain_file': blockchain_config.get('file_path', "data/blockchain/audit.json"),
                'difficulty': blockchain_config.get('difficulty', 2)
            }
            
            # Initialize plugin
            result = self._plugin.initialize(context)
            
            if result:
                logger.info("Blockchain Audit Plugin initialized successfully")
            else:
                logger.error("Failed to initialize Blockchain Audit Plugin")
            
            return result
        
        except Exception as e:
            logger.error(f"Error initializing Blockchain Audit Plugin: {e}")
            return False
    
    def register_event_handlers(self, bot) -> bool:
        """
        Register event handlers with the trading bot.
        
        Args:
            bot: The trading bot instance
            
        Returns:
            bool: True if event handlers were registered successfully, False otherwise
        """
        try:
            # Register event handlers for trading events
            self._register_trading_event_handlers(bot)
            
            # Register event handlers for system events
            self._register_system_event_handlers(bot)
            
            logger.info("Registered event handlers with trading bot")
            return True
        
        except Exception as e:
            logger.error(f"Error registering event handlers: {e}")
            return False
    
    def _register_trading_event_handlers(self, bot) -> None:
        """
        Register event handlers for trading events.
        
        Args:
            bot: The trading bot instance
        """
        # Check if trading events are enabled
        event_types = self._config.get('event_types', {})
        
        # Register order placed handler
        if event_types.get('order_placed', True):
            bot.on_order_placed(self._handle_order_placed)
        
        # Register order cancelled handler
        if event_types.get('order_cancelled', True):
            bot.on_order_cancelled(self._handle_order_cancelled)
        
        # Register trade executed handler
        if event_types.get('trade_executed', True):
            bot.on_trade_executed(self._handle_trade_executed)
        
        # Register position opened handler
        if event_types.get('position_opened', True):
            bot.on_position_opened(self._handle_position_opened)
        
        # Register position closed handler
        if event_types.get('position_closed', True):
            bot.on_position_closed(self._handle_position_closed)
    
    def _register_system_event_handlers(self, bot) -> None:
        """
        Register event handlers for system events.
        
        Args:
            bot: The trading bot instance
        """
        # Check if system events are enabled
        event_types = self._config.get('event_types', {})
        
        # Register system startup handler
        if event_types.get('system_startup', True):
            bot.on_startup(self._handle_system_startup)
        
        # Register system shutdown handler
        if event_types.get('system_shutdown', True):
            bot.on_shutdown(self._handle_system_shutdown)
        
        # Register config changed handler
        if event_types.get('config_changed', True):
            bot.on_config_changed(self._handle_config_changed)
        
        # Register strategy changed handler
        if event_types.get('strategy_changed', True):
            bot.on_strategy_changed(self._handle_strategy_changed)
        
        # Register error occurred handler
        if event_types.get('error_occurred', True):
            bot.on_error(self._handle_error_occurred)
    
    def _handle_order_placed(self, order_data: Dict[str, Any]) -> None:
        """
        Handle order placed event.
        
        Args:
            order_data (Dict[str, Any]): Order data
        """
        self._record_event('order_placed', order_data)
    
    def _handle_order_cancelled(self, order_data: Dict[str, Any]) -> None:
        """
        Handle order cancelled event.
        
        Args:
            order_data (Dict[str, Any]): Order data
        """
        self._record_event('order_cancelled', order_data)
    
    def _handle_trade_executed(self, trade_data: Dict[str, Any]) -> None:
        """
        Handle trade executed event.
        
        Args:
            trade_data (Dict[str, Any]): Trade data
        """
        self._record_event('trade_executed', trade_data)
    
    def _handle_position_opened(self, position_data: Dict[str, Any]) -> None:
        """
        Handle position opened event.
        
        Args:
            position_data (Dict[str, Any]): Position data
        """
        self._record_event('position_opened', position_data)
    
    def _handle_position_closed(self, position_data: Dict[str, Any]) -> None:
        """
        Handle position closed event.
        
        Args:
            position_data (Dict[str, Any]): Position data
        """
        self._record_event('position_closed', position_data)
    
    def _handle_system_startup(self, system_data: Dict[str, Any]) -> None:
        """
        Handle system startup event.
        
        Args:
            system_data (Dict[str, Any]): System data
        """
        self._record_event('system_startup', system_data)
    
    def _handle_system_shutdown(self, system_data: Dict[str, Any]) -> None:
        """
        Handle system shutdown event.
        
        Args:
            system_data (Dict[str, Any]): System data
        """
        self._record_event('system_shutdown', system_data)
    
    def _handle_config_changed(self, config_data: Dict[str, Any]) -> None:
        """
        Handle config changed event.
        
        Args:
            config_data (Dict[str, Any]): Configuration data
        """
        self._record_event('config_changed', config_data)
    
    def _handle_strategy_changed(self, strategy_data: Dict[str, Any]) -> None:
        """
        Handle strategy changed event.
        
        Args:
            strategy_data (Dict[str, Any]): Strategy data
        """
        self._record_event('strategy_changed', strategy_data)
    
    def _handle_error_occurred(self, error_data: Dict[str, Any]) -> None:
        """
        Handle error occurred event.
        
        Args:
            error_data (Dict[str, Any]): Error data
        """
        self._record_event('error_occurred', error_data)
    
    def _record_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Record an event in the blockchain.
        
        Args:
            event_type (str): Event type
            event_data (Dict[str, Any]): Event data
        """
        try:
            # Check if event type is enabled
            event_types = self._config.get('event_types', {})
            if not event_types.get(event_type, True):
                logger.debug(f"Event type {event_type} is disabled, skipping")
                return
            
            # Execute plugin to record event
            result = self._plugin.execute({
                'event_type': event_type,
                'event_data': event_data
            })
            
            if result.get('success'):
                logger.debug(f"Recorded event: {event_type} (Block #{result['block_index']})")
            else:
                logger.error(f"Failed to record event: {event_type} - {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error recording event: {e}")
    
    def get_plugin(self) -> BlockchainAuditPlugin:
        """
        Get the blockchain audit plugin instance.
        
        Returns:
            BlockchainAuditPlugin: The plugin instance
        """
        return self._plugin
    
    def shutdown(self) -> bool:
        """
        Shutdown the blockchain audit plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        try:
            result = self._plugin.shutdown()
            
            if result:
                logger.info("Blockchain Audit Plugin shutdown successfully")
            else:
                logger.error("Failed to shutdown Blockchain Audit Plugin")
            
            return result
        
        except Exception as e:
            logger.error(f"Error shutting down Blockchain Audit Plugin: {e}")
            return False

# Create a singleton instance
blockchain_audit_integration = BlockchainAuditIntegration()

def initialize_blockchain_audit() -> bool:
    """
    Initialize the blockchain audit plugin.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Load configuration
        if not blockchain_audit_integration.load_config():
            logger.error("Failed to load blockchain audit configuration")
            return False
        
        # Initialize plugin
        if not blockchain_audit_integration.initialize():
            logger.error("Failed to initialize blockchain audit plugin")
            return False
        
        logger.info("Blockchain audit initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing blockchain audit: {e}")
        return False

def register_blockchain_audit_handlers(bot) -> bool:
    """
    Register blockchain audit event handlers with the trading bot.
    
    Args:
        bot: The trading bot instance
        
    Returns:
        bool: True if event handlers were registered successfully, False otherwise
    """
    return blockchain_audit_integration.register_event_handlers(bot)

def shutdown_blockchain_audit() -> bool:
    """
    Shutdown the blockchain audit plugin.
    
    Returns:
        bool: True if shutdown was successful, False otherwise
    """
    return blockchain_audit_integration.shutdown()

def get_blockchain_audit_plugin() -> BlockchainAuditPlugin:
    """
    Get the blockchain audit plugin instance.
    
    Returns:
        BlockchainAuditPlugin: The plugin instance
    """
    return blockchain_audit_integration.get_plugin() 