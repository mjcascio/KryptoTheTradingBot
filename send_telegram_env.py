#!/usr/bin/env python3
"""
Send Telegram Message Using Environment Variables

This script uses the environment variables to send a Telegram message.
"""

import os
import requests
from dotenv import load_dotenv

def send_telegram_message():
    """Send a Telegram message using environment variables"""
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Get Telegram credentials from environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Mask sensitive values for logging
    masked_token = bot_token[:5] + '...' + bot_token[-5:] if len(bot_token) > 10 else bot_token
    
    print(f"Using bot token: {masked_token}")
    print(f"Using chat ID: {chat_id}")
    
    # Telegram API URL
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Prepare message
    data = {
        "chat_id": chat_id,
        "text": "This is a test message from KryptoBot using environment variables"
    }
    
    # Send message
    try:
        print(f"Sending message to Telegram...")
        response = requests.post(url, data=data)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("Message sent successfully!")
            return True
        else:
            print(f"Error sending message: {response.json()}")
            
            # Provide troubleshooting information based on error code
            if response.status_code == 401:
                print("Unauthorized error: The bot token is invalid or has been revoked.")
                print("Please create a new bot with @BotFather and update your .env file.")
            elif response.status_code == 400:
                print("Bad request: Check if the chat_id is correct.")
            elif response.status_code == 404:
                print("Not found: The API endpoint or method is incorrect.")
            
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_telegram_message() 