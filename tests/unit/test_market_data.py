import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from market_data import MarketDataService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_market_data():
    # Load environment variables
    load_dotenv()
    
    # Initialize Alpaca API
    api = tradeapi.REST(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY'),
        base_url=os.getenv('ALPACA_BASE_URL')
    )
    
    # Initialize market data service
    market_data = MarketDataService(api)
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print("\nTesting Market Data Service:")
    print("============================")
    
    for symbol in symbols:
        print(f"\nTesting {symbol}:")
        
        # Test market data fetching
        data = market_data.get_market_data(symbol, timeframe='15Min', limit=10)
        if data is not None and not data.empty:
            print(f"✅ Successfully fetched market data")
            print(f"Latest close: ${data['close'].iloc[-1]:.2f}")
            print(f"Data points: {len(data)}")
        else:
            print(f"❌ Failed to fetch market data")
            
        # Test current price
        price = market_data.get_current_price(symbol)
        if price is not None:
            print(f"✅ Current price: ${price:.2f}")
        else:
            print(f"❌ Failed to get current price")
    
    # Test market hours
    is_open = market_data.check_market_hours()
    print(f"\nMarket Status: {'🟢 Open' if is_open else '🔴 Closed'}")

if __name__ == "__main__":
    test_market_data() 