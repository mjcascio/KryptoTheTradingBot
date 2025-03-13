#!/usr/bin/env python3
"""Test script to verify Alpaca API connection"""

from src.integrations.alpaca import AlpacaIntegration

def test_connection():
    """Test Alpaca API connection"""
    try:
        # Initialize Alpaca integration with paper trading
        alpaca = AlpacaIntegration(paper_trading=True)
        
        # Get account info
        account = alpaca.get_account_info()
        if account:
            print("\n=== Alpaca Account Info ===")
            print(f"Account Status: {account['status']}")
            print(f"Cash: ${float(account['cash']):,.2f}")
            print(f"Portfolio Value: ${float(account['portfolio_value']):,.2f}")
            print(f"Buying Power: ${float(account['buying_power']):,.2f}")
            print("=========================\n")
            return True
    except Exception as e:
        print(f"\nError connecting to Alpaca: {e}\n")
        return False

if __name__ == "__main__":
    if test_connection():
        print("✅ Successfully connected to Alpaca paper trading account!")
    else:
        print("❌ Failed to connect to Alpaca. Please check your API credentials.") 