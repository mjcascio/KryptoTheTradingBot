# Take Profit and Stop Loss Prices for Active Positions

## Overview
This enhancement adds Take Profit and Stop Loss prices to the Active Positions display in the KryptoBot Trading Dashboard. This allows traders to quickly see the exit points for each position without having to navigate to another screen or calculate them manually.

## Changes Made

### 1. Dashboard HTML Template
- Added two new columns to the positions table in `templates/dashboard.html`:
  - Take Profit: Shows the price at which the position will be automatically closed for profit
  - Stop Loss: Shows the price at which the position will be automatically closed to limit losses

### 2. JavaScript Position Rendering
- Updated the `updatePositionsTable` function in `templates/dashboard.html` to:
  - Extract take profit and stop loss values from position data
  - Format and display these values in the table
  - Handle cases where these values might not be set (displaying "-" instead)

### 3. Trading Bot Position Updates
- Modified the `_update_positions` method in `trading_bot.py` to:
  - Include take profit and stop loss values in the position data sent to the dashboard
  - Calculate take profit and stop loss values if they're not already set by the broker
  - Use the configured `take_profit_pct` and `stop_loss_pct` values for calculations

### 4. Risk Management Parameters
- Updated the `TradingBot` class initialization to properly store risk management parameters:
  - `stop_loss_pct`: Percentage below entry price for stop loss (for long positions)
  - `take_profit_pct`: Percentage above entry price for take profit (for long positions)
  - These values are reversed for short positions

## How It Works
1. When a position is opened, take profit and stop loss levels are set based on the configured percentages
2. For long positions:
   - Take Profit = Entry Price × (1 + take_profit_pct)
   - Stop Loss = Entry Price × (1 - stop_loss_pct)
3. For short positions:
   - Take Profit = Entry Price × (1 - take_profit_pct)
   - Stop Loss = Entry Price × (1 + stop_loss_pct)
4. These values are displayed in the positions table on the dashboard

## Configuration
The take profit and stop loss percentages are configured in `config.py`:
```python
# Risk Management
STOP_LOSS_PCT = 0.02    # 2% stop loss
TAKE_PROFIT_PCT = 0.06  # 6% take profit
```

You can adjust these values to change the default take profit and stop loss levels for all positions.

## Testing
The changes have been tested and are working correctly. The dashboard now displays take profit and stop loss prices for all active positions.

## Future Enhancements
Potential future enhancements could include:
- Ability to edit take profit and stop loss levels directly from the dashboard
- Visual indicators showing how close the current price is to take profit or stop loss levels
- Alerts when price approaches take profit or stop loss levels 