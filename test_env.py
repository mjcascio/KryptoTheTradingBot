#!/usr/bin/env python3
"""
Test Environment Variables

This script tests if the .env file is being loaded correctly.
"""

import os
from dotenv import load_dotenv

def test_env():
    """Test if the .env file is being loaded correctly"""
    
    # Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_path = os.path.join(os.getcwd(), '.env')
    print(f"Checking if .env file exists at: {env_path}")
    print(f"File exists: {os.path.exists(env_path)}")
    
    # Try to load .env file
    print("\nLoading .env file...")
    load_dotenv(dotenv_path=env_path, override=True)
    
    # Print all environment variables
    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if 'TOKEN' in key or 'CHAT' in key or 'ALPACA' in key:
            # Mask sensitive values
            masked_value = value[:5] + '...' + value[-5:] if len(value) > 10 else '****'
            print(f"{key}: {masked_value}")
    
    # Check specific variables
    print("\nChecking specific variables:")
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', 'Not found')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', 'Not found')
    
    # Mask sensitive values
    masked_token = telegram_bot_token[:5] + '...' + telegram_bot_token[-5:] if len(telegram_bot_token) > 10 else telegram_bot_token
    
    print(f"TELEGRAM_BOT_TOKEN: {masked_token}")
    print(f"TELEGRAM_CHAT_ID: {telegram_chat_id}")
    
    # Try to read the .env file directly
    print("\nReading .env file directly:")
    try:
        with open(env_path, 'r') as f:
            env_contents = f.read()
            
            # Find and print the Telegram-related lines (with masking)
            for line in env_contents.split('\n'):
                if 'TELEGRAM_BOT_TOKEN' in line or 'TELEGRAM_CHAT_ID' in line:
                    # Mask the value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        masked_value = value[:5] + '...' + value[-5:] if len(value) > 10 else value
                        print(f"{key}={masked_value}")
                    else:
                        print(line)
    except Exception as e:
        print(f"Error reading .env file: {e}")

if __name__ == "__main__":
    test_env() 