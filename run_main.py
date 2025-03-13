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

# Import and run the main module
import main
