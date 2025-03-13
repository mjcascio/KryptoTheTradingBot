#!/usr/bin/env python3
"""
Check Trades Script

This script checks if the trading bot executed any trades today and displays a summary.
"""

import os
import sys
import logging
import json
import pandas as pd
from datetime import datetime, timedelta
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("check_trades.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_trade_history(file_path='data/trade_history.json'):
    """
    Load trade history from JSON file
    
    Args:
        file_path: Path to trade history file
        
    Returns:
        DataFrame with trade history
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Trade history file not found: {file_path}")
            return pd.DataFrame()
        
        with open(file_path, 'r') as f:
            trade_data = json.load(f)
        
        if not trade_data:
            logger.warning("Trade history is empty")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(trade_data)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    except Exception as e:
        logger.error(f"Error loading trade history: {e}")
        return pd.DataFrame()

def check_trades_today(trade_history=None):
    """
    Check if any trades were executed today
    
    Args:
        trade_history: DataFrame with trade history
        
    Returns:
        DataFrame with today's trades
    """
    try:
        if trade_history is None:
            trade_history = load_trade_history()
        
        if trade_history.empty:
            logger.warning("No trade history available")
            return pd.DataFrame()
        
        # Get today's date
        today = datetime.now().date()
        
        # Filter trades for today
        today_trades = trade_history[trade_history['timestamp'].dt.date == today]
        
        return today_trades
    
    except Exception as e:
        logger.error(f"Error checking today's trades: {e}")
        return pd.DataFrame()

def check_recent_trades(days=7, trade_history=None):
    """
    Check trades from the last N days
    
    Args:
        days: Number of days to look back
        trade_history: DataFrame with trade history
        
    Returns:
        DataFrame with recent trades
    """
    try:
        if trade_history is None:
            trade_history = load_trade_history()
        
        if trade_history.empty:
            logger.warning("No trade history available")
            return pd.DataFrame()
        
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        # Filter trades since start date
        recent_trades = trade_history[trade_history['timestamp'].dt.date >= start_date]
        
        return recent_trades
    
    except Exception as e:
        logger.error(f"Error checking recent trades: {e}")
        return pd.DataFrame()

def format_trade_summary(trades):
    """
    Format trade summary for display
    
    Args:
        trades: DataFrame with trades
        
    Returns:
        Formatted summary string
    """
    if trades.empty:
        return "No trades found."
    
    # Calculate summary statistics
    total_trades = len(trades)
    profitable_trades = len(trades[trades['profit'] > 0])
    losing_trades = len(trades[trades['profit'] < 0])
    
    if 'profit' in trades.columns:
        total_profit = trades['profit'].sum()
        avg_profit = trades['profit'].mean()
        max_profit = trades['profit'].max()
        max_loss = trades['profit'].min()
    else:
        total_profit = avg_profit = max_profit = max_loss = 0
    
    # Format summary
    summary = f"Trade Summary ({total_trades} trades):\n"
    summary += f"  Profitable trades: {profitable_trades}\n"
    summary += f"  Losing trades: {losing_trades}\n"
    summary += f"  Total profit/loss: ${total_profit:.2f}\n"
    summary += f"  Average profit/loss: ${avg_profit:.2f}\n"
    summary += f"  Maximum profit: ${max_profit:.2f}\n"
    summary += f"  Maximum loss: ${max_loss:.2f}\n\n"
    
    # Add trade details
    summary += "Trade Details:\n"
    for i, trade in trades.iterrows():
        timestamp = trade.get('timestamp', 'Unknown')
        symbol = trade.get('symbol', 'Unknown')
        side = trade.get('side', 'Unknown')
        quantity = trade.get('quantity', 0)
        entry_price = trade.get('entry_price', 0)
        exit_price = trade.get('exit_price', 0)
        profit = trade.get('profit', 0)
        strategy = trade.get('strategy', 'Unknown')
        
        summary += f"  {timestamp}: {side.upper()} {quantity} {symbol} @ ${entry_price:.2f}, "
        summary += f"Exit @ ${exit_price:.2f}, Profit: ${profit:.2f}, Strategy: {strategy}\n"
    
    return summary

def check_active_positions(file_path='data/positions.json'):
    """
    Check currently active positions
    
    Args:
        file_path: Path to positions file
        
    Returns:
        Dictionary with active positions
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Positions file not found: {file_path}")
            return {}
        
        with open(file_path, 'r') as f:
            positions = json.load(f)
        
        return positions
    
    except Exception as e:
        logger.error(f"Error checking active positions: {e}")
        return {}

def format_positions_summary(positions):
    """
    Format positions summary for display
    
    Args:
        positions: Dictionary with positions
        
    Returns:
        Formatted summary string
    """
    if not positions:
        return "No active positions."
    
    summary = f"Active Positions ({len(positions)} positions):\n"
    
    for symbol, position in positions.items():
        entry_time = position.get('entry_time', 'Unknown')
        side = position.get('side', 'Unknown')
        quantity = position.get('quantity', 0)
        entry_price = position.get('entry_price', 0)
        current_price = position.get('current_price', 0)
        unrealized_profit = position.get('unrealized_profit', 0)
        strategy = position.get('strategy', 'Unknown')
        
        summary += f"  {symbol}: {side.upper()} {quantity} @ ${entry_price:.2f}, "
        summary += f"Current: ${current_price:.2f}, Unrealized P/L: ${unrealized_profit:.2f}, Strategy: {strategy}\n"
    
    return summary

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Check if the trading bot executed any trades today')
    parser.add_argument('--days', type=int, default=1, help='Number of days to look back (default: 1 for today only)')
    parser.add_argument('--positions', action='store_true', help='Show active positions')
    args = parser.parse_args()
    
    try:
        # Load trade history
        trade_history = load_trade_history()
        
        if args.days == 1:
            # Check today's trades
            today_trades = check_trades_today(trade_history)
            
            if today_trades.empty:
                print("No trades were executed today.")
            else:
                print(f"The bot executed {len(today_trades)} trades today.")
                print(format_trade_summary(today_trades))
        else:
            # Check recent trades
            recent_trades = check_recent_trades(days=args.days, trade_history=trade_history)
            
            if recent_trades.empty:
                print(f"No trades were executed in the last {args.days} days.")
            else:
                print(f"The bot executed {len(recent_trades)} trades in the last {args.days} days.")
                print(format_trade_summary(recent_trades))
        
        # Check active positions if requested
        if args.positions:
            positions = check_active_positions()
            print("\nActive Positions:")
            print(format_positions_summary(positions))
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"Error checking trades: {e}")

if __name__ == "__main__":
    main() 