# KryptoTheTradingBot

A sophisticated trading bot that implements both stock and options trading strategies with advanced risk management.

## Features

- **Multi-Strategy Support**
  - Stock trading with technical analysis
  - Options trading with volatility analysis
  - Customizable strategy parameters

- **Risk Management**
  - Position sizing based on account equity
  - Maximum drawdown limits
  - Per-trade risk controls
  - Volatility-based adjustments
  - Maximum position limits

- **Market Data**
  - Real-time market data processing
  - Technical indicators calculation
  - Historical data caching
  - Options chain data support (via Alpaca API or Yahoo Finance)

- **Integration**
  - Alpaca trading platform integration
  - Telegram notifications
  - Comprehensive logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/KryptoTheTradingBot.git
cd KryptoTheTradingBot
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Usage

1. Run the preflight check:
```bash
python test_options.py
```
This will verify that all systems are operational and ready for trading.

2. Start the trading bot:
```bash
python3 src/main.py
```

3. Monitor the logs:
```bash
tail -f logs/trading_bot.log
```

4. Check Telegram for notifications about:
   - Trade executions
   - Position updates
   - Risk alerts
   - Daily summaries

## Market Data Sources

### Stock Data
- Primary: Alpaca API (real-time market data)
- Technical indicators calculated in real-time

### Options Data
- Primary: Alpaca API (requires subscription)
- Fallback: Yahoo Finance (free, reliable data)
  - Real-time options chains
  - Greeks and implied volatility
  - Volume and open interest

## Configuration

### Risk Management Parameters
- `max_position_size`: Maximum position size in dollars
- `max_drawdown`: Maximum allowed drawdown percentage
- `risk_per_trade`: Maximum risk per trade percentage
- `max_open_positions`: Maximum number of open positions
- `max_daily_loss`: Maximum daily loss percentage
- `volatility_threshold`: Volatility threshold for position sizing

### Trading Parameters
- `update_interval`: How often to update market data (default: 60 seconds)
- `watchlist`: List of symbols to monitor

## Project Structure

```
KryptoTheTradingBot/
├── src/
│   ├── core/
│   │   ├── trading_bot.py
│   │   ├── market_data.py
│   │   └── risk_management.py
│   ├── strategies/
│   │   ├── base.py
│   │   ├── stock.py
│   │   └── options.py
│   ├── integrations/
│   │   └── alpaca.py
│   └── main.py
├── logs/
├── data/
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This trading bot is for educational purposes only. Always do your own research and never risk more than you can afford to lose.

## Last Backup
Last backup triggered: 2024-03-13 19:55:00 UTC
