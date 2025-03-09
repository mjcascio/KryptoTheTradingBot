import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from strategies import TradingStrategy
import pandas as pd
from datetime import datetime, timedelta
import logging

def test_alpaca_connection():
    """Test Alpaca API connection and account access"""
    try:
        api = tradeapi.REST(
            os.getenv('ALPACA_API_KEY'),
            os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL'),
            api_version='v2'
        )
        
        account = api.get_account()
        print("\n=== Alpaca Connection Test ===")
        print(f"✅ Connected to Alpaca API")
        print(f"Account ID: {account.id}")
        print(f"Account Status: {account.status}")
        print(f"Buying Power: ${float(account.buying_power):.2f}")
        return True
    except Exception as e:
        print(f"❌ Alpaca Connection Failed: {str(e)}")
        return False

def test_market_data():
    """Test market data retrieval"""
    try:
        # Initialize API for market data
        api = tradeapi.REST(
            key_id=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url='https://data.alpaca.markets',
            api_version='v2'
        )
        
        # Test with AAPL data
        end = datetime.now()
        
        # Use the correct timeframe format and ensure dates are in the past
        bars = api.get_bars(
            "AAPL",
            timeframe='1Day',
            start='2024-01-01',
            end='2024-03-01',
            adjustment='raw'
        ).df
        
        print("\n=== Market Data Test ===")
        print(f"✅ Successfully retrieved AAPL data")
        print(f"Number of bars: {len(bars)}")
        if not bars.empty:
            print(f"Latest close: ${bars['close'].iloc[-1]:.2f}")
        return True
    except Exception as e:
        print(f"❌ Market Data Test Failed: {str(e)}")
        return False

def test_strategy():
    """Test trading strategy calculations"""
    try:
        # Initialize API for market data
        api = tradeapi.REST(
            key_id=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url='https://data.alpaca.markets',
            api_version='v2'
        )
        
        # Get test data using fixed date range
        bars = api.get_bars(
            "AAPL",
            timeframe='1Day',
            start='2024-01-01',
            end='2024-03-01',
            adjustment='raw'
        ).df
        
        if bars.empty:
            print("❌ No data received for strategy testing")
            return False
            
        strategy = TradingStrategy()
        prob, params = strategy.analyze_trade_opportunity(bars)
        
        print("\n=== Strategy Test ===")
        print(f"✅ Strategy analysis completed")
        print(f"Success Probability: {prob:.2%}")
        print(f"Entry Price: ${params['entry_price']:.2f}")
        print(f"Stop Loss: ${params['stop_loss']:.2f}")
        print(f"Take Profit: ${params['take_profit']:.2f}")
        return True
    except Exception as e:
        print(f"❌ Strategy Test Failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\nRunning KryptoBot Diagnostic Tests...")
    print("=====================================")
    
    # Run all tests
    tests = {
        "Alpaca Connection": test_alpaca_connection,
        "Market Data": test_market_data,
        "Strategy": test_strategy
    }
    
    results = {}
    for name, test_func in tests.items():
        try:
            results[name] = test_func()
        except Exception as e:
            results[name] = False
            print(f"\n❌ {name} test failed with unexpected error: {str(e)}")
    
    # Print summary
    print("\nTest Summary")
    print("===========")
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}") 