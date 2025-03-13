"""
Unit tests for the plugin system.
"""

import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kryptobot.utils.plugin_manager import PluginInterface, PluginManager

class MockPlugin(PluginInterface):
    """Mock plugin for testing."""
    
    def __init__(self):
        self._name = "Mock Plugin"
        self._version = "0.1.0"
        self._description = "Mock plugin for testing"
        self._category = "test"
        self._initialized = False
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def category(self) -> str:
        return self._category
    
    def initialize(self, context):
        self._initialized = True
        return True
    
    def execute(self, data):
        if not self._initialized:
            return {"error": "Plugin not initialized"}
        return {"result": "success", "data": data}
    
    def shutdown(self):
        self._initialized = False
        return True

class TestPluginSystem(unittest.TestCase):
    """Test cases for the plugin system."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for the plugin configuration
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, 'plugins.yaml')
        
        # Create a plugin configuration file
        config = {
            'enabled_plugins': ['mock_plugin'],
            'plugin_configs': {
                'mock_plugin': {
                    'option1': 'value1',
                    'option2': 'value2'
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f)
    
    def tearDown(self):
        """Clean up the test environment."""
        self.temp_dir.cleanup()
    
    @patch('importlib.import_module')
    def test_plugin_manager_initialization(self, mock_import_module):
        """Test plugin manager initialization."""
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Check that the plugin manager was initialized correctly
        self.assertEqual(plugin_manager.plugin_directories, ['plugins'])
        self.assertEqual(plugin_manager.enabled_plugins, ['mock_plugin'])
        self.assertEqual(
            plugin_manager.plugin_configs,
            {
                'mock_plugin': {
                    'option1': 'value1',
                    'option2': 'value2'
                }
            }
        )
    
    @patch('importlib.import_module')
    @patch('pkgutil.iter_modules')
    def test_discover_plugins(self, mock_iter_modules, mock_import_module):
        """Test plugin discovery."""
        # Mock the iter_modules function to return a list of plugins
        mock_iter_modules.return_value = [
            (None, 'mock_plugin', True),
            (None, 'not_a_plugin', False)
        ]
        
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Discover plugins
        discovered_plugins = plugin_manager.discover_plugins()
        
        # Check that the correct plugins were discovered
        self.assertEqual(discovered_plugins, ['mock_plugin'])
    
    @patch('importlib.import_module')
    def test_load_plugin(self, mock_import_module):
        """Test plugin loading."""
        # Mock the import_module function to return a module with a MockPlugin class
        mock_module = MagicMock()
        mock_module.MockPlugin = MockPlugin
        mock_import_module.return_value = mock_module
        
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Load a plugin
        result = plugin_manager.load_plugin('mock_plugin')
        
        # Check that the plugin was loaded successfully
        self.assertTrue(result)
        self.assertIn('mock_plugin', plugin_manager.plugins)
        self.assertIsInstance(plugin_manager.plugins['mock_plugin'], MockPlugin)
    
    @patch('importlib.import_module')
    def test_execute_plugin(self, mock_import_module):
        """Test plugin execution."""
        # Mock the import_module function to return a module with a MockPlugin class
        mock_module = MagicMock()
        mock_module.MockPlugin = MockPlugin
        mock_import_module.return_value = mock_module
        
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Load a plugin
        plugin_manager.load_plugin('mock_plugin')
        
        # Execute the plugin
        data = {'test': 'data'}
        result = plugin_manager.execute_plugin('mock_plugin', data)
        
        # Check that the plugin was executed successfully
        self.assertEqual(result, {'result': 'success', 'data': data})
    
    @patch('importlib.import_module')
    def test_execute_plugins_by_category(self, mock_import_module):
        """Test execution of plugins by category."""
        # Mock the import_module function to return a module with a MockPlugin class
        mock_module = MagicMock()
        mock_module.MockPlugin = MockPlugin
        mock_import_module.return_value = mock_module
        
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Load a plugin
        plugin_manager.load_plugin('mock_plugin')
        
        # Execute plugins by category
        data = {'test': 'data'}
        results = plugin_manager.execute_plugins_by_category('test', data)
        
        # Check that the plugins were executed successfully
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], {'result': 'success', 'data': data})
    
    @patch('importlib.import_module')
    def test_unload_plugin(self, mock_import_module):
        """Test plugin unloading."""
        # Mock the import_module function to return a module with a MockPlugin class
        mock_module = MagicMock()
        mock_module.MockPlugin = MockPlugin
        mock_import_module.return_value = mock_module
        
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Load a plugin
        plugin_manager.load_plugin('mock_plugin')
        
        # Unload the plugin
        result = plugin_manager.unload_plugin('mock_plugin')
        
        # Check that the plugin was unloaded successfully
        self.assertTrue(result)
        self.assertNotIn('mock_plugin', plugin_manager.plugins)
    
    @patch('importlib.import_module')
    def test_get_plugin_info(self, mock_import_module):
        """Test getting plugin information."""
        # Mock the import_module function to return a module with a MockPlugin class
        mock_module = MagicMock()
        mock_module.MockPlugin = MockPlugin
        mock_import_module.return_value = mock_module
        
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Load a plugin
        plugin_manager.load_plugin('mock_plugin')
        
        # Get plugin information
        info = plugin_manager.get_plugin_info('mock_plugin')
        
        # Check that the plugin information is correct
        self.assertEqual(info, {
            'name': 'Mock Plugin',
            'version': '0.1.0',
            'description': 'Mock plugin for testing',
            'category': 'test'
        })
    
    @patch('importlib.import_module')
    def test_get_all_plugin_info(self, mock_import_module):
        """Test getting information for all plugins."""
        # Mock the import_module function to return a module with a MockPlugin class
        mock_module = MagicMock()
        mock_module.MockPlugin = MockPlugin
        mock_import_module.return_value = mock_module
        
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Load a plugin
        plugin_manager.load_plugin('mock_plugin')
        
        # Get information for all plugins
        info = plugin_manager.get_all_plugin_info()
        
        # Check that the plugin information is correct
        self.assertEqual(info, {
            'mock_plugin': {
                'name': 'Mock Plugin',
                'version': '0.1.0',
                'description': 'Mock plugin for testing',
                'category': 'test'
            }
        })
    
    @patch('importlib.import_module')
    def test_save_plugin_config(self, mock_import_module):
        """Test saving plugin configuration."""
        # Create a plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=self.config_path
        )
        
        # Modify the plugin configuration
        plugin_manager.enabled_plugins = ['new_plugin']
        plugin_manager.plugin_configs = {
            'new_plugin': {
                'option1': 'new_value1',
                'option2': 'new_value2'
            }
        }
        
        # Save the plugin configuration
        result = plugin_manager.save_plugin_config(self.config_path)
        
        # Check that the configuration was saved successfully
        self.assertTrue(result)
        
        # Load the saved configuration
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check that the configuration was saved correctly
        self.assertEqual(config, {
            'enabled_plugins': ['new_plugin'],
            'plugin_configs': {
                'new_plugin': {
                    'option1': 'new_value1',
                    'option2': 'new_value2'
                }
            }
        })

if __name__ == '__main__':
    unittest.main() 