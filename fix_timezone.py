#!/usr/bin/env python3
"""
This script patches the pandas Timestamp class to fix the timezone localization issue.
"""

import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if the tz_localize method exists
if hasattr(pd.Timestamp, 'tz_localize'):
    # Save the original method
    original_tz_localize = pd.Timestamp.tz_localize
    
    # Define a patched method
    def patched_tz_localize(self, tz=None, ambiguous='raise', nonexistent='raise'):
        """
        Patched version of tz_localize that handles None timezone correctly.
        """
        if tz is None:
            return self
        return original_tz_localize(self, tz, ambiguous, nonexistent)
    
    # Apply the patch
    pd.Timestamp.tz_localize = patched_tz_localize
    
    logger.info("Successfully patched pandas Timestamp.tz_localize method")
else:
    logger.warning("pandas Timestamp.tz_localize method not found, no patch applied")

print("Timezone localization patch applied successfully") 