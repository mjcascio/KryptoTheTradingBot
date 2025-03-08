# Krypto Trading Bot - Alpaca Markets Edition

An automated trading bot that uses technical analysis to identify high-probability trading opportunities in the stock market using Alpaca Markets API.

## Features

- Implements breakout and trend following strategies
- High-probability trade identification (80%+ success rate target)
- Risk management with position sizing and stop losses
- Maximum 10 trades per day
- Real-time market data monitoring
- Automated trade execution

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your Alpaca credentials:
   ```
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
   ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Use this for paper trading
   ```

## Configuration

The bot can be configured through the `config.py` file:
- Trading parameters
- Risk management settings
- Strategy parameters
- Trading schedule

## Usage

Run the bot:
```bash
python main.py
```

## Strategies

1. Breakout Strategy:
   - Identifies potential breakout points using volume and price action
   - Confirms trends using multiple timeframes
   - Uses volatility for position sizing

2. Trend Following Strategy:
   - Multiple moving average crossovers
   - RSI for trend confirmation
   - Volume analysis for trend strength

## Risk Management

- Position sizing based on account equity
- Stop loss and take profit levels
- Maximum daily loss limits
- Trade frequency limits 