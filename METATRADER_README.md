# MetaTrader Integration for KryptoBot

This guide explains how to set up and use the MetaTrader integration with KryptoBot for forex trading.

## Prerequisites

1. MetaTrader 4 or MetaTrader 5 installed on your computer
2. Python 3.7+ installed
3. KryptoBot installed and configured

## Setup Instructions

### 1. Install the MetaTrader REST API Bridge

The MetaTrader integration requires a REST API bridge to communicate between KryptoBot and MetaTrader. Follow these steps to set it up:

#### For MetaTrader 4:

1. Download the MT4 REST API bridge from [GitHub](https://github.com/khramkov/MQL4-REST-API) or use the provided files in the `mt_bridge` directory.
2. Copy the `MQL4-REST-API.ex4` file to your MetaTrader 4 `Experts` directory.
3. Copy the `Include` folder contents to your MetaTrader 4 `Include` directory.
4. Restart MetaTrader 4.
5. Open a chart (any currency pair) and drag the `MQL4-REST-API` expert advisor onto the chart.
6. In the expert advisor settings, set the following:
   - Server port: 5000 (default)
   - API key: Create a secure key (you'll need this for KryptoBot configuration)
7. Click "OK" to start the REST API server.

#### For MetaTrader 5:

1. Download the MT5 REST API bridge from [GitHub](https://github.com/khramkov/MQL5-REST-API) or use the provided files in the `mt_bridge` directory.
2. Copy the `MQL5-REST-API.ex5` file to your MetaTrader 5 `Experts` directory.
3. Copy the `Include` folder contents to your MetaTrader 5 `Include` directory.
4. Restart MetaTrader 5.
5. Open a chart (any currency pair) and drag the `MQL5-REST-API` expert advisor onto the chart.
6. In the expert advisor settings, set the following:
   - Server port: 5000 (default)
   - API key: Create a secure key (you'll need this for KryptoBot configuration)
7. Click "OK" to start the REST API server.

### 2. Configure KryptoBot for MetaTrader

1. Open your `.env` file in the KryptoBot directory and add the following environment variables:

```
MT_API_URL=http://localhost:5000
MT_API_KEY=your_api_key_here
MT_ACCOUNT_NUMBER=your_mt_account_number
```

2. Open the `config.py` file and ensure the MetaTrader platform is enabled:

```python
"metatrader": {
    "enabled": True,
    "name": "MetaTrader",
    "type": "forex",
    "default": False,
    "watchlist": [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"
    ]
}
```

3. You can customize the watchlist with your preferred forex pairs.

## Using MetaTrader with KryptoBot

### Switching Platforms

1. Start KryptoBot with `python main.py`.
2. Open the KryptoBot dashboard in your web browser.
3. Navigate to the Accounts page.
4. In the Platform Management section, you'll see both Alpaca and MetaTrader platforms.
5. Click "Switch to MetaTrader" to activate the MetaTrader platform.

### Trading with MetaTrader

Once MetaTrader is set as the active platform:

1. KryptoBot will use your MetaTrader account for all trading operations.
2. The dashboard will display your MetaTrader account information, positions, and trades.
3. The trading bot will execute trades on the forex pairs in your watchlist according to your strategy.

### Troubleshooting

If you encounter issues with the MetaTrader integration:

1. Ensure the MetaTrader REST API bridge is running (the expert advisor should be active on a chart).
2. Check that the API URL, key, and account number are correctly configured in your `.env` file.
3. Verify that MetaTrader is connected to your broker and has internet access.
4. Check the KryptoBot logs for any error messages related to MetaTrader.

## API Documentation

For developers who want to extend the MetaTrader integration, the REST API bridge provides the following endpoints:

- `/connect` - Connect to the MetaTrader terminal
- `/disconnect` - Disconnect from the MetaTrader terminal
- `/account` - Get account information
- `/positions` - Get current positions
- `/orders` - Get pending orders
- `/history` - Get trade history
- `/order` - Place a new order
- `/modify` - Modify an existing order
- `/close` - Close an open position
- `/delete` - Delete a pending order
- `/prices` - Get current prices for symbols
- `/ohlc` - Get OHLC data for a symbol

Refer to the MetaTrader REST API bridge documentation for more details on these endpoints.

## Security Considerations

- The MetaTrader REST API bridge runs locally on your machine and should not be exposed to the internet.
- Always use a strong API key to protect your MetaTrader integration.
- The API bridge does not store your MetaTrader login credentials. 