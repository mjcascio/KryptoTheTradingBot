#!/usr/bin/env python3
"""
Test script for options trading functionality.

This script demonstrates how to use the options_trading.py module
to interact with Alpaca's options trading API.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta

# Add parent directory to path to import options_trading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import options trading module
from options_trading import OptionsTrading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_options.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test options trading functionality')
    
    parser.add_argument('--action', type=str, required=True,
                        choices=['chain', 'snapshot', 'find', 'order', 'positions', 'orders', 'multi'],
                        help='Action to perform')
    
    parser.add_argument('--symbol', type=str, default='SPY',
                        help='Symbol for the underlying asset (default: SPY)')
    
    parser.add_argument('--option-symbol', type=str,
                        help='Option symbol for snapshot or order (e.g., SPY230616C00420000)')
    
    parser.add_argument('--expiration', type=str,
                        help='Expiration date in YYYY-MM-DD format')
    
    parser.add_argument('--option-type', type=str, choices=['call', 'put'],
                        help='Option type (call or put)')
    
    parser.add_argument('--strike', type=float,
                        help='Strike price')
    
    parser.add_argument('--qty', type=int, default=1,
                        help='Quantity for order (default: 1)')
    
    parser.add_argument('--side', type=str, choices=['buy', 'sell'],
                        help='Side for order (buy or sell)')
    
    parser.add_argument('--order-type', type=str, default='market',
                        choices=['market', 'limit'],
                        help='Order type (default: market)')
    
    parser.add_argument('--limit-price', type=float,
                        help='Limit price for limit orders')
    
    parser.add_argument('--max-dte', type=int, default=45,
                        help='Maximum days to expiration for finding options (default: 45)')
    
    parser.add_argument('--min-delta', type=float, default=0.3,
                        help='Minimum delta for finding options (default: 0.3)')
    
    parser.add_argument('--max-delta', type=float, default=0.7,
                        help='Maximum delta for finding options (default: 0.7)')
    
    return parser.parse_args()

def get_option_chain(options, args):
    """Get and display option chain."""
    logger.info(f"Getting option chain for {args.symbol}")
    
    # Prepare parameters
    params = {
        'symbol': args.symbol
    }
    
    if args.expiration:
        params['expiration_date'] = args.expiration
    
    if args.option_type:
        params['option_type'] = args.option_type
    
    if args.strike:
        params['strike_price'] = args.strike
    
    # Get option chain
    chain = options.get_option_chain(**params)
    
    # Display results
    print(f"\nOption Chain for {args.symbol}:")
    print("-" * 80)
    
    for i, option in enumerate(chain[:10]):  # Show first 10 options
        print(f"{i+1}. {option.symbol} - Strike: ${option.strike_price:.2f}, "
              f"Type: {option.option_type}, Expiration: {option.expiration_date}")
    
    if len(chain) > 10:
        print(f"... and {len(chain) - 10} more options")
    
    print(f"\nTotal options: {len(chain)}")
    
    return chain

def get_option_snapshot(options, args):
    """Get and display option snapshot."""
    if not args.option_symbol:
        logger.error("Option symbol is required for snapshot action")
        return
    
    logger.info(f"Getting snapshot for {args.option_symbol}")
    
    # Get snapshot
    snapshot = options.get_option_snapshot(args.option_symbol)
    
    # Display results
    print(f"\nSnapshot for {args.option_symbol}:")
    print("-" * 80)
    
    # Extract and display relevant information
    print(f"Bid: ${snapshot.get('bid', 'N/A')}")
    print(f"Ask: ${snapshot.get('ask', 'N/A')}")
    print(f"Last: ${snapshot.get('last', 'N/A')}")
    print(f"Volume: {snapshot.get('volume', 'N/A')}")
    print(f"Open Interest: {snapshot.get('open_interest', 'N/A')}")
    
    # Display Greeks if available
    greeks = options.calculate_option_greeks(snapshot)
    
    if greeks:
        print("\nGreeks:")
        print(f"Delta: {greeks.get('delta', 'N/A')}")
        print(f"Gamma: {greeks.get('gamma', 'N/A')}")
        print(f"Theta: {greeks.get('theta', 'N/A')}")
        print(f"Vega: {greeks.get('vega', 'N/A')}")
        print(f"Implied Volatility: {greeks.get('implied_volatility', 'N/A')}")
    
    return snapshot

def find_options_by_criteria(options, args):
    """Find options matching criteria."""
    logger.info(f"Finding options for {args.symbol} matching criteria")
    
    # Prepare criteria
    criteria = {
        'max_dte': args.max_dte,
        'min_delta': args.min_delta,
        'max_delta': args.max_delta
    }
    
    # Find options
    matching_options = options.find_options_by_criteria(args.symbol, criteria)
    
    # Display results
    print(f"\nOptions for {args.symbol} matching criteria:")
    print(f"Max DTE: {args.max_dte}, Delta Range: {args.min_delta} - {args.max_delta}")
    print("-" * 80)
    
    for i, option in enumerate(matching_options):
        print(f"{i+1}. {option['symbol']} - Strike: ${option['strike']:.2f}, "
              f"Type: {option['option_type']}, Expiration: {option['expiration']}, "
              f"Delta: {option['delta']:.4f}")
    
    print(f"\nTotal matching options: {len(matching_options)}")
    
    return matching_options

def place_option_order(options, args):
    """Place an option order."""
    if not args.option_symbol:
        logger.error("Option symbol is required for order action")
        return
    
    if not args.side:
        logger.error("Side (buy/sell) is required for order action")
        return
    
    # Check if limit order requires a price
    if args.order_type == 'limit' and args.limit_price is None:
        logger.error("Limit price is required for limit orders")
        return
    
    logger.info(f"Placing {args.order_type} {args.side} order for {args.qty} {args.option_symbol}")
    
    # Prepare order parameters
    params = {
        'option_symbol': args.option_symbol,
        'qty': args.qty,
        'side': args.side,
        'order_type': args.order_type,
        'time_in_force': 'day'
    }
    
    if args.order_type == 'limit':
        params['limit_price'] = args.limit_price
    
    # Confirm with user
    print(f"\nAbout to place order:")
    print(f"Symbol: {args.option_symbol}")
    print(f"Side: {args.side}")
    print(f"Quantity: {args.qty}")
    print(f"Order Type: {args.order_type}")
    
    if args.order_type == 'limit':
        print(f"Limit Price: ${args.limit_price:.2f}")
    
    confirm = input("\nConfirm order (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Order cancelled")
        return
    
    # Place order
    try:
        order = options.place_option_order(**params)
        
        # Display order information
        print("\nOrder placed successfully:")
        print(f"Order ID: {order.id}")
        print(f"Status: {order.status}")
        print(f"Created At: {order.created_at}")
        
        return order
    
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        print(f"\nError placing order: {e}")
        return None

def get_option_positions(options, args):
    """Get and display option positions."""
    logger.info("Getting option positions")
    
    # Get positions
    positions = options.get_option_positions()
    
    # Display results
    print("\nCurrent Option Positions:")
    print("-" * 80)
    
    if not positions:
        print("No option positions found")
        return positions
    
    for i, position in enumerate(positions):
        print(f"{i+1}. {position.symbol} - Qty: {position.qty}, "
              f"Side: {position.side}, Avg Entry: ${float(position.avg_entry_price):.2f}, "
              f"Current Value: ${float(position.market_value):.2f}, "
              f"Unrealized P/L: ${float(position.unrealized_pl):.2f}")
    
    print(f"\nTotal positions: {len(positions)}")
    
    return positions

def get_option_orders(options, args):
    """Get and display option orders."""
    logger.info("Getting option orders")
    
    # Get orders
    orders = options.get_option_orders()
    
    # Display results
    print("\nCurrent Option Orders:")
    print("-" * 80)
    
    if not orders:
        print("No option orders found")
        return orders
    
    for i, order in enumerate(orders):
        print(f"{i+1}. {order.symbol} - Qty: {order.qty}, "
              f"Side: {order.side}, Type: {order.type}, "
              f"Status: {order.status}, Created: {order.created_at}")
    
    print(f"\nTotal orders: {len(orders)}")
    
    return orders

def place_multi_leg_option_order(options, args):
    """Place a multi-leg option order (example: straddle)."""
    if not args.symbol:
        logger.error("Symbol is required for multi-leg order")
        return
    
    logger.info(f"Setting up a straddle for {args.symbol}")
    
    # Get current price of the underlying
    # This is a simplified example - in a real scenario, you'd get the actual price
    print(f"Fetching option chain for {args.symbol} to create a straddle...")
    
    # Get option chain
    chain = options.get_option_chain(args.symbol)
    
    if not chain:
        print("No options found for this symbol")
        return
    
    # Find at-the-money options
    # This is a simplified approach - in a real scenario, you'd use more sophisticated logic
    calls = [opt for opt in chain if opt.option_type == 'call']
    puts = [opt for opt in chain if opt.option_type == 'put']
    
    if not calls or not puts:
        print("Could not find both calls and puts for this symbol")
        return
    
    # Sort by expiration date (closest first)
    calls.sort(key=lambda x: datetime.strptime(x.expiration_date, '%Y-%m-%d'))
    puts.sort(key=lambda x: datetime.strptime(x.expiration_date, '%Y-%m-%d'))
    
    # Get options expiring in the next 30-45 days
    today = datetime.now().date()
    target_date = today + timedelta(days=30)
    
    # Find closest expiration date
    call_exp = min(calls, key=lambda x: abs((datetime.strptime(x.expiration_date, '%Y-%m-%d').date() - target_date).days))
    put_exp = min(puts, key=lambda x: abs((datetime.strptime(x.expiration_date, '%Y-%m-%d').date() - target_date).days))
    
    # Filter options by expiration date
    calls = [opt for opt in calls if opt.expiration_date == call_exp.expiration_date]
    puts = [opt for opt in puts if opt.expiration_date == put_exp.expiration_date]
    
    # Find at-the-money options
    # In a real scenario, you'd compare with the current price of the underlying
    # For this example, we'll just use the middle strike price
    call_strikes = sorted([opt.strike_price for opt in calls])
    put_strikes = sorted([opt.strike_price for opt in puts])
    
    if not call_strikes or not put_strikes:
        print("Could not find suitable strikes for straddle")
        return
    
    # Find middle strike
    middle_call_strike = call_strikes[len(call_strikes) // 2]
    middle_put_strike = put_strikes[len(put_strikes) // 2]
    
    # Find the options with these strikes
    atm_call = next((opt for opt in calls if opt.strike_price == middle_call_strike), None)
    atm_put = next((opt for opt in puts if opt.strike_price == middle_put_strike), None)
    
    if not atm_call or not atm_put:
        print("Could not find at-the-money options for straddle")
        return
    
    # Display the selected options
    print("\nSelected options for straddle:")
    print(f"Call: {atm_call.symbol} - Strike: ${atm_call.strike_price:.2f}, Expiration: {atm_call.expiration_date}")
    print(f"Put: {atm_put.symbol} - Strike: ${atm_put.strike_price:.2f}, Expiration: {atm_put.expiration_date}")
    
    # Prepare legs for the straddle
    legs = [
        {"symbol": atm_call.symbol, "side": "buy", "ratio": 1},
        {"symbol": atm_put.symbol, "side": "buy", "ratio": 1}
    ]
    
    # Confirm with user
    confirm = input("\nConfirm straddle order (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Order cancelled")
        return
    
    # Place multi-leg order
    try:
        order = options.place_multi_leg_option_order(
            legs=legs,
            qty=args.qty,
            order_type=args.order_type,
            limit_price=args.limit_price if args.order_type == 'limit' else None
        )
        
        # Display order information
        print("\nStraddle order placed successfully:")
        print(f"Order ID: {order.id}")
        print(f"Status: {order.status}")
        print(f"Created At: {order.created_at}")
        
        return order
    
    except Exception as e:
        logger.error(f"Error placing straddle order: {e}")
        print(f"\nError placing straddle order: {e}")
        return None

def main():
    """Main function."""
    args = parse_arguments()
    
    try:
        # Initialize options trading
        options = OptionsTrading(paper=True)
        
        # Perform requested action
        if args.action == 'chain':
            get_option_chain(options, args)
        
        elif args.action == 'snapshot':
            get_option_snapshot(options, args)
        
        elif args.action == 'find':
            find_options_by_criteria(options, args)
        
        elif args.action == 'order':
            place_option_order(options, args)
        
        elif args.action == 'positions':
            get_option_positions(options, args)
        
        elif args.action == 'orders':
            get_option_orders(options, args)
        
        elif args.action == 'multi':
            place_multi_leg_option_order(options, args)
        
        else:
            logger.error(f"Unknown action: {args.action}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())