#!/usr/bin/env python3
"""
Monitor Alpaca Account

This script monitors your Alpaca account in real-time, displaying account information,
positions, and recent orders. It refreshes the data at regular intervals.
"""

import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime
from alpaca_integration import AlpacaIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_currency(value):
    """Format a value as currency"""
    return f"${float(value):.2f}"

def format_percent(value):
    """Format a value as percentage"""
    return f"{float(value) * 100:.2f}%"

def display_account_info(account):
    """Display account information"""
    print("=" * 80)
    print(f"ACCOUNT INFORMATION ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 80)
    
    if not account:
        print("Error: Could not retrieve account information")
        return
    
    print(f"Account ID: {account['id']}")
    print(f"Account Status: {account['status']}")
    print(f"Currency: {account['currency']}")
    print(f"Cash: {format_currency(account['cash'])}")
    print(f"Portfolio Value: {format_currency(account['portfolio_value'])}")
    print(f"Buying Power: {format_currency(account['buying_power'])}")
    
    # Calculate equity change
    equity_change = float(account['equity']) - float(account['last_equity'])
    equity_change_percent = equity_change / float(account['last_equity']) if float(account['last_equity']) > 0 else 0
    
    print(f"Equity: {format_currency(account['equity'])} ({format_currency(equity_change)} / {format_percent(equity_change_percent)} today)")
    
    # Display trading status
    print(f"Trading Blocked: {account['trading_blocked']}")
    print(f"Account Blocked: {account['account_blocked']}")
    print(f"Pattern Day Trader: {account['pattern_day_trader']}")
    print(f"Day Trades Remaining: {account.get('daytrading_buying_power', 'N/A')}")

def display_positions(positions):
    """Display positions"""
    print("\n" + "=" * 80)
    print("POSITIONS")
    print("=" * 80)
    
    if not positions:
        print("No open positions")
        return
    
    # Calculate total unrealized P/L
    total_unrealized_pl = sum(float(position['unrealized_pl']) for position in positions)
    
    # Print header
    print(f"{'Symbol':<6} {'Side':<6} {'Qty':<8} {'Entry':<10} {'Current':<10} {'P/L':<12} {'P/L %':<10} {'Market Value':<12}")
    print("-" * 80)
    
    # Print positions
    for position in positions:
        symbol = position['symbol']
        side = position['side']
        qty = float(position['qty'])
        entry_price = float(position['avg_entry_price'])
        current_price = float(position['current_price'])
        unrealized_pl = float(position['unrealized_pl'])
        unrealized_plpc = float(position['unrealized_plpc'])
        market_value = float(position['market_value'])
        
        print(f"{symbol:<6} {side.upper():<6} {qty:<8.2f} {format_currency(entry_price):<10} {format_currency(current_price):<10} {format_currency(unrealized_pl):<12} {format_percent(unrealized_plpc):<10} {format_currency(market_value):<12}")
    
    # Print total
    print("-" * 80)
    print(f"TOTAL P/L: {format_currency(total_unrealized_pl)}")

def display_orders(orders, limit=5):
    """Display recent orders"""
    print("\n" + "=" * 80)
    print(f"RECENT ORDERS (Last {min(limit, len(orders))})")
    print("=" * 80)
    
    if not orders:
        print("No recent orders")
        return
    
    # Sort orders by created_at (newest first)
    sorted_orders = sorted(orders, key=lambda x: x['created_at'], reverse=True)
    
    # Limit the number of orders to display
    display_orders = sorted_orders[:limit]
    
    # Print header
    print(f"{'ID':<10} {'Symbol':<6} {'Side':<6} {'Qty':<8} {'Type':<10} {'Status':<10} {'Created At':<20}")
    print("-" * 80)
    
    # Print orders
    for order in display_orders:
        order_id = order['id'][:8]  # Truncate ID for display
        symbol = order['symbol']
        side = order['side']
        qty = float(order['qty'])
        order_type = order['type']
        status = order['status']
        created_at = order['created_at'].replace('T', ' ').replace('Z', '')
        
        print(f"{order_id:<10} {symbol:<6} {side.upper():<6} {qty:<8.2f} {order_type:<10} {status:<10} {created_at:<20}")

def monitor_alpaca(refresh_interval=60, display_orders_limit=5):
    """
    Monitor Alpaca account in real-time
    
    Args:
        refresh_interval: Refresh interval in seconds
        display_orders_limit: Number of recent orders to display
    """
    try:
        while True:
            # Clear screen
            clear_screen()
            
            # Get account information
            account = AlpacaIntegration.get_account()
            
            # Get positions
            positions = AlpacaIntegration.get_positions()
            
            # Get orders
            orders = AlpacaIntegration.get_orders(limit=display_orders_limit)
            
            # Display information
            display_account_info(account)
            display_positions(positions)
            display_orders(orders, limit=display_orders_limit)
            
            # Display refresh information
            print(f"\nRefreshing in {refresh_interval} seconds... (Press Ctrl+C to exit)")
            
            # Wait for next refresh
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        logger.error(f"Error monitoring Alpaca account: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Monitor Alpaca account in real-time")
    parser.add_argument("--refresh", type=int, default=60, help="Refresh interval in seconds")
    parser.add_argument("--orders", type=int, default=5, help="Number of recent orders to display")
    
    args = parser.parse_args()
    
    # Monitor Alpaca account
    monitor_alpaca(refresh_interval=args.refresh, display_orders_limit=args.orders)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 