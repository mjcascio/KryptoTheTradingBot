#!/usr/bin/env python
"""
Test script for the sentiment analyzer plugin.

This script demonstrates how to use the sentiment analyzer plugin directly.
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
        # Import the sentiment analyzer plugin
        from plugins.sentiment_analyzer.sentiment_analyzer import SentimentAnalyzerPlugin
        
        # Create the plugin
        plugin = SentimentAnalyzerPlugin()
        logger.info(f"Created plugin: {plugin.name} v{plugin.version}")
        
        # Initialize the plugin
        context = {
            'api_keys': {
                'news_api_key': 'dummy_key',
                'twitter_api_key': 'dummy_key',
                'twitter_api_secret': 'dummy_secret',
                'reddit_client_id': 'dummy_id',
                'reddit_client_secret': 'dummy_secret'
            },
            'cache_dir': 'cache/sentiment',
            'cache_expiry': 3600,
            'sources': ['news', 'twitter', 'reddit']
        }
        
        if plugin.initialize(context):
            logger.info("Plugin initialized successfully")
        else:
            logger.error("Failed to initialize plugin")
            return 1
        
        # Execute the plugin
        data = {
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
        }
        
        result = plugin.execute(data)
        logger.info(f"Sentiment analysis result: {json.dumps(result, indent=2)}")
        
        # Shutdown the plugin
        if plugin.shutdown():
            logger.info("Plugin shutdown successfully")
        else:
            logger.error("Failed to shutdown plugin")
            return 1
        
        return 0
    
    except ImportError as e:
        logger.error(f"Error importing plugin: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"Error testing plugin: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 