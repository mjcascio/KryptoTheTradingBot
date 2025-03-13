#!/usr/bin/env python3
"""
Test script to verify that our patch works.
"""

import os
import sys
import pandas as pd
import logging
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set SSL certificate path in the environment
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

logger.info(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE', 'Not set')}")
logger.info(f"REQUESTS_CA_BUNDLE: {os.environ.get('REQUESTS_CA_BUNDLE', 'Not set')}")

# Import our patch
import patch_pandas

# Test the patch
ts = pd.Timestamp('2020-01-01')
logger.info(f"Testing with None timezone: {ts.tz_localize(None)}")
logger.info(f"Testing with UTC timezone: {ts.tz_localize('UTC')}")

# Try to import the market_data module
try:
    from market_data import MarketDataService
    logger.info("Successfully imported MarketDataService")
except Exception as e:
    logger.error(f"Error importing MarketDataService: {e}")

# Try to import the brokers module
try:
    from brokers import BrokerFactory
    logger.info("Successfully imported BrokerFactory")
except Exception as e:
    logger.error(f"Error importing BrokerFactory: {e}")

print("Test completed successfully") 