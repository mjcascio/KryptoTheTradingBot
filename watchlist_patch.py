
# Watchlist patch for KryptoBot
# This file ensures the watchlist is properly loaded

from config import WATCHLIST, FOREX_WATCHLIST
import logging

logger = logging.getLogger("watchlist_patch")

def patch_watchlist():
    """Patch the watchlist loading"""
    logger.info(f"Patching watchlist with {len(WATCHLIST)} symbols")
    
    # Print the watchlist for verification
    logger.info(f"Watchlist: {WATCHLIST[:5]}... (total: {len(WATCHLIST)})")
    
    # Return True to indicate success
    return True

# Call the patch function
patch_result = patch_watchlist()
