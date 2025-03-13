#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Kill all existing instances of the trading bot and MetaTrader API bridge
echo "Stopping all existing processes..."
pkill -9 -f "python.*main.py" || true
pkill -9 -f "python.*mt_api_bridge.py" || true
pkill -9 -f "python.*dashboard.py" || true
sleep 2

# Activate virtual environment
source .venv/bin/activate

# Set SSL certificate path
export SSL_CERT_FILE="$PWD/.venv/lib/python3.9/site-packages/certifi/cacert.pem"
export REQUESTS_CA_BUNDLE="$PWD/.venv/lib/python3.9/site-packages/certifi/cacert.pem"
export PYTHONPATH="$PWD:$PYTHONPATH"

# Create a patch for the market_data.py file
cat > market_data_patch.py << 'EOF'
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

# Patch pandas Timestamp.tz_localize
if hasattr(pd.Timestamp, 'tz_localize'):
    original_tz_localize = pd.Timestamp.tz_localize
    
    def patched_tz_localize(self, tz=None, ambiguous='raise', nonexistent='raise'):
        """Patched version of tz_localize that handles None timezone correctly."""
        if tz is None:
            return self
        return original_tz_localize(self, tz, ambiguous, nonexistent)
    
    pd.Timestamp.tz_localize = patched_tz_localize
    logger.info("Successfully patched pandas Timestamp.tz_localize method")
EOF

# Create a patch for the alpaca_broker.py file
cat > alpaca_broker_patch.py << 'EOF'
import os
import certifi
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set SSL certificate path in the environment
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
logger.info(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE', 'Not set')}")
EOF

# Create a wrapper script for the main.py file
cat > run_fixed_bot.py << 'EOF'
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
EOF

# Make the wrapper script executable
chmod +x run_fixed_bot.py

# Start the trading bot using the wrapper script
echo "Starting the trading bot with fixes applied..."
python run_fixed_bot.py 