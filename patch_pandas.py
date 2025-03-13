import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set SSL certificate path in the environment
os.environ['SSL_CERT_FILE'] = os.path.join(os.path.dirname(__file__), '.venv/lib/python3.9/site-packages/certifi/cacert.pem')
os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(os.path.dirname(__file__), '.venv/lib/python3.9/site-packages/certifi/cacert.pem')

# Check if the tz_localize method exists
if hasattr(pd.Timestamp, 'tz_localize'):
    # Save the original method
    original_tz_localize = pd.Timestamp.tz_localize
    
    # Define a patched method
    def patched_tz_localize(self, tz=None, ambiguous='raise', nonexistent='raise'):
        """Patched version of tz_localize that handles None timezone correctly."""
        if tz is None:
            return self
        return original_tz_localize(self, tz, ambiguous, nonexistent)
    
    # Apply the patch
    pd.Timestamp.tz_localize = patched_tz_localize
    logger.info("Successfully patched pandas Timestamp.tz_localize method")
else:
    logger.warning("pandas Timestamp.tz_localize method not found, no patch applied")

print("Timezone localization patch applied successfully")
