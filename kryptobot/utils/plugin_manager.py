"""
Plugin Manager Module - Enables dynamic loading of trading bot enhancements.

This module provides a framework for loading, managing, and executing plugins
that extend the functionality of the KryptoBot trading system. It allows for
modular development and integration of new features without modifying the core
codebase.
"""

import os
import sys
import importlib
import inspect
import logging
import pkgutil
import yaml
from typing import Dict, List, Any, Optional, Type, Callable
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)

class PluginInterface(ABC):
    """
    Base interface that all plugins must implement.
    
    This abstract class defines the required methods that all plugins
    must implement to be compatible with the plugin system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            str: The name of the plugin
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the version of the plugin.
        
        Returns:
            str: The version of the plugin
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            str: The description of the plugin
        """
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """
        Get the category of the plugin.
        
        Returns:
            str: The category of the plugin (e.g., 'strategy', 'analysis', 'integration')
        """
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with the provided context.
        
        Args:
            context (Dict[str, Any]): Context data for initialization
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
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
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Perform cleanup operations before shutting down the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        pass

class PluginManager:
    """
    Manages the discovery, loading, and execution of plugins.
    
    This class is responsible for discovering, loading, and managing plugins
    that extend the functionality of the KryptoBot trading system.
    
    Attributes:
        plugins (Dict[str, PluginInterface]): Loaded plugins
        plugin_directories (List[str]): Directories to search for plugins
        enabled_plugins (List[str]): Names of enabled plugins
        plugin_configs (Dict[str, Dict[str, Any]]): Configuration for each plugin
    """
    
    def __init__(self, plugin_directories: List[str] = None, config_path: str = None):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_directories (List[str], optional): Directories to search for plugins
            config_path (str, optional): Path to the plugin configuration file
        """
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_directories = plugin_directories or ['plugins']
        self.enabled_plugins: List[str] = []
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # Add plugin directories to Python path
        for directory in self.plugin_directories:
            if os.path.isdir(directory) and directory not in sys.path:
                sys.path.append(directory)
        
        # Load plugin configuration if provided
        if config_path and os.path.exists(config_path):
            self._load_plugin_config(config_path)
        
        logger.info(f"Plugin manager initialized with directories: {self.plugin_directories}")
    
    def _load_plugin_config(self, config_path: str):
        """
        Load plugin configuration from a YAML file.
        
        Args:
            config_path (str): Path to the plugin configuration file
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                
                if not config:
                    logger.warning(f"Empty plugin configuration file: {config_path}")
                    return
                
                if 'enabled_plugins' in config:
                    self.enabled_plugins = config['enabled_plugins']
                
                if 'plugin_configs' in config:
                    self.plugin_configs = config['plugin_configs']
                
                logger.info(f"Loaded plugin configuration from {config_path}")
                logger.debug(f"Enabled plugins: {self.enabled_plugins}")
        
        except Exception as e:
            logger.error(f"Error loading plugin configuration: {e}")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugin directories.
        
        Returns:
            List[str]: Names of discovered plugins
        """
        discovered_plugins = []
        
        for directory in self.plugin_directories:
            if not os.path.isdir(directory):
                logger.warning(f"Plugin directory does not exist: {directory}")
                continue
            
            # Walk through the directory and its subdirectories
            for _, name, ispkg in pkgutil.iter_modules([directory]):
                if ispkg:  # Only consider packages as plugins
                    discovered_plugins.append(name)
        
        logger.info(f"Discovered {len(discovered_plugins)} plugins: {discovered_plugins}")
        return discovered_plugins
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a specific plugin by name.
        
        Args:
            plugin_name (str): Name of the plugin to load
            
        Returns:
            bool: True if the plugin was loaded successfully, False otherwise
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin already loaded: {plugin_name}")
            return True
        
        try:
            # Import the plugin module
            module = importlib.import_module(plugin_name)
            
            # Find plugin classes (classes that implement PluginInterface)
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj is not PluginInterface):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                logger.warning(f"No plugin classes found in module: {plugin_name}")
                return False
            
            # Use the first plugin class found
            plugin_class = plugin_classes[0]
            plugin = plugin_class()
            
            # Initialize the plugin with its configuration
            plugin_config = self.plugin_configs.get(plugin_name, {})
            if not plugin.initialize(plugin_config):
                logger.error(f"Failed to initialize plugin: {plugin_name}")
                return False
            
            # Add the plugin to the loaded plugins
            self.plugins[plugin_name] = plugin
            logger.info(f"Loaded plugin: {plugin_name} (v{plugin.version})")
            return True
        
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def load_plugins(self, plugin_names: List[str] = None) -> int:
        """
        Load multiple plugins by name.
        
        Args:
            plugin_names (List[str], optional): Names of plugins to load.
                If None, load all enabled plugins.
            
        Returns:
            int: Number of plugins successfully loaded
        """
        if plugin_names is None:
            plugin_names = self.enabled_plugins
        
        if not plugin_names:
            logger.warning("No plugins specified to load")
            return 0
        
        loaded_count = 0
        for plugin_name in plugin_names:
            if self.load_plugin(plugin_name):
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} out of {len(plugin_names)} plugins")
        return loaded_count
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin by name.
        
        Args:
            plugin_name (str): Name of the plugin to unload
            
        Returns:
            bool: True if the plugin was unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return False
        
        try:
            # Shutdown the plugin
            plugin = self.plugins[plugin_name]
            if not plugin.shutdown():
                logger.warning(f"Plugin {plugin_name} reported issues during shutdown")
            
            # Remove the plugin
            del self.plugins[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def unload_all_plugins(self) -> int:
        """
        Unload all loaded plugins.
        
        Returns:
            int: Number of plugins successfully unloaded
        """
        if not self.plugins:
            logger.info("No plugins to unload")
            return 0
        
        plugin_names = list(self.plugins.keys())
        unloaded_count = 0
        
        for plugin_name in plugin_names:
            if self.unload_plugin(plugin_name):
                unloaded_count += 1
        
        logger.info(f"Unloaded {unloaded_count} out of {len(plugin_names)} plugins")
        return unloaded_count
    
    def execute_plugin(self, plugin_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a specific plugin with the provided data.
        
        Args:
            plugin_name (str): Name of the plugin to execute
            data (Dict[str, Any]): Input data for the plugin
            
        Returns:
            Optional[Dict[str, Any]]: Output data from the plugin, or None if execution failed
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return None
        
        try:
            plugin = self.plugins[plugin_name]
            result = plugin.execute(data)
            logger.debug(f"Executed plugin: {plugin_name}")
            return result
        
        except Exception as e:
            logger.error(f"Error executing plugin {plugin_name}: {e}")
            return None
    
    def execute_plugins_by_category(self, category: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute all plugins of a specific category with the provided data.
        
        Args:
            category (str): Category of plugins to execute
            data (Dict[str, Any]): Input data for the plugins
            
        Returns:
            List[Dict[str, Any]]: List of output data from the plugins
        """
        results = []
        
        for plugin_name, plugin in self.plugins.items():
            if plugin.category == category:
                try:
                    result = plugin.execute(data)
                    results.append(result)
                    logger.debug(f"Executed plugin: {plugin_name} (category: {category})")
                
                except Exception as e:
                    logger.error(f"Error executing plugin {plugin_name}: {e}")
        
        logger.info(f"Executed {len(results)} plugins in category: {category}")
        return results
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific plugin.
        
        Args:
            plugin_name (str): Name of the plugin
            
        Returns:
            Optional[Dict[str, Any]]: Plugin information, or None if the plugin is not loaded
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return None
        
        plugin = self.plugins[plugin_name]
        return {
            'name': plugin.name,
            'version': plugin.version,
            'description': plugin.description,
            'category': plugin.category
        }
    
    def get_all_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all loaded plugins.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of plugin information
        """
        plugin_info = {}
        
        for plugin_name, plugin in self.plugins.items():
            plugin_info[plugin_name] = {
                'name': plugin.name,
                'version': plugin.version,
                'description': plugin.description,
                'category': plugin.category
            }
        
        return plugin_info
    
    def save_plugin_config(self, config_path: str) -> bool:
        """
        Save the current plugin configuration to a YAML file.
        
        Args:
            config_path (str): Path to save the plugin configuration
            
        Returns:
            bool: True if the configuration was saved successfully, False otherwise
        """
        try:
            config = {
                'enabled_plugins': self.enabled_plugins,
                'plugin_configs': self.plugin_configs
            }
            
            with open(config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            
            logger.info(f"Saved plugin configuration to {config_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving plugin configuration: {e}")
            return False
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin_name (str): Name of the plugin to enable
            
        Returns:
            bool: True if the plugin was enabled successfully, False otherwise
        """
        if plugin_name in self.enabled_plugins:
            logger.warning(f"Plugin already enabled: {plugin_name}")
            return True
        
        self.enabled_plugins.append(plugin_name)
        logger.info(f"Enabled plugin: {plugin_name}")
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin_name (str): Name of the plugin to disable
            
        Returns:
            bool: True if the plugin was disabled successfully, False otherwise
        """
        if plugin_name not in self.enabled_plugins:
            logger.warning(f"Plugin not enabled: {plugin_name}")
            return True
        
        self.enabled_plugins.remove(plugin_name)
        
        # Unload the plugin if it's loaded
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)
        
        logger.info(f"Disabled plugin: {plugin_name}")
        return True
    
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        Set the configuration for a plugin.
        
        Args:
            plugin_name (str): Name of the plugin
            config (Dict[str, Any]): Configuration for the plugin
            
        Returns:
            bool: True if the configuration was set successfully, False otherwise
        """
        self.plugin_configs[plugin_name] = config
        
        # Update the configuration of the plugin if it's loaded
        if plugin_name in self.plugins:
            try:
                plugin = self.plugins[plugin_name]
                if not plugin.initialize(config):
                    logger.warning(f"Failed to reinitialize plugin with new configuration: {plugin_name}")
                    return False
            
            except Exception as e:
                logger.error(f"Error updating plugin configuration for {plugin_name}: {e}")
                return False
        
        logger.info(f"Set configuration for plugin: {plugin_name}")
        return True
    
    def get_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a plugin.
        
        Args:
            plugin_name (str): Name of the plugin
            
        Returns:
            Optional[Dict[str, Any]]: Configuration for the plugin, or None if not found
        """
        return self.plugin_configs.get(plugin_name)
    
    def register_hook(self, hook_name: str, plugin_name: str, callback: Callable) -> bool:
        """
        Register a plugin hook.
        
        Args:
            hook_name (str): Name of the hook
            plugin_name (str): Name of the plugin
            callback (Callable): Callback function to execute when the hook is triggered
            
        Returns:
            bool: True if the hook was registered successfully, False otherwise
        """
        # This is a placeholder for a more sophisticated hook system
        # In a real implementation, you would store the hooks and provide a way to trigger them
        logger.info(f"Registered hook {hook_name} for plugin {plugin_name}")
        return True 