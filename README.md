# Krypto Trading Bot

[![CI/CD](https://github.com/mjcascio/KryptoTheTradingBot/actions/workflows/ci.yml/badge.svg)](https://github.com/mjcascio/KryptoTheTradingBot/actions/workflows/ci.yml)
[![Security Tests](https://github.com/mjcascio/KryptoTheTradingBot/actions/workflows/security.yml/badge.svg)](https://github.com/mjcascio/KryptoTheTradingBot/actions/workflows/security.yml)
[![Automated Backup](https://github.com/mjcascio/KryptoTheTradingBot/actions/workflows/backup.yml/badge.svg)](https://github.com/mjcascio/KryptoTheTradingBot/actions/workflows/backup.yml)

A modular, extensible trading bot for stocks and options with machine learning capabilities, built with Python.

## Architecture

The bot is organized into the following core modules:

```
src/
├── core/           # Core trading engine and bot management
├── data/           # Market data fetching and processing
├── integrations/   # External service integrations (Alpaca, Telegram)
├── ml/             # Machine learning models and predictions
├── monitoring/     # System monitoring and performance tracking
├── strategies/     # Trading strategies implementation
├── utils/          # Utility functions and helpers
├── web/           # Web dashboard and API
└── diagnostics/    # System diagnostics and health checks
```

## Features

- **Trading**
  - Stocks and options trading via Alpaca
  - Risk management and position sizing
  - Multiple trading strategies support
  - Real-time market data processing

- **Machine Learning**
  - Predictive analytics for trade signals
  - Automated model training and optimization
  - Feature extraction and engineering
  - Performance monitoring and retraining triggers

- **Monitoring & Control**
  - Real-time system monitoring
  - Performance metrics tracking
  - Telegram integration for alerts and control
  - Automated compliance checks

- **Security**
  - Secure credential management
  - Role-based access control
  - Audit logging
  - Automated backups

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env`:
   ```
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

## Configuration

The bot uses YAML configuration files in the `config/` directory:
- `config.yaml`: Main configuration file
- `trading.yaml`: Trading parameters
- `monitoring.yaml`: Monitoring settings
- `strategies.yaml`: Strategy configurations

## Usage

### Starting the Bot

```bash
python3 src/main.py
```

### Telegram Commands

- `/start` - Start trading
- `/stop` - Stop trading
- `/status` - Get system status
- `/positions` - View current positions
- `/performance` - Get performance metrics
- `/diagnostics` - Run system diagnostics

### Dashboard

Access the web dashboard at `http://localhost:8080`

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Strategies

1. Create a new strategy class in `src/strategies/`
2. Implement the required interface methods
3. Add configuration in `config/strategies.yaml`
4. Register the strategy in `src/strategies/__init__.py`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License

## Support

For support, please open an issue on GitHub or contact the maintainers.
# Last backup triggered: Sat Mar 15 12:35:27 EDT 2025
