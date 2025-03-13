# KryptoBot Coinbase Integration

This module provides a standalone integration with Coinbase Pro for the KryptoBot Trading System. It includes a fully-featured API client, market data handling, order management, and a real-time dashboard.

## Features

- Asynchronous Coinbase Pro API client
- Real-time market data streaming
- Order management (market and limit orders)
- Account and position tracking
- Modern web dashboard
- Comprehensive error handling and logging
- Secure configuration management

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the integration directory with your Coinbase Pro API credentials:
```bash
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
COINBASE_PASSPHRASE=your_passphrase
COINBASE_SANDBOX=false  # Set to true for sandbox environment
```

2. Make sure the `.env` file is properly secured:
```bash
chmod 600 .env
```

## Usage

### Starting the Dashboard

1. Run the Flask application:
```bash
python -m dashboard.app
```

2. Open your browser and navigate to `http://localhost:5001`

### Using the API Client

```python
from api.client import CoinbaseClient
import asyncio

async def main():
    async with CoinbaseClient(
        api_key="your_api_key",
        api_secret="your_api_secret",
        passphrase="your_passphrase"
    ) as client:
        # Get account information
        accounts = await client.get_accounts()
        print("Accounts:", accounts)
        
        # Get market data
        ticker = await client.get_product_ticker("BTC-USD")
        print("BTC-USD Price:", ticker.price)
        
        # Place a limit order
        order = await client.place_order(
            product_id="BTC-USD",
            side="buy",
            order_type="limit",
            size=0.01,
            price=50000.00
        )
        print("Order placed:", order)

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Structure

```
integrations/coinbase/
├── api/
│   └── client.py          # Coinbase Pro API client
├── models/
│   ├── account.py         # Account and position models
│   ├── market.py          # Market data models
│   └── order.py          # Order models
├── utils/
│   ├── exceptions.py      # Custom exceptions
│   └── logging.py        # Logging configuration
├── dashboard/
│   ├── app.py            # Flask dashboard application
│   ├── static/           # Static assets
│   └── templates/        # HTML templates
├── tests/                # Test suite
├── docs/                # Documentation
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Testing

Run the test suite:
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## Security

- API credentials are stored securely using environment variables
- All API requests use HMAC authentication
- Rate limiting is implemented to prevent API abuse
- Sensitive data is never logged
- Regular security updates for dependencies

## License

This project is licensed under the MIT License - see the LICENSE file for details. 