# Krypto Trading Bot

An advanced automated trading system that leverages machine learning, technical analysis, and multiple broker integrations to execute sophisticated trading strategies in various financial markets.

## Features

- **Multi-Broker Support**:
  - Alpaca Markets integration for stocks and crypto
  - MetaTrader integration for forex markets
  - Extensible broker architecture for adding new platforms

- **Advanced Trading Strategies**:
  - Machine learning enhanced signal generation
  - Multiple concurrent strategy execution
  - Dynamic strategy allocation based on market conditions
  - Breakout and trend following implementations
  - Custom strategy development framework

- **Risk Management**:
  - Position sizing based on account equity
  - Dynamic stop loss and take profit levels
  - Maximum drawdown protection
  - Trade frequency limits
  - Portfolio optimization and diversification

- **Analytics & Monitoring**:
  - Real-time performance dashboard
  - Trade history and analytics
  - Market condition monitoring
  - Email notifications for important events
  - Automated parameter tuning

## Project Structure

```
├── brokers/                 # Broker integration implementations
├── static/                  # Dashboard static assets
├── templates/              # Dashboard HTML templates
├── tests/                  # Test suite
├── main.py                 # Main bot entry point
├── trading_bot.py          # Core trading logic
├── market_data.py          # Market data handling
├── ml_enhancer.py          # ML signal enhancement
├── portfolio_optimizer.py   # Portfolio optimization
├── parameter_tuner.py      # Strategy parameter tuning
├── performance_analyzer.py  # Performance analytics
├── strategy_allocator.py   # Strategy management
├── strategies.py           # Trading strategies
├── notifications.py        # Notification system
└── config.py              # Configuration settings
```

## Setup

### Prerequisites
- Python 3.9+
- pip package manager
- Git

### Installation

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

4. Configure environment variables:
   Create a `.env` file with your credentials:
   ```
   # Alpaca Configuration
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
   ALPACA_BASE_URL=https://paper-api.alpaca.markets

   # MetaTrader Configuration (if using)
   MT_SERVER=your_server
   MT_PORT=your_port
   MT_USERNAME=your_username
   MT_PASSWORD=your_password

   # Email Notifications (optional)
   EMAIL_SERVER=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USERNAME=your_email
   EMAIL_PASSWORD=your_app_password
   ```

## Usage

### Starting the Bot

1. Start the trading bot:
   ```bash
   ./start_bot.sh
   ```

2. Start the dashboard:
   ```bash
   ./start_dashboard.sh
   ```

3. Monitor the bot:
   ```bash
   ./monitor_bot.sh
   ```

### Dashboard Access
- Access the dashboard at: `http://localhost:5000`
- View real-time performance metrics
- Monitor active trades and positions
- Analyze historical performance

## Development

### Workflow

1. Create a new branch for features:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Run tests before committing:
   ```bash
   python -m pytest tests/
   ```

3. Follow commit message convention:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation
   - test: Testing
   - refactor: Code refactoring

### Adding New Features

1. **New Strategies**:
   - Create strategy class in `strategies.py`
   - Implement required methods
   - Add strategy to configuration
   - Write tests in `tests/`

2. **New Broker Integration**:
   - Add broker class in `brokers/`
   - Implement base broker interface
   - Update broker factory
   - Add configuration options

## Testing

Run all tests:
```bash
python test_all.py
```

Run specific test categories:
```bash
python test_market_data.py
python test_connection.py
python test_enhanced_features.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@kryptobot.com or open an issue on GitHub. 