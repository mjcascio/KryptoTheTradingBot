# KryptoBot Trading Dashboard

This dashboard provides a web interface for monitoring and managing your KryptoBot trading activities.

## Quick Start

### Starting the Dashboard

To start the dashboard manually:

```bash
./start_dashboard.sh
```

The dashboard will be available at: http://localhost:5001

### Stopping the Dashboard

To stop the dashboard:

```bash
./stop_dashboard.sh
```

### Restarting the Dashboard

To restart the dashboard:

```bash
./restart_dashboard.sh
```

## Installing as a macOS Service

To install the dashboard as a service that starts automatically when you log in:

```bash
./install_dashboard_service.sh
```

After installation, you can manage the service with:

- Start: `launchctl start com.krypto.dashboard`
- Stop: `launchctl stop com.krypto.dashboard`
- Uninstall: `launchctl unload ~/Library/LaunchAgents/com.krypto.dashboard.plist`

## Dashboard Features

- **Real-time Trading Data**: View your account equity, positions, and trade history
- **Trade Monitoring**: Monitor bot activity and trade logs
- **Account Management**: Manage multiple trading accounts
- **System Status**: Monitor system resources and bot status

## Troubleshooting

If the dashboard fails to start:

1. Check the logs in `logs/dashboard.log`
2. Ensure port 5001 is not in use by another application
3. Verify that the virtual environment is activated
4. Make sure all required dependencies are installed

If you encounter issues with the macOS service:

1. Check the logs in `logs/dashboard_launch.log` and `logs/dashboard_launch_error.log`
2. Try restarting the service manually with `launchctl stop com.krypto.dashboard` followed by `launchctl start com.krypto.dashboard`

## Advanced Configuration

The dashboard configuration can be modified in `dashboard.py`. Key settings include:

- Port: The default port is 5001
- Host: The default host is 0.0.0.0 (accessible from any network interface)
- Threading: The dashboard uses threading for better performance 