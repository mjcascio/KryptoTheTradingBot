#!/usr/bin/env python3
"""
Send Telegram Message Using curl

This script uses curl to send a Telegram message, which might work differently than requests.
"""

import subprocess
import json

def send_telegram_message_curl():
    """Send a Telegram message using curl"""
    
    # Telegram credentials
    bot_token = "8104386769:AAG8VBEgkA7MLW8Madtk0JFEr7VWNmiOoFY"
    chat_id = "7924393886"
    
    print(f"Using bot token: {bot_token}")
    print(f"Using chat ID: {chat_id}")
    
    # Prepare the curl command
    curl_command = [
        "curl",
        "-s",  # Silent mode
        "-X", "POST",
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        "-d", f"chat_id={chat_id}",
        "-d", "text=This is a test message from KryptoBot using curl"
    ]
    
    print(f"\nExecuting curl command: {' '.join(curl_command)}")
    
    try:
        # Execute the curl command
        result = subprocess.run(curl_command, capture_output=True, text=True)
        
        # Check the result
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Try to parse the JSON response
        try:
            response = json.loads(result.stdout)
            print(f"\nParsed response: {json.dumps(response, indent=2)}")
        except json.JSONDecodeError:
            print("\nCould not parse response as JSON")
        
    except Exception as e:
        print(f"Error executing curl command: {e}")

if __name__ == "__main__":
    send_telegram_message_curl() 