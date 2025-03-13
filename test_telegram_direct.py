#!/usr/bin/env python3
"""
Test Telegram API Directly

This script tests the Telegram API with the exact token and chat ID.
"""

import requests

def test_telegram_api():
    """Test the Telegram API with the exact token and chat ID"""
    
    # Exact token and chat ID
    bot_token = "8104386769:AAG8VBEgkA7MLW8Madtk0JFEr7VWNmiOoFY"
    chat_id = "7924393886"
    
    print(f"Using bot token: {bot_token}")
    print(f"Using chat ID: {chat_id}")
    
    # Test getMe endpoint
    get_me_url = f"https://api.telegram.org/bot{bot_token}/getMe"
    print(f"\nTesting getMe endpoint: {get_me_url}")
    
    try:
        response = requests.get(get_me_url)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test sendMessage endpoint
    send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    print(f"\nTesting sendMessage endpoint: {send_message_url}")
    
    data = {
        "chat_id": chat_id,
        "text": "This is a test message from KryptoBot"
    }
    
    try:
        response = requests.post(send_message_url, data=data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_telegram_api() 