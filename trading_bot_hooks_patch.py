#!/usr/bin/env python3
"""
Trading Bot Hooks Patch

This script patches the trading bot to integrate the trade hooks.
It should be applied to the trading bot by importing it in the main trading bot file.
"""

import logging
from typing import Dict, Any, Optional
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

def patch_trading_bot():
    """
    Patch the trading bot to integrate the trade hooks
    
    This function monkey patches the relevant methods in the trading bot
    to call the trade hooks at the appropriate points.
    """
    logger.info("Patching trading bot with trade hooks...")
    
    # Import the necessary modules
    try:
        # Import broker module
        from brokers.base_broker import BaseBroker
        
        # Store original methods
        original_place_order = BaseBroker.place_order
        original_update_position = BaseBroker.update_position
        
        # Patch place_order method
        def patched_place_order(self, symbol: str, qty: float, side: str, order_type: str,
                               limit_price: Optional[float] = None, stop_price: Optional[float] = None,
                               time_in_force: str = 'day', **kwargs) -> Dict[str, Any]:
            """Patched place_order method that calls trade hooks"""
            # Call original method
            result = original_place_order(self, symbol, qty, side, order_type, 
                                         limit_price, stop_price, time_in_force, **kwargs)
            
            # Get price from result or use limit_price/stop_price
            price = result.get('price', limit_price or stop_price or 0)
            
            # Call trade hooks
            if side.lower() in ['buy', 'long']:
                # Call trade executed hook
                on_trade_executed(
                    symbol=symbol,
                    side='buy',
                    quantity=qty,
                    price=price,
                    strategy=kwargs.get('strategy', 'unknown')
                )
                
                # Call position opened hook
                on_position_opened(
                    symbol=symbol,
                    side='long',
                    quantity=qty,
                    price=price,
                    strategy=kwargs.get('strategy', 'unknown')
                )
            else:
                # For sell orders, we need to determine if this is closing a position
                # or opening a short position
                if kwargs.get('is_closing_position', False):
                    # Get entry price and profit if available
                    entry_price = kwargs.get('entry_price', 0)
                    profit = kwargs.get('profit', (price - entry_price) * qty if entry_price > 0 else 0)
                    
                    # Call position closed hook
                    on_position_closed(
                        symbol=symbol,
                        side='long',
                        quantity=qty,
                        entry_price=entry_price,
                        exit_price=price,
                        profit=profit,
                        strategy=kwargs.get('strategy', 'unknown')
                    )
                else:
                    # Opening a short position
                    on_trade_executed(
                        symbol=symbol,
                        side='sell',
                        quantity=qty,
                        price=price,
                        strategy=kwargs.get('strategy', 'unknown')
                    )
                    
                    on_position_opened(
                        symbol=symbol,
                        side='short',
                        quantity=qty,
                        price=price,
                        strategy=kwargs.get('strategy', 'unknown')
                    )
            
            return result
        
        # Patch update_position method
        def patched_update_position(self, symbol: str, stop_loss: float = None, 
                                   take_profit: float = None) -> bool:
            """Patched update_position method that calls trade hooks"""
            # Call original method
            result = original_update_position(self, symbol, stop_loss, take_profit)
            
            # Get position details
            try:
                position = self.get_position(symbol)
                if position:
                    # Calculate unrealized profit
                    entry_price = position.get('avg_entry_price', 0)
                    current_price = position.get('current_price', 0)
                    qty = position.get('qty', 0)
                    side = 'long' if position.get('side', '').lower() in ['buy', 'long'] else 'short'
                    
                    # Calculate unrealized profit based on position side
                    if side == 'long':
                        unrealized_profit = (current_price - entry_price) * qty
                    else:
                        unrealized_profit = (entry_price - current_price) * qty
                    
                    # Call position updated hook
                    on_position_updated(
                        symbol=symbol,
                        side=side,
                        quantity=qty,
                        entry_price=entry_price,
                        current_price=current_price,
                        unrealized_profit=unrealized_profit,
                        strategy=position.get('strategy', 'unknown')
                    )
            except Exception as e:
                logger.error(f"Error updating position hook for {symbol}: {e}")
            
            return result
        
        # Apply patches
        BaseBroker.place_order = patched_place_order
        BaseBroker.update_position = patched_update_position
        
        logger.info("Successfully patched trading bot with trade hooks")
        
        # Send system event notification
        on_system_event(
            event_type="info",
            message="Trading bot patched with trade hooks"
        )
        
        return True
        
    except ImportError as e:
        logger.error(f"Error importing modules for patching: {e}")
        return False
    except Exception as e:
        logger.error(f"Error patching trading bot: {e}")
        return False

# Apply patch when module is imported
patch_result = patch_trading_bot()

# For testing
if __name__ == "__main__":
    if patch_result:
        print("Trading bot successfully patched with trade hooks")
    else:
        print("Failed to patch trading bot with trade hooks") 