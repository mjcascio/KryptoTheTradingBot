"""
Test script for SMS notifications.

This script tests the SMS notification functionality by sending a test message.
"""

import os
import logging
from dotenv import load_dotenv
from trade_notifications import send_trade_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test SMS notifications."""
    # Load environment variables
    load_dotenv()
    
    # Check if SMS notifications are enabled
    if os.getenv('KRYPTOBOT_SMS_ENABLED', 'false').lower() != 'true':
        logger.error("SMS notifications are not enabled. Please set KRYPTOBOT_SMS_ENABLED=true in .env file.")
        return
    
    # Check if Twilio credentials are configured
    account_sid = os.getenv('KRYPTOBOT_SMS_ACCOUNT_SID')
    auth_token = os.getenv('KRYPTOBOT_SMS_AUTH_TOKEN')
    from_number = os.getenv('KRYPTOBOT_SMS_FROM_NUMBER')
    to_numbers = os.getenv('KRYPTOBOT_SMS_TO_NUMBERS', '')
    
    if not account_sid or not auth_token or not from_number or not to_numbers:
        logger.error("Twilio credentials are not properly configured. Please check your .env file.")
        return
    
    logger.info("Sending test SMS notification...")
    
    # Send a test trade notification
    send_trade_notification(
        symbol="TEST",
        side="buy",
        quantity=100,
        price=123.45,
        strategy="Test Strategy"
    )
    
    logger.info("Test SMS notification sent. Please check your phone.")

if __name__ == "__main__":
    main() 