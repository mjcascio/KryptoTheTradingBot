#!/usr/bin/env python3
"""Test script to execute a small test trade"""

from src.integrations.alpaca import AlpacaIntegration
import time

def test_trade():
    """Execute a test trade"""
    try:
        # Initialize Alpaca integration with paper trading
        alpaca = AlpacaIntegration(paper_trading=True)
        
        # Get account info before trade
        account_before = alpaca.get_account_info()
        print("\n=== Account Before Trade ===")
        print(f"Cash: ${float(account_before['cash']):,.2f}")
        print(f"Portfolio Value: ${float(account_before['portfolio_value']):,.2f}")
        
        # Place a small test order for AAPL
        symbol = 'AAPL'
        quantity = 1
        print(f"\nPlacing test order: Buy {quantity} share(s) of {symbol}")
        
        order = alpaca.place_market_order(
            symbol=symbol,
            side='buy',
            quantity=quantity
        )
        
        if order:
            print(f"Order placed successfully: {order}")
            
            # Wait for order to fill
            print("Waiting for order to fill...")
            time.sleep(10)
            
            # Get positions
            positions = alpaca.get_positions()
            print("\n=== Current Positions ===")
            for pos in positions:
                print(f"Symbol: {pos['symbol']}")
                print(f"Quantity: {pos['qty']}")
                print(f"Entry Price: ${float(pos['avg_entry_price']):,.2f}")
                print(f"Current Price: ${float(pos['current_price']):,.2f}")
                print(f"P&L: ${float(pos['unrealized_pl']):,.2f}")
            
            # Get account info after trade
            account_after = alpaca.get_account_info()
            print("\n=== Account After Trade ===")
            print(f"Cash: ${float(account_after['cash']):,.2f}")
            print(f"Portfolio Value: ${float(account_after['portfolio_value']):,.2f}")
            
            return True
            
    except Exception as e:
        print(f"\nError executing test trade: {e}")
        return False

if __name__ == "__main__":
    if test_trade():
        print("\n✅ Test trade executed successfully!")
    else:
        print("\n❌ Failed to execute test trade. Please check the error message above.") 