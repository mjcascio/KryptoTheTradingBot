#!/usr/bin/env python3
"""
Telegram Integration Test Script

This script tests the Telegram notification functionality
by sending a test message and verifying the connection.
"""

import os
import logging
from dotenv import load_dotenv
from src.integrations.telegram_notifications import send_telegram_message, send_system_alert


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_telegram():
    """Test Telegram connectivity and notifications."""
    # Load environment variables
    load_dotenv()
    
    # Get Telegram credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Check if credentials are configured
    if not bot_token or bot_token.startswith('your_'):
        logger.error("❌ TELEGRAM_BOT_TOKEN not properly configured")
        return False
    
    if not chat_id:
        logger.error("❌ TELEGRAM_CHAT_ID not configured")
        return False
    
    logger.info("✅ Telegram credentials found")
    
    # Test basic message
    test_message = (
        "🤖 *KryptoBot Test Message*\n\n"
        "This is a test message to verify Telegram integration.\n"
        "If you receive this, the bot can successfully send notifications!"
    )
    
    if send_telegram_message(test_message):
        logger.info("✅ Basic message test passed")
    else:
        logger.error("❌ Failed to send basic message")
        return False
    
    # Test system alerts
    alerts = [
        ("info", "System initialization complete"),
        ("success", "Connection test successful"),
        ("warning", "This is a test warning"),
        ("error", "This is a test error message")
    ]
    
    for alert_type, message in alerts:
        if send_system_alert(alert_type, message):
            logger.info(f"✅ {alert_type.title()} alert test passed")
        else:
            logger.error(f"❌ Failed to send {alert_type} alert")
            return False
    
    logger.info("✅ All Telegram tests completed successfully")
    return True


if __name__ == "__main__":
    test_telegram() 