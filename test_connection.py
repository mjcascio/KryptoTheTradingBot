import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

def test_alpaca_connection():
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize Alpaca API
        api = tradeapi.REST(
            os.getenv('ALPACA_API_KEY'),
            os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL')
        )
        
        # Get account information
        account = api.get_account()
        print("\n=== Alpaca Account Information ===")
        print(f"Account ID: {account.id}")
        print(f"Account Status: {account.status}")
        print(f"Buying Power: ${float(account.buying_power):.2f}")
        print(f"Cash: ${float(account.cash):.2f}")
        print(f"Portfolio Value: ${float(account.portfolio_value):.2f}")
        
        # Test market data access
        print("\n=== Testing Market Data Access ===")
        aapl = api.get_bars("AAPL", "1D", limit=1)
        print(f"AAPL Latest Close: ${float(aapl[0].c):.2f}")
        
        print("\n✅ Connection test successful!")
        return True
        
    except Exception as e:
        print("\n❌ Connection test failed!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_alpaca_connection() 