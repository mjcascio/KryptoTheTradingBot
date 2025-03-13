# KryptoBot Trading System - Fixes Documentation

## Issues Fixed

### 1. SSL Certificate Path Issue
The trading bot was looking for SSL certificates in the wrong path (`venv` instead of `.venv`). This was causing errors when making HTTPS requests to external APIs.

### 2. Timezone Localization Issue
The `pd.Timestamp.tz_localize()` method was not handling `None` timezone correctly, causing errors in the market data module.

## Changes Made

### 1. Environment Variables
- Updated the `.env` file to include both `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` with the correct path to the SSL certificates in the `.venv` directory.

### 2. Source Code Modifications
- **market_data.py**: Added proper loading of environment variables and patched the pandas Timestamp.tz_localize method.
- **brokers/alpaca_broker.py**: Added proper loading of environment variables for SSL certificate paths.
- **main.py**: Added direct patching of the pandas Timestamp.tz_localize method as a fallback if the fix_timezone module is not found.
- **mt_api_bridge.py**: Added SSL certificate path configuration.
- **dashboard.py**: Added SSL certificate path configuration.

### 3. New Scripts
- **start_all.sh**: A comprehensive script to start all components of the trading bot system with the correct environment variables.
- **stop_all.sh**: A script to safely stop all components of the trading bot system.

## How to Use

### Starting the Trading Bot System
```bash
./start_all.sh
```
This script will:
1. Stop any existing processes
2. Set the correct environment variables
3. Start the MetaTrader API bridge
4. Start the trading bot
5. Start the dashboard
6. Verify all processes are running

### Stopping the Trading Bot System
```bash
./stop_all.sh
```
This script will:
1. Stop all running processes using their PID files
2. Ensure all processes are stopped by name
3. Verify all processes are stopped

## Accessing the Dashboard
The dashboard is accessible at: http://localhost:5001

## Monitoring Logs
- Trading bot logs: `logs/trading_bot.out`
- MetaTrader API bridge logs: `logs/mt_api_bridge.out`
- Dashboard logs: `logs/dashboard.out`

## Troubleshooting
If you encounter any issues:
1. Check the log files for errors
2. Ensure the SSL certificate paths are correct in the `.env` file
3. Verify that the virtual environment is activated before running the scripts
4. Make sure all required dependencies are installed in the virtual environment 