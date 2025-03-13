#!/usr/bin/env python3
"""
Manage Alpaca Watchlist

This script allows you to manage your Alpaca watchlists, including creating,
updating, and deleting watchlists, as well as adding and removing symbols.
"""

import os
import sys
import json
import logging
import argparse
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Alpaca credentials
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL')

# Check if Alpaca is configured
if not all([ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL]):
    logger.error("Alpaca API credentials not configured. Please check your .env file.")
    sys.exit(1)

# Alpaca API headers
HEADERS = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

def get_watchlists():
    """
    Get all watchlists
    
    Returns:
        List of watchlists
    """
    try:
        response = requests.get(
            f'{ALPACA_BASE_URL}/v2/watchlists',
            headers=HEADERS
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting watchlists: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting watchlists: {e}")
        return []

def get_watchlist(watchlist_id):
    """
    Get a specific watchlist
    
    Args:
        watchlist_id: Watchlist ID
        
    Returns:
        Watchlist information
    """
    try:
        response = requests.get(
            f'{ALPACA_BASE_URL}/v2/watchlists/{watchlist_id}',
            headers=HEADERS
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting watchlist: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        return None

def create_watchlist(name, symbols=None):
    """
    Create a new watchlist
    
    Args:
        name: Watchlist name
        symbols: List of symbols to add to the watchlist
        
    Returns:
        Watchlist information
    """
    try:
        # Prepare data
        data = {
            'name': name
        }
        
        if symbols:
            data['symbols'] = symbols
        
        # Create watchlist
        response = requests.post(
            f'{ALPACA_BASE_URL}/v2/watchlists',
            headers=HEADERS,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error creating watchlist: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        return None

def update_watchlist(watchlist_id, name=None, symbols=None):
    """
    Update a watchlist
    
    Args:
        watchlist_id: Watchlist ID
        name: New watchlist name
        symbols: List of symbols to set for the watchlist
        
    Returns:
        Watchlist information
    """
    try:
        # Prepare data
        data = {}
        
        if name:
            data['name'] = name
            
        if symbols:
            data['symbols'] = symbols
        
        # Update watchlist
        response = requests.put(
            f'{ALPACA_BASE_URL}/v2/watchlists/{watchlist_id}',
            headers=HEADERS,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error updating watchlist: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error updating watchlist: {e}")
        return None

def delete_watchlist(watchlist_id):
    """
    Delete a watchlist
    
    Args:
        watchlist_id: Watchlist ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.delete(
            f'{ALPACA_BASE_URL}/v2/watchlists/{watchlist_id}',
            headers=HEADERS
        )
        
        if response.status_code == 204:
            return True
        else:
            logger.error(f"Error deleting watchlist: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting watchlist: {e}")
        return False

def add_symbol(watchlist_id, symbol):
    """
    Add a symbol to a watchlist
    
    Args:
        watchlist_id: Watchlist ID
        symbol: Symbol to add
        
    Returns:
        Watchlist information
    """
    try:
        response = requests.post(
            f'{ALPACA_BASE_URL}/v2/watchlists/{watchlist_id}',
            headers=HEADERS,
            json={'symbol': symbol}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error adding symbol: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error adding symbol: {e}")
        return None

def remove_symbol(watchlist_id, symbol):
    """
    Remove a symbol from a watchlist
    
    Args:
        watchlist_id: Watchlist ID
        symbol: Symbol to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.delete(
            f'{ALPACA_BASE_URL}/v2/watchlists/{watchlist_id}/{symbol}',
            headers=HEADERS
        )
        
        if response.status_code == 204:
            return True
        else:
            logger.error(f"Error removing symbol: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error removing symbol: {e}")
        return False

def display_watchlists(watchlists):
    """
    Display watchlists
    
    Args:
        watchlists: List of watchlists
    """
    print("=" * 80)
    print("WATCHLISTS")
    print("=" * 80)
    
    if not watchlists:
        print("No watchlists found")
        return
    
    for watchlist in watchlists:
        print(f"ID: {watchlist['id']}")
        print(f"Name: {watchlist['name']}")
        print(f"Created At: {watchlist['created_at']}")
        print(f"Updated At: {watchlist['updated_at']}")
        
        if 'assets' in watchlist and watchlist['assets']:
            print("Symbols:")
            for asset in watchlist['assets']:
                print(f"  {asset['symbol']}")
        else:
            print("Symbols: None")
            
        print("-" * 80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Manage Alpaca watchlists")
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # List watchlists
    list_parser = subparsers.add_parser('list', help='List watchlists')
    
    # Get watchlist
    get_parser = subparsers.add_parser('get', help='Get a specific watchlist')
    get_parser.add_argument('watchlist_id', help='Watchlist ID')
    
    # Create watchlist
    create_parser = subparsers.add_parser('create', help='Create a new watchlist')
    create_parser.add_argument('name', help='Watchlist name')
    create_parser.add_argument('--symbols', nargs='+', help='Symbols to add to the watchlist')
    
    # Update watchlist
    update_parser = subparsers.add_parser('update', help='Update a watchlist')
    update_parser.add_argument('watchlist_id', help='Watchlist ID')
    update_parser.add_argument('--name', help='New watchlist name')
    update_parser.add_argument('--symbols', nargs='+', help='Symbols to set for the watchlist')
    
    # Delete watchlist
    delete_parser = subparsers.add_parser('delete', help='Delete a watchlist')
    delete_parser.add_argument('watchlist_id', help='Watchlist ID')
    
    # Add symbol
    add_parser = subparsers.add_parser('add', help='Add a symbol to a watchlist')
    add_parser.add_argument('watchlist_id', help='Watchlist ID')
    add_parser.add_argument('symbol', help='Symbol to add')
    
    # Remove symbol
    remove_parser = subparsers.add_parser('remove', help='Remove a symbol from a watchlist')
    remove_parser.add_argument('watchlist_id', help='Watchlist ID')
    remove_parser.add_argument('symbol', help='Symbol to remove')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        # List watchlists
        watchlists = get_watchlists()
        display_watchlists(watchlists)
        
    elif args.command == 'get':
        # Get watchlist
        watchlist = get_watchlist(args.watchlist_id)
        if watchlist:
            display_watchlists([watchlist])
        
    elif args.command == 'create':
        # Create watchlist
        watchlist = create_watchlist(args.name, args.symbols)
        if watchlist:
            print(f"Watchlist '{args.name}' created successfully")
            display_watchlists([watchlist])
        
    elif args.command == 'update':
        # Update watchlist
        watchlist = update_watchlist(args.watchlist_id, args.name, args.symbols)
        if watchlist:
            print(f"Watchlist updated successfully")
            display_watchlists([watchlist])
        
    elif args.command == 'delete':
        # Delete watchlist
        success = delete_watchlist(args.watchlist_id)
        if success:
            print(f"Watchlist deleted successfully")
        
    elif args.command == 'add':
        # Add symbol
        watchlist = add_symbol(args.watchlist_id, args.symbol)
        if watchlist:
            print(f"Symbol '{args.symbol}' added successfully")
            display_watchlists([watchlist])
        
    elif args.command == 'remove':
        # Remove symbol
        success = remove_symbol(args.watchlist_id, args.symbol)
        if success:
            print(f"Symbol '{args.symbol}' removed successfully")
            
            # Get updated watchlist
            watchlist = get_watchlist(args.watchlist_id)
            if watchlist:
                display_watchlists([watchlist])
    
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 