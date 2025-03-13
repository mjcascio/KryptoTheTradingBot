#!/usr/bin/env python3
"""
Get Telegram Chat ID

This script helps you get your Telegram chat ID after you've created a bot and sent it a message.
"""

import os
import requests
import time
from dotenv import load_dotenv

def get_chat_id():
    """Get the chat ID for Telegram notifications"""
    
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment or prompt user
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token or bot_token == 'your_new_bot_token_here':
        bot_token = input("Please enter your Telegram bot token: ")
    
    print(f"Using bot token: {bot_token}")
    
    # Test the bot token
    get_me_url = f"https://api.telegram.org/bot{bot_token}/getMe"
    print(f"\nTesting bot token with getMe endpoint: {get_me_url}")
    
    try:
        response = requests.get(get_me_url)
        if response.status_code != 200:
            print(f"Error: Invalid bot token. Status code: {response.status_code}")
            print(f"Response: {response.json()}")
            return
        
        bot_info = response.json()
        print(f"Bot token is valid!")
        print(f"Bot name: {bot_info['result']['first_name']}")
        print(f"Bot username: @{bot_info['result']['username']}")
        
    except Exception as e:
        print(f"Error testing bot token: {e}")
        return
    
    # Get updates to find chat ID
    print("\nGetting updates to find your chat ID...")
    print("If you haven't sent a message to your bot yet, please do so now.")
    
    get_updates_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        # Wait for user to send message
        for i in range(5):
            print(f"Checking for messages... (attempt {i+1}/5)")
            response = requests.get(get_updates_url)
            
            if response.status_code != 200:
                print(f"Error getting updates: {response.json()}")
                time.sleep(2)
                continue
            
            updates = response.json()
            
            if not updates['result']:
                print("No messages found. Please send a message to your bot.")
                time.sleep(3)
                continue
            
            # Find the chat ID
            for update in updates['result']:
                if 'message' in update and 'chat' in update['message']:
                    chat_id = update['message']['chat']['id']
                    print(f"\nFound your chat ID: {chat_id}")
                    print("\nAdd these lines to your .env file:")
                    print(f"TELEGRAM_BOT_TOKEN={bot_token}")
                    print(f"TELEGRAM_CHAT_ID={chat_id}")
                    
                    # Send confirmation message
                    send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = {
                        "chat_id": chat_id,
                        "text": "✅ Chat ID successfully retrieved! You can now receive notifications from KryptoBot."
                    }
                    
                    confirm_response = requests.post(send_message_url, data=data)
                    if confirm_response.status_code == 200:
                        print("\nSent confirmation message to your Telegram.")
                    
                    return
            
            print("No chat ID found in the messages. Please send a message to your bot.")
            time.sleep(3)
        
        print("\nCouldn't find your chat ID after 5 attempts.")
        print("Please make sure you've sent a message to your bot and try again.")
        
    except Exception as e:
        print(f"Error getting chat ID: {e}")

if __name__ == "__main__":
    get_chat_id() 