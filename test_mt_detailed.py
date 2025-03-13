#!/usr/bin/env python3
"""
Detailed MetaTrader Connection Test Script

This script performs a comprehensive test of the MetaTrader REST API connection,
checking various ports and endpoints with different authentication methods.
"""

import os
import sys
import requests
import json
import time
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PORTS_TO_TRY = [6789, 5001, 6542, 5555, 5000, 5050, 8080]
AUTH_TOKENS = [
    "KryptKeeperToken2025",  # Current token
    "",                      # No token
    "RestApi"                # Default token
]
MT_ACCOUNT_NUMBER = "5034206028"

def check_port_open(host, port, timeout=1):
    """Check if a port is open using a socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def test_basic_connection(port):
    """Test basic HTTP connection to the port"""
    url = f"http://localhost:{port}"
    try:
        response = requests.get(url, timeout=2)
        print(f"  Basic HTTP connection: ✅ (Status: {response.status_code})")
        print(f"  Response headers: {dict(response.headers)}")
        try:
            print(f"  Response body: {response.text[:200]}...")
        except:
            print("  Could not read response body")
        return True
    except requests.exceptions.ConnectionError:
        print(f"  Basic HTTP connection: ❌ (Connection refused)")
        return False
    except Exception as e:
        print(f"  Basic HTTP connection: ❌ ({str(e)})")
        return False

def test_endpoints(port, auth_token):
    """Test various REST API endpoints"""
    base_url = f"http://localhost:{port}"
    
    # Headers with and without authentication
    headers_with_auth = {
        'Content-Type': 'application/json',
        'X-API-KEY': auth_token
    }
    
    headers_without_auth = {
        'Content-Type': 'application/json'
    }
    
    endpoints = [
        # Standard endpoints
        {"path": "/", "name": "Root", "headers": headers_without_auth},
        {"path": "/connect", "name": "Connect", "headers": headers_with_auth},
        {"path": "/account", "name": "Account", "headers": headers_with_auth},
        
        # Try without authentication
        {"path": "/connect", "name": "Connect (no auth)", "headers": headers_without_auth},
        
        # Alternative endpoints
        {"path": "/api", "name": "API Root", "headers": headers_without_auth},
        {"path": "/api/connect", "name": "API Connect", "headers": headers_with_auth},
        {"path": "/mt5", "name": "MT5 Root", "headers": headers_without_auth},
        {"path": "/mt5/connect", "name": "MT5 Connect", "headers": headers_with_auth}
    ]
    
    success = False
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint['path']}"
        name = endpoint['name']
        headers = endpoint['headers']
        
        try:
            print(f"  Testing {name} ({url})...")
            response = requests.get(url, headers=headers, timeout=3)
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"    ✅ Success!")
                try:
                    data = response.json()
                    print(f"    Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"    Response: {response.text[:200]}...")
                
                success = True
            else:
                print(f"    ❌ Failed with status {response.status_code}")
                print(f"    Response: {response.text[:200]}...")
        
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
    
    return success

def main():
    print("=" * 60)
    print("Detailed MetaTrader Connection Test")
    print("=" * 60)
    
    # First, check which ports are open
    print("\nChecking which ports are open...")
    open_ports = []
    
    for port in PORTS_TO_TRY:
        if check_port_open("localhost", port):
            print(f"Port {port}: ✅ OPEN")
            open_ports.append(port)
        else:
            print(f"Port {port}: ❌ CLOSED")
    
    if not open_ports:
        print("\n❌ No ports are open. Make sure MetaTrader is running with the REST API Expert Advisor.")
        return
    
    # Test each open port
    overall_success = False
    
    for port in open_ports:
        print(f"\n{'-' * 40}")
        print(f"Testing port {port}:")
        print(f"{'-' * 40}")
        
        # Test basic connection
        if not test_basic_connection(port):
            print(f"Skipping further tests for port {port} due to connection failure.")
            continue
        
        # Try different authentication tokens
        for auth_token in AUTH_TOKENS:
            token_display = auth_token if auth_token else "(empty)"
            print(f"\nTrying with Auth-Token: {token_display}")
            
            if test_endpoints(port, auth_token):
                print(f"\n✅ Found working endpoint on port {port} with token '{token_display}'")
                print(f"Update your .env file with:")
                print(f"MT_API_URL=http://localhost:{port}")
                print(f"MT_API_KEY={auth_token}")
                overall_success = True
                break
        
        if overall_success:
            break
    
    print("\n" + "=" * 60)
    if overall_success:
        print("✅ Test completed successfully! Found working configuration.")
    else:
        print("❌ Could not find a working configuration.")
        print("\nTroubleshooting steps:")
        print("1. Make sure MetaTrader is running")
        print("2. Check that the REST API Expert Advisor is attached to a chart")
        print("3. Verify the port and Auth-Token settings in the Expert Advisor")
        print("4. Try restarting MetaTrader")
        print("5. Check for any error messages in the MetaTrader Experts tab")
    print("=" * 60)

if __name__ == "__main__":
    main() 