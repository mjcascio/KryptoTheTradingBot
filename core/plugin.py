"""
Core Plugin Module - Base class for all plugins in the KryptoBot trading system.

This module provides a base class for all plugins in the KryptoBot trading system.
It implements the PluginInterface from kryptobot.utils.plugin_manager and provides
common functionality for all plugins.
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)

class Plugin(ABC):
    """
    Base class for all plugins in the KryptoBot trading system.
    
    This class implements the PluginInterface from kryptobot.utils.plugin_manager
    and provides common functionality for all plugins.
    
    Attributes:
        name (str): Name of the plugin
        version (str): Version of the plugin
        description (str): Description of the plugin
        category (str): Category of the plugin
        config (Dict[str, Any]): Configuration for the plugin
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the plugin.
        
        Args:
            config (Dict[str, Any], optional): Configuration for the plugin
        """
        self._name = "base_plugin"
        self._version = "0.1.0"
        self._description = "Base plugin class"
        self._category = "utility"
        self.config = config or {}
    
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
            str: The category of the plugin (e.g., 'strategy', 'analysis', 'integration')
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
            # Update config with context
            if context:
                self.config.update(context)
            
            logger.info(f"Initialized plugin: {self.name} (v{self.version})")
            return True
        except Exception as e:
            logger.error(f"Error initializing plugin {self.name}: {e}")
            return False
    
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
    
    def shutdown(self) -> bool:
        """
        Perform cleanup operations before shutting down the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        try:
            logger.info(f"Shutting down plugin: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error shutting down plugin {self.name}: {e}")
            return False 