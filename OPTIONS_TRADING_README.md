# Options Trading with KryptoBot

This module adds options trading capabilities to KryptoBot using the Alpaca API. It allows you to fetch option chains, place option orders, and manage option positions programmatically.

## Features

- **Option Chain Retrieval**: Fetch option chains for any symbol with filtering by expiration date, option type, and strike price.
- **Option Snapshots**: Get detailed information about specific option contracts, including pricing and Greeks.
- **Option Order Placement**: Place market and limit orders for option contracts.
- **Multi-leg Strategies**: Create and execute multi-leg option strategies like straddles, strangles, and spreads.
- **Position Management**: View and manage your option positions.
- **Option Screening**: Find options matching specific criteria like delta, days to expiration, etc.

## Prerequisites

- Alpaca account with options trading enabled
- Alpaca API key and secret
- Python 3.7+
- Required Python packages:
  - alpaca-py
  - pandas
  - python-dotenv

## Setup

1. Ensure your Alpaca API credentials are set in your `.env` file:
   ```
   ALPACA_API_KEY=your_api_key
   ALPACA_API_SECRET=your_api_secret
   ```

2. Install required packages:
   ```
   pip install alpaca-py pandas python-dotenv
   ```

## Usage

### Basic Usage

```python
from options_trading import OptionsTrading

# Initialize with paper trading (recommended for testing)
options = OptionsTrading(paper=True)

# Get option chain for SPY
chain = options.get_option_chain("SPY")

# Get snapshot for a specific option contract
snapshot = options.get_option_snapshot("SPY230616C00420000")

# Place an option order
order = options.place_option_order(
    option_symbol="SPY230616C00420000",
    qty=1,
    side="buy",
    order_type="market"
)

# Get current option positions
positions = options.get_option_positions()
```

### Using the Test Script

The `test_options_trading.py` script provides a command-line interface for testing options trading functionality:

```bash
# Get option chain for SPY
./test_options_trading.py --action chain --symbol SPY

# Get snapshot for a specific option contract
./test_options_trading.py --action snapshot --option-symbol SPY230616C00420000

# Find options matching criteria
./test_options_trading.py --action find --symbol SPY --max-dte 30 --min-delta 0.3 --max-delta 0.7

# Place an option order
./test_options_trading.py --action order --option-symbol SPY230616C00420000 --side buy --qty 1

# View current option positions
./test_options_trading.py --action positions

# Create a straddle
./test_options_trading.py --action multi --symbol SPY
```

## Multi-leg Strategies

The module supports creating and executing multi-leg option strategies:

```python
# Create a straddle (buy call and put at the same strike)
legs = [
    {"symbol": "SPY230616C00420000", "side": "buy", "ratio": 1},
    {"symbol": "SPY230616P00420000", "side": "buy", "ratio": 1}
]

# Place the multi-leg order
order = options.place_multi_leg_option_order(
    legs=legs,
    qty=1,
    order_type="market"
)
```

## Important Notes

1. **Paper Trading**: As of April 2024, Alpaca supports options trading in paper environment, with live trading coming soon. Always test your strategies in paper trading first.

2. **Risk Management**: Options trading involves significant risk. Implement proper risk management in your strategies.

3. **API Limitations**: Be aware of Alpaca's API rate limits and any restrictions on options trading.

4. **Option Symbols**: Alpaca uses the OCC option symbol format (e.g., SPY230616C00420000), which encodes:
   - Underlying symbol (SPY)
   - Expiration date (230616 = June 16, 2023)
   - Option type (C = Call, P = Put)
   - Strike price (00420000 = $420.00)

## Troubleshooting

- **Authentication Issues**: Ensure your API key and secret are correct in the `.env` file.
- **Option Trading Access**: Verify that your Alpaca account has options trading enabled.
- **Symbol Format**: Ensure option symbols follow the correct format.
- **API Errors**: Check the logs at `logs/options_trading.log` for detailed error messages.

## Resources

- [Alpaca Options Trading Documentation](https://alpaca.markets/docs/trading/options/)
- [Alpaca-py GitHub Repository](https://github.com/alpacahq/alpaca-py)
- [Options Trading Basics](https://www.investopedia.com/options-basics-tutorial-4583012) 