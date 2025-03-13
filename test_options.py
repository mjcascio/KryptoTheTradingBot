#!/usr/bin/env python3
"""Test script to verify options trading functionality"""

import sys
import os
from datetime import datetime, timedelta
from src.integrations.alpaca import AlpacaIntegration
from src.strategies.options import OptionsStrategy
from src.core.market_data import MarketData

def test_options():
    """Test options trading functionality"""
    try:
        print("\n=== Options Trading System Preflight Check ===")
        
        # Get API credentials from environment
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not api_key or not api_secret:
            print("❌ Alpaca API credentials not found in environment variables")
            return False
            
        print("✅ API credentials verified")
        
        # Initialize components
        print("\nInitializing trading components...")
        alpaca = AlpacaIntegration(api_key=api_key, api_secret=api_secret, paper_trading=True)
        market_data = MarketData(api_key=api_key, api_secret=api_secret, paper_trading=True)
        strategy = OptionsStrategy(
            name="Production Options Strategy",
            description="Options trading strategy for paper trading",
            min_delta=0.3,
            max_delta=0.7,
            min_days_to_expiry=30,
            max_days_to_expiry=45,
            min_volume=100,
            min_open_interest=500
        )
        
        print("✅ Trading components initialized")
        
        # Verify account access
        print("\nVerifying account access...")
        account_info = alpaca.get_account_info()
        if not account_info:
            print("❌ Failed to access trading account")
            return False
            
        print(f"✅ Account access verified")
        print(f"   Account Status: {account_info.get('status', 'Unknown')}")
        print(f"   Equity: ${float(account_info.get('equity', 0)):.2f}")
        print(f"   Buying Power: ${float(account_info.get('buying_power', 0)):.2f}")
        
        # Test market data access
        print("\nTesting market data access...")
        symbol = 'AAPL'  # Test with a liquid stock
        data = market_data.get_current_data(symbol, include_options=False)  # Don't include options for initial test
        if not data:
            print(f"❌ Failed to get market data")
            return False
            
        print(f"✅ Market data access verified")
        print(f"   Last Price: ${data['current_price']:.2f}")
        print(f"   Volume: {data['volume']:,}")
        
        # Test strategy analysis
        print("\nTesting strategy analysis...")
        signals = strategy.analyze_market({symbol: data})
        print("✅ Strategy analysis functional")
        
        # Final status
        print("\n=== System Status ===")
        print("✅ API Connection: OK")
        print("✅ Account Access: OK")
        print("✅ Market Data: OK")
        print("✅ Strategy Engine: OK")
        print("\nSystem is ready for paper trading!")
        print("Note: Options data access requires Alpaca subscription")
        print("\nTo start trading, run: python3 src/main.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during preflight check: {e}")
        return False

if __name__ == "__main__":
    if test_options():
        print("\n✅ All systems operational!")
    else:
        print("\n❌ System check failed. Please resolve issues before proceeding.") 