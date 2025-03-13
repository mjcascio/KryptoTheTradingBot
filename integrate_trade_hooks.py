#!/usr/bin/env python3
"""
Trade Hooks Integration

This script demonstrates how to integrate the trade hooks with the trading bot.
It provides examples of how to call the trade hooks at the appropriate points
in your trading logic.
"""

import os
import sys
import logging
from trade_hooks import (
    on_trade_executed,
    on_position_opened,
    on_position_closed,
    on_position_updated,
    on_system_event
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def integrate_with_trading_bot():
    """
    Example of how to integrate trade hooks with your trading bot
    
    This is a demonstration function showing where to call the hooks
    in your trading logic. You should adapt this to your actual trading bot.
    """
    # System startup notification
    on_system_event(
        event_type="info",
        message="Trading bot started successfully"
    )
    
    # Example trading logic
    try:
        # Your trading bot initialization code here
        logger.info("Initializing trading bot...")
        
        # Example: When a trade is executed
        # This would be called when your bot executes a trade
        on_trade_executed(
            symbol="AAPL",
            side="buy",
            quantity=10,
            price=198.50,
            strategy="breakout"
        )
        
        # Example: When a position is opened
        # This would be called when your bot opens a new position
        on_position_opened(
            symbol="AAPL",
            side="long",
            quantity=10,
            price=198.50,
            strategy="breakout"
        )
        
        # Example: When a position is updated
        # This would be called periodically to update position status
        on_position_updated(
            symbol="AAPL",
            side="long",
            quantity=10,
            entry_price=198.50,
            current_price=200.25,
            unrealized_profit=17.50,
            strategy="breakout"
        )
        
        # Example: When a position is closed
        # This would be called when your bot closes a position
        on_position_closed(
            symbol="AAPL",
            side="long",
            quantity=10,
            entry_price=198.50,
            exit_price=205.75,
            profit=72.50,
            strategy="breakout"
        )
        
        # Example: System event notification
        # This can be called for various system events
        on_system_event(
            event_type="info",
            message="Trading session completed successfully"
        )
        
    except Exception as e:
        # Error notification
        logger.error(f"Error in trading bot: {e}")
        on_system_event(
            event_type="error",
            message=f"Trading bot error: {str(e)}"
        )

def main():
    """Main function"""
    logger.info("Starting trade hooks integration example...")
    
    # Run the integration example
    integrate_with_trading_bot()
    
    logger.info("Trade hooks integration example completed")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 