#!/usr/bin/env python3
"""
MetaTrader Connection Test Script

This script tests the connection to MetaTrader via the REST API bridge.
It attempts to connect and retrieve account information.
"""

import os
import sys
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try different ports commonly used by MetaTrader bridges
PORTS_TO_TRY = [6542, 5555, 5000, 5050, 8080]
MT_API_KEY = "KryptKeeperToken2025"
MT_ACCOUNT_NUMBER = "5034206028"

def test_connection(port):
    """Test connection to MetaTrader REST API"""
    mt_api_url = f"http://localhost:{port}"
    
    print(f"\nTesting connection to MetaTrader REST API at {mt_api_url}")
    print(f"Using API Key: {MT_API_KEY[:4]}{'*' * (len(MT_API_KEY) - 4)}")
    print(f"Account Number: {MT_ACCOUNT_NUMBER}")
    
    # Headers for authentication
    headers = {
        'Content-Type': 'application/json',
        'Auth-Token': MT_API_KEY
    }
    
    try:
        # Test if the server is reachable
        print(f"Checking if port {port} is open...")
        try:
            response = requests.get(mt_api_url, timeout=2)
            print(f"Server is reachable on port {port}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to server on port {port}")
            return False
        
        # Test the connection endpoint
        print(f"Testing /connect endpoint...")
        response = requests.get(f"{mt_api_url}/connect", headers=headers, timeout=5)
        
        print("\nConnection Response:")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Connection successful!")
            print("\nResponse Data:")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
                
            # Try to get account info
            print("\nTrying to get account info...")
            account_response = requests.get(f"{mt_api_url}/account", headers=headers)
            
            if account_response.status_code == 200:
                print("✅ Account info retrieved successfully!")
                print("\nAccount Data:")
                try:
                    print(json.dumps(account_response.json(), indent=2))
                except:
                    print(account_response.text)
            else:
                print(f"❌ Failed to get account info. Status: {account_response.status_code}")
                print(account_response.text)
            
            return True
        else:
            print("❌ Connection failed!")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("MetaTrader Connection Test")
    print("=" * 50)
    
    success = False
    
    for port in PORTS_TO_TRY:
        print(f"\nTrying port {port}...")
        if test_connection(port):
            success = True
            print(f"\n✅ Successfully connected on port {port}")
            print(f"Update your .env file to use MT_API_URL=http://localhost:{port}")
            break
        else:
            print(f"❌ Failed to connect on port {port}")
        
        # Wait a bit before trying the next port
        if port != PORTS_TO_TRY[-1]:
            print("Waiting before trying next port...")
            time.sleep(1)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed on all ports!")
        print("\nPossible issues:")
        print("1. MetaTrader is not running")
        print("2. REST API Expert Advisor is not attached to a chart")
        print("3. The REST API is using a different port")
        print("4. API Key is incorrect")
        print("5. Network/firewall issues")
    print("=" * 50) 