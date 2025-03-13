#!/usr/bin/env python3
"""
Wrapper script for the trading bot that applies necessary fixes.
"""

import os
import sys
import pandas as pd
import logging
import certifi
import importlib.util
import types

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set SSL certificate path in the environment
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
logger.info(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE', 'Not set')}")
logger.info(f"REQUESTS_CA_BUNDLE: {os.environ.get('REQUESTS_CA_BUNDLE', 'Not set')}")

# Import the patches
try:
    import market_data_patch
    import alpaca_broker_patch
    logger.info("Successfully imported patches")
except Exception as e:
    logger.error(f"Error importing patches: {e}")

# Import and run the main module
logger.info("Starting the trading bot...")
try:
    # Import the main module
    import main
    logger.info("Successfully imported main module")
except Exception as e:
    logger.error(f"Error importing main module: {e}")
    sys.exit(1)
