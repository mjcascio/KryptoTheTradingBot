#!/usr/bin/env python3
"""
Verification script for KryptoBot setup.
Checks environment variables, connections, and system requirements.
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv
from typing import Dict, List, Tuple
import psutil
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check if all required environment variables are set."""
    required_vars = {
        'ALPACA_API_KEY': 'Alpaca API key',
        'ALPACA_SECRET_KEY': 'Alpaca secret key',
        'TELEGRAM_BOT_TOKEN': 'Telegram bot token',
        'TELEGRAM_CHAT_ID': 'Telegram chat ID',
        'EMAIL_ADDRESS': 'Email address for notifications',
        'EMAIL_PASSWORD': 'Email password',
        'NOTIFICATION_EMAIL': 'Notification recipient email'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{description} ({var})")
    
    return len(missing_vars) == 0, missing_vars

def check_system_requirements() -> Tuple[bool, List[str]]:
    """Check if system meets minimum requirements."""
    issues = []
    
    # Check CPU cores
    cpu_count = psutil.cpu_count()
    if cpu_count < 2:
        issues.append(f"Insufficient CPU cores: {cpu_count} (minimum 2 recommended)")
    
    # Check available memory
    memory = psutil.virtual_memory()
    if memory.available < (2 * 1024 * 1024 * 1024):  # 2GB
        issues.append(f"Insufficient available memory: {memory.available / (1024*1024*1024):.1f}GB (minimum 2GB recommended)")
    
    # Check disk space
    disk = psutil.disk_usage('/')
    if disk.free < (5 * 1024 * 1024 * 1024):  # 5GB
        issues.append(f"Insufficient disk space: {disk.free / (1024*1024*1024):.1f}GB (minimum 5GB recommended)")
    
    return len(issues) == 0, issues

def test_market_data_connection() -> Tuple[bool, str]:
    """Test connection to market data provider."""
    try:
        # Test Yahoo Finance connection
        test_symbol = 'AAPL'
        stock = yf.Ticker(test_symbol)
        info = stock.info
        if not info:
            return False, "Failed to retrieve market data"
        return True, "Market data connection successful"
    except Exception as e:
        return False, f"Market data connection failed: {str(e)}"

def test_telegram_connection() -> Tuple[bool, str]:
    """Test Telegram bot connection."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        return False, "Telegram credentials not configured"
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url)
        if response.status_code == 200:
            return True, "Telegram connection successful"
        return False, f"Telegram connection failed: {response.status_code}"
    except Exception as e:
        return False, f"Telegram connection failed: {str(e)}"

def test_email_connection() -> Tuple[bool, str]:
    """Test email connection."""
    import smtplib
    from email.mime.text import MIMEText
    
    email = os.getenv('EMAIL_ADDRESS')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not email or not password:
        return False, "Email credentials not configured"
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.quit()
        return True, "Email connection successful"
    except Exception as e:
        return False, f"Email connection failed: {str(e)}"

def main():
    """Run all verification checks."""
    logger.info("Starting KryptoBot setup verification...")
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    env_ok, missing_vars = check_environment_variables()
    if not env_ok:
        logger.error("Missing environment variables:")
        for var in missing_vars:
            logger.error(f"- {var}")
    else:
        logger.info("✓ All required environment variables are set")
    
    # Check system requirements
    sys_ok, issues = check_system_requirements()
    if not sys_ok:
        logger.error("System requirement issues:")
        for issue in issues:
            logger.error(f"- {issue}")
    else:
        logger.info("✓ System meets minimum requirements")
    
    # Test market data connection
    market_ok, market_msg = test_market_data_connection()
    if market_ok:
        logger.info(f"✓ {market_msg}")
    else:
        logger.error(f"✗ {market_msg}")
    
    # Test Telegram connection
    telegram_ok, telegram_msg = test_telegram_connection()
    if telegram_ok:
        logger.info(f"✓ {telegram_msg}")
    else:
        logger.error(f"✗ {telegram_msg}")
    
    # Test email connection
    email_ok, email_msg = test_email_connection()
    if email_ok:
        logger.info(f"✓ {email_msg}")
    else:
        logger.error(f"✗ {email_msg}")
    
    # Overall status
    all_ok = env_ok and sys_ok and market_ok and telegram_ok and email_ok
    if all_ok:
        logger.info("\n✓ All checks passed! KryptoBot is ready to run.")
        sys.exit(0)
    else:
        logger.error("\n✗ Some checks failed. Please fix the issues before running KryptoBot.")
        sys.exit(1)

if __name__ == "__main__":
    main() 