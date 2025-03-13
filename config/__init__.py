"""
Configuration module for KryptoBot Trading System.

This module manages all configuration settings and constants used throughout
the application. It provides a centralized location for managing system
parameters, trading settings, and environment-specific configurations.

Key Components:
    - Settings: Environment-specific configuration and parameters
    - Constants: System-wide constants and default values
    - Strategy Parameters: Parameters for different trading strategies
    - Environment Variables: Secure handling of sensitive credentials

Example:
    from config.settings import (
        MAX_POSITION_SIZE_PCT,
        STOP_LOSS_PCT,
        DASHBOARD_PORT
    )
    from config.constants import (
        SECTOR_MAPPING,
        RECOMMENDED_ALLOCATIONS,
        DEFAULT_RISK_METRICS
    )
    from config.strategy_params import (
        BREAKOUT_PARAMS,
        TREND_PARAMS,
        MEAN_REVERSION_PARAMS
    )

    # Access trading parameters
    max_position = account_value * MAX_POSITION_SIZE_PCT
    stop_loss = entry_price * (1 - STOP_LOSS_PCT)

    # Get sector information
    sector = SECTOR_MAPPING.get(symbol, "Unknown")
    allocation = RECOMMENDED_ALLOCATIONS["neutral_market"][sector]
    
    # Access strategy parameters
    lookback_period = BREAKOUT_PARAMS["lookback_period"]
    fast_ema = TREND_PARAMS["fast_ema"]
"""

from .settings import *
from .constants import *
from .strategy_params import * 