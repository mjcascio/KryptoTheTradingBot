#!/usr/bin/env python3
"""
Send Telegram Message

This script sends a test message to Telegram using hardcoded credentials.
"""

import requests

def send_telegram_message():
    """Send a test message to Telegram"""
    
    # Hardcoded Telegram credentials
    bot_token = "8104386769:AAG8VBEgkA7MLW8Madtk0JFEr7VWNmiOoFY"
    chat_id = "7924393886"
    
    print(f"Using bot token: {bot_token}")
    print(f"Using chat ID: {chat_id}")
    
    # Telegram API URL
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Prepare message
    data = {
        "chat_id": chat_id,
        "text": "This is a test message from KryptoBot"
    }
    
    # Send message
    try:
        print(f"Sending message to {url}")
        response = requests.post(url, data=data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_telegram_message() 