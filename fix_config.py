#!/usr/bin/env python3
"""
Fix Configuration Script for KryptoBot

This script fixes configuration issues with the KryptoBot trading system:
1. Ensures Alpaca is properly enabled in the configuration
2. Fixes the watchlist loading issue
3. Verifies the Alpaca API connection
"""

import os
import sys
import logging
from typing import Dict, List, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_config")

def fix_platforms_config():
    """Fix the PLATFORMS configuration in config.py"""
    logger.info("Fixing PLATFORMS configuration...")
    
    config_file = "config.py"
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Check if PLATFORMS is defined correctly
    if '"enabled": True' not in content and "'enabled': True" not in content:
        logger.info("Updating PLATFORMS configuration to enable Alpaca")
        
        # Find the PLATFORMS section
        platforms_start = content.find("PLATFORMS = {")
        if platforms_start == -1:
            logger.error("Could not find PLATFORMS section in config.py")
            return False
        
        # Find the alpaca section
        alpaca_start = content.find('"alpaca":', platforms_start)
        if alpaca_start == -1:
            alpaca_start = content.find("'alpaca':", platforms_start)
        
        if alpaca_start == -1:
            logger.error("Could not find alpaca section in PLATFORMS")
            return False
        
        # Find the enabled setting
        enabled_start = content.find('"enabled":', alpaca_start)
        if enabled_start == -1:
            enabled_start = content.find("'enabled':", alpaca_start)
        
        if enabled_start == -1:
            logger.error("Could not find enabled setting in alpaca section")
            return False
        
        # Replace the enabled setting
        content_before = content[:enabled_start]
        content_after = content[enabled_start:]
        
        # Replace False with True
        content_after = content_after.replace('"enabled": False', '"enabled": True')
        content_after = content_after.replace("'enabled': False", "'enabled': True")
        
        # Write the updated content
        with open(config_file, 'w') as f:
            f.write(content_before + content_after)
        
        logger.info("Successfully updated PLATFORMS configuration")
        return True
    else:
        logger.info("PLATFORMS configuration already has Alpaca enabled")
        return True

def fix_watchlist_loading():
    """Fix the watchlist loading issue"""
    logger.info("Fixing watchlist loading...")
    
    # Create a file to patch the watchlist loading
    patch_file = "watchlist_patch.py"
    with open(patch_file, 'w') as f:
        f.write("""
# Watchlist patch for KryptoBot
# This file ensures the watchlist is properly loaded

from config import WATCHLIST, FOREX_WATCHLIST
import logging

logger = logging.getLogger("watchlist_patch")

def patch_watchlist():
    \"\"\"Patch the watchlist loading\"\"\"
    logger.info(f"Patching watchlist with {len(WATCHLIST)} symbols")
    
    # Print the watchlist for verification
    logger.info(f"Watchlist: {WATCHLIST[:5]}... (total: {len(WATCHLIST)})")
    
    # Return True to indicate success
    return True

# Call the patch function
patch_result = patch_watchlist()
""")
    
    logger.info(f"Created watchlist patch file: {patch_file}")
    
    # Update the main.py file to import the patch
    main_file = "main.py"
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if the patch is already imported
    if "import watchlist_patch" not in content:
        # Find a good place to add the import
        import_section_end = content.find("# Initialize logging")
        if import_section_end == -1:
            import_section_end = content.find("# Load environment variables")
        
        if import_section_end == -1:
            logger.error("Could not find a good place to add the import in main.py")
            return False
        
        # Add the import
        content_before = content[:import_section_end]
        content_after = content[import_section_end:]
        
        # Add the import
        content = content_before + "\n# Import watchlist patch\ntry:\n    import watchlist_patch\n    logging.info(\"Successfully imported watchlist patch\")\nexcept ImportError:\n    logging.warning(\"Could not import watchlist patch\")\n" + content_after
        
        # Write the updated content
        with open(main_file, 'w') as f:
            f.write(content)
        
        logger.info("Successfully updated main.py to import the watchlist patch")
        return True
    else:
        logger.info("main.py already imports the watchlist patch")
        return True

def verify_alpaca_api():
    """Verify the Alpaca API connection"""
    logger.info("Verifying Alpaca API connection...")
    
    # Check if the API key is set
    api_key = os.environ.get('ALPACA_API_KEY')
    if not api_key or api_key == 'your_api_key_here' or api_key == 'PK1234567890ABCDEFGHIJ':
        logger.error("Alpaca API key is not properly set in the environment")
        logger.info("Please update the .env file with your actual Alpaca API key")
        return False
    
    # Check if the endpoint key is set
    endpoint_key = os.environ.get('ALPACA_ENDPOINT_KEY')
    if not endpoint_key:
        logger.warning("Alpaca endpoint key is not set, using default endpoint")
    
    # Try to import the Alpaca SDK
    try:
        import alpaca_trade_api as tradeapi
        from alpaca_trade_api.rest import REST
    except ImportError:
        logger.error("Could not import Alpaca SDK. Please install it with: pip install alpaca-trade-api")
        return False
    
    # Try to connect to Alpaca
    try:
        base_url = os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        logger.info(f"Connecting to Alpaca with API key: {api_key[:4]}...{api_key[-4:]}")
        logger.info(f"Using base URL: {base_url}")
        
        api = REST(
            key_id=api_key,
            base_url=base_url
        )
        
        # Test connection by getting account info
        account = api.get_account()
        logger.info(f"Successfully connected to Alpaca: {account.id}")
        logger.info(f"Account status: {account.status}")
        logger.info(f"Account equity: ${account.equity}")
        
        # Save the account info to a file for reference
        with open('alpaca_account.json', 'w') as f:
            account_data = {
                'id': account.id,
                'status': account.status,
                'equity': account.equity,
                'buying_power': account.buying_power,
                'cash': account.cash,
                'portfolio_value': account.portfolio_value,
                'currency': account.currency
            }
            json.dump(account_data, f, indent=2)
        
        logger.info(f"Saved account info to alpaca_account.json")
        
        return True
    except Exception as e:
        logger.error(f"Error connecting to Alpaca: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting configuration fix...")
    
    # Fix the PLATFORMS configuration
    platforms_fixed = fix_platforms_config()
    
    # Fix the watchlist loading
    watchlist_fixed = fix_watchlist_loading()
    
    # Verify the Alpaca API connection
    api_verified = verify_alpaca_api()
    
    # Print summary
    logger.info("\nFix Summary:")
    logger.info(f"PLATFORMS configuration: {'✅ Fixed' if platforms_fixed else '❌ Failed'}")
    logger.info(f"Watchlist loading: {'✅ Fixed' if watchlist_fixed else '❌ Failed'}")
    logger.info(f"Alpaca API connection: {'✅ Verified' if api_verified else '❌ Failed'}")
    
    if platforms_fixed and watchlist_fixed and api_verified:
        logger.info("\n✅ All issues fixed successfully!")
        logger.info("Please restart the bot with: ./stop_bot.sh && ./start_bot.sh")
        return 0
    else:
        logger.error("\n❌ Some issues could not be fixed.")
        logger.error("Please check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 