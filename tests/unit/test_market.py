import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from datetime import datetime
import pytz

def check_market_status():
    # Load environment variables
    load_dotenv()
    
    # Initialize Alpaca API
    api = tradeapi.REST(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY'),
        base_url=os.getenv('ALPACA_BASE_URL')
    )
    
    # Get clock
    clock = api.get_clock()
    
    # Get current time in ET
    et_time = datetime.now(pytz.timezone('America/New_York'))
    
    print(f"\nCurrent time (ET): {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Market is {'OPEN' if clock.is_open else 'CLOSED'}")
    print(f"Next market open: {clock.next_open.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Next market close: {clock.next_close.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    return clock.is_open

if __name__ == "__main__":
    check_market_status() 