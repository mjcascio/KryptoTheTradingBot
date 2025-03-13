#!/usr/bin/env python
"""
Test script for the plugin system.

This script demonstrates how to use the plugin system to load and execute plugins.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    try:
        # Import the plugin manager directly
        from kryptobot.utils.plugin_manager import PluginManager
        
        # Initialize plugin manager
        plugin_manager = PluginManager(
            plugin_directories=['plugins'],
            config_path=os.path.join('config', 'plugins.yaml')
        )
        
        # Discover available plugins
        discovered_plugins = plugin_manager.discover_plugins()
        logger.info(f"Discovered plugins: {discovered_plugins}")
        
        # Load enabled plugins
        loaded_count = plugin_manager.load_plugins()
        logger.info(f"Loaded {loaded_count} plugins")
        
        # Get information about loaded plugins
        plugin_info = plugin_manager.get_all_plugin_info()
        logger.info(f"Plugin information: {json.dumps(plugin_info, indent=2)}")
        
        # Execute sentiment analysis plugin
        if 'sentiment_analyzer' in plugin_manager.plugins:
            logger.info("Executing sentiment analysis plugin")
            
            # Prepare input data
            data = {
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
            }
            
            # Execute the plugin
            result = plugin_manager.execute_plugin('sentiment_analyzer', data)
            
            # Print the result
            logger.info(f"Sentiment analysis result: {json.dumps(result, indent=2)}")
        
        # Execute all plugins in the 'analysis' category
        logger.info("Executing all plugins in the 'analysis' category")
        
        # Prepare input data
        data = {
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
        }
        
        # Execute the plugins
        results = plugin_manager.execute_plugins_by_category('analysis', data)
        
        # Print the results
        logger.info(f"Analysis results: {json.dumps(results, indent=2)}")
        
        # Unload all plugins
        unloaded_count = plugin_manager.unload_all_plugins()
        logger.info(f"Unloaded {unloaded_count} plugins")
        
        return 0
    
    except ImportError as e:
        logger.error(f"Error importing plugin manager: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"Error testing plugin system: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 