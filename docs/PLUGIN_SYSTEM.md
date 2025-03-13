# KryptoBot Plugin System

The KryptoBot Plugin System allows for dynamic loading and execution of plugins that extend the functionality of the KryptoBot trading system. This document provides an overview of the plugin system and instructions for creating and using plugins.

## Overview

The plugin system is designed to be modular and extensible, allowing for the addition of new features without modifying the core codebase. Plugins can be used to add new trading strategies, data sources, analysis techniques, and more.

Key features of the plugin system include:

- Dynamic discovery and loading of plugins
- Configuration management for plugins
- Categorization of plugins for organized execution
- Lifecycle management (initialization, execution, shutdown)
- Error handling and logging

## Plugin Structure

A plugin is a Python package that implements the `PluginInterface` class defined in `kryptobot.utils.plugin_manager`. The package should have the following structure:

```
my_plugin/
├── __init__.py
└── my_plugin.py
```

The `__init__.py` file should export the plugin class:

```python
from .my_plugin import MyPlugin

__all__ = ['MyPlugin']
```

The `my_plugin.py` file should implement the `PluginInterface` class:

```python
from kryptobot.utils.plugin_manager import PluginInterface

class MyPlugin(PluginInterface):
    def __init__(self):
        self._name = "My Plugin"
        self._version = "0.1.0"
        self._description = "My plugin description"
        self._category = "analysis"
    
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
        # Initialize the plugin with the provided context
        return True
    
    def execute(self, data):
        # Execute the plugin's main functionality
        return {"result": "success"}
    
    def shutdown(self):
        # Perform cleanup operations
        return True
```

## Plugin Categories

Plugins are categorized to organize their execution. The following categories are currently supported:

- `strategy`: Trading strategy plugins
- `analysis`: Market analysis plugins
- `data`: Data source plugins
- `integration`: Integration plugins
- `utility`: Utility plugins

## Plugin Configuration

Plugins are configured using a YAML file located at `config/plugins.yaml`. The file has the following structure:

```yaml
# List of enabled plugins
enabled_plugins:
  - my_plugin

# Configuration for each plugin
plugin_configs:
  my_plugin:
    option1: value1
    option2: value2
```

## Using the Plugin System

### Loading Plugins

To load plugins, use the `PluginManager` class:

```python
from kryptobot.utils.plugin_manager import PluginManager

# Initialize plugin manager
plugin_manager = PluginManager(
    plugin_directories=['plugins'],
    config_path='config/plugins.yaml'
)

# Discover available plugins
discovered_plugins = plugin_manager.discover_plugins()

# Load enabled plugins
loaded_count = plugin_manager.load_plugins()
```

### Executing Plugins

To execute a plugin, use the `execute_plugin` method:

```python
# Prepare input data
data = {
    'symbols': ['AAPL', 'MSFT', 'GOOGL']
}

# Execute the plugin
result = plugin_manager.execute_plugin('my_plugin', data)
```

To execute all plugins in a category, use the `execute_plugins_by_category` method:

```python
# Prepare input data
data = {
    'symbols': ['AAPL', 'MSFT', 'GOOGL']
}

# Execute all plugins in the 'analysis' category
results = plugin_manager.execute_plugins_by_category('analysis', data)
```

### Unloading Plugins

To unload a plugin, use the `unload_plugin` method:

```python
# Unload a plugin
plugin_manager.unload_plugin('my_plugin')
```

To unload all plugins, use the `unload_all_plugins` method:

```python
# Unload all plugins
plugin_manager.unload_all_plugins()
```

## Creating a New Plugin

To create a new plugin, follow these steps:

1. Create a new directory in the `plugins` directory with the name of your plugin.
2. Create an `__init__.py` file that exports your plugin class.
3. Create a file with the implementation of your plugin class.
4. Add your plugin to the `config/plugins.yaml` file.

## Example Plugins

The following example plugins are included with KryptoBot:

- `sentiment_analyzer`: Analyzes market sentiment from various sources.

## Testing Plugins

To test a plugin, use the `scripts/test_plugin_system.py` script:

```bash
./scripts/test_plugin_system.py
```

This script demonstrates how to use the plugin system to load and execute plugins.

## Troubleshooting

If you encounter issues with the plugin system, check the following:

- Make sure the plugin directory is in the Python path.
- Make sure the plugin class implements the `PluginInterface` class.
- Make sure the plugin is enabled in the `config/plugins.yaml` file.
- Check the logs for error messages.

## Contributing

To contribute a plugin to KryptoBot, follow these steps:

1. Fork the KryptoBot repository.
2. Create a new branch for your plugin.
3. Create your plugin following the structure described above.
4. Add tests for your plugin.
5. Submit a pull request.

## License

The KryptoBot Plugin System is licensed under the same license as KryptoBot. 