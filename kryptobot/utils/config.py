"""
Configuration Management Module - Handles application configuration.

This module is responsible for loading, validating, and providing access
to application configuration from various sources (files, environment variables).
"""

import os
import yaml
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration manager for the application.
    
    This class is responsible for loading, validating, and providing access
    to application configuration from various sources (files, environment variables).
    
    Attributes:
        config (Dict[str, Any]): Configuration dictionary
        config_path (str): Path to the configuration file
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to the configuration file
        """
        self.config = {}
        self.config_path = config_path
        
        # Load configuration from file if provided
        if config_path:
            self.load_from_file(config_path)
        
        # Load configuration from environment variables
        self.load_from_env()
        
        # Set default values for required configuration
        self.set_defaults()
        
        logger.info("Configuration loaded")
    
    def load_from_file(self, config_path: str):
        """
        Load configuration from a file.
        
        Args:
            config_path (str): Path to the configuration file
            
        Raises:
            FileNotFoundError: If the configuration file is not found
            ValueError: If the configuration file is invalid
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            # Determine file type from extension
            _, ext = os.path.splitext(config_path)
            
            if ext.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    self.config.update(yaml.safe_load(f))
            elif ext.lower() == '.json':
                with open(config_path, 'r') as f:
                    self.config.update(json.load(f))
            else:
                raise ValueError(f"Unsupported configuration file format: {ext}")
            
            logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from file: {e}")
            raise
    
    def load_from_env(self):
        """
        Load configuration from environment variables.
        
        Environment variables are loaded with the following prefixes:
        - KRYPTOBOT_: General configuration
        - ALPACA_: Alpaca broker configuration
        - MT_: MetaTrader broker configuration
        """
        # Load general configuration
        for key, value in os.environ.items():
            if key.startswith('KRYPTOBOT_'):
                config_key = key[10:].lower()
                self.config[config_key] = self._parse_env_value(value)
        
        # Load Alpaca configuration
        alpaca_config = {}
        for key, value in os.environ.items():
            if key.startswith('ALPACA_'):
                config_key = key[7:].lower()
                alpaca_config[config_key] = self._parse_env_value(value)
        
        if alpaca_config:
            self.config.setdefault('platforms', {})
            self.config['platforms']['alpaca'] = {
                'name': 'Alpaca',
                'type': 'stocks',
                'description': 'Alpaca Markets for stocks and crypto trading',
                'icon': 'fa-chart-line',
                **alpaca_config
            }
        
        # Load MetaTrader configuration
        mt_config = {}
        for key, value in os.environ.items():
            if key.startswith('MT_'):
                config_key = key[3:].lower()
                mt_config[config_key] = self._parse_env_value(value)
        
        if mt_config:
            self.config.setdefault('platforms', {})
            self.config['platforms']['metatrader'] = {
                'name': 'MetaTrader',
                'type': 'forex',
                'description': 'MetaTrader for forex trading',
                'icon': 'fa-exchange-alt',
                **mt_config
            }
        
        logger.info("Configuration loaded from environment variables")
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parse an environment variable value.
        
        Args:
            value (str): Environment variable value
            
        Returns:
            Any: Parsed value
        """
        # Try to parse as JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # If not JSON, return as string
            return value
    
    def set_defaults(self):
        """
        Set default values for required configuration.
        """
        # Trading parameters
        self.config.setdefault('max_position_size_pct', 0.05)
        self.config.setdefault('total_risk_pct', 0.02)
        self.config.setdefault('max_trades_per_day', 5)
        self.config.setdefault('min_success_probability', 0.65)
        self.config.setdefault('min_position_size', 1000)
        
        # Technical analysis parameters
        self.config.setdefault('breakout_params', {
            'volume_threshold': 1.5,
            'price_threshold': 0.015,
            'lookback_period': 15,
            'consolidation_threshold': 0.015
        })
        
        self.config.setdefault('trend_params', {
            'short_ma': 9,
            'medium_ma': 20,
            'long_ma': 50,
            'rsi_period': 14,
            'rsi_overbought': 65,
            'rsi_oversold': 35,
            'volume_ma': 20
        })
        
        # Risk management
        self.config.setdefault('stop_loss_pct', 0.02)
        self.config.setdefault('take_profit_pct', 0.06)
        self.config.setdefault('max_daily_loss_pct', 0.05)
        self.config.setdefault('position_sizing_volatility_multiplier', 1.5)
        
        # Market hours
        self.config.setdefault('market_open', '09:30')
        self.config.setdefault('market_close', '16:00')
        self.config.setdefault('timezone', 'America/New_York')
        
        # Sleep mode
        self.config.setdefault('sleep_mode', {
            'enabled': True,
            'sleep_outside_market_hours': True,
            'sleep_when_no_opportunities': True,
            'max_daily_loss_sleep': True
        })
        
        # Watchlists
        if 'watchlist' not in self.config:
            self.config['watchlist'] = [
                # Tech stocks
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'AMD', 'TSLA',
                # Financial stocks
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA', 'PYPL',
                # Healthcare stocks
                'JNJ', 'PFE', 'MRK', 'UNH', 'ABBV', 'LLY', 'TMO', 'DHR',
                # Consumer stocks
                'PG', 'KO', 'PEP', 'WMT', 'COST', 'MCD', 'SBUX', 'NKE'
            ]
        
        if 'forex_watchlist' not in self.config:
            self.config['forex_watchlist'] = [
                'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD',
                'EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY', 'CHFJPY', 'NZDJPY'
            ]
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key
            default (Any, optional): Default value if key is not found
            
        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            key (str): Configuration key
            value (Any): Configuration value
        """
        self.config[key] = value
    
    def save(self, config_path: str = None):
        """
        Save the configuration to a file.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If not provided, the original config_path is used.
                
        Raises:
            ValueError: If no config_path is provided and no original config_path exists
        """
        config_path = config_path or self.config_path
        
        if not config_path:
            raise ValueError("No configuration file path provided")
        
        try:
            # Determine file type from extension
            _, ext = os.path.splitext(config_path)
            
            if ext.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif ext.lower() == '.json':
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration file format: {ext}")
            
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to file: {e}")
            raise
    
    def __getitem__(self, key: str) -> Any:
        """
        Get a configuration value using dictionary syntax.
        
        Args:
            key (str): Configuration key
            
        Returns:
            Any: Configuration value
            
        Raises:
            KeyError: If the key is not found
        """
        if key not in self.config:
            raise KeyError(f"Configuration key not found: {key}")
        
        return self.config[key]
    
    def __setitem__(self, key: str, value: Any):
        """
        Set a configuration value using dictionary syntax.
        
        Args:
            key (str): Configuration key
            value (Any): Configuration value
        """
        self.config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        Args:
            key (str): Configuration key
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        return key in self.config
    
    def __str__(self) -> str:
        """
        Get a string representation of the configuration.
        
        Returns:
            str: String representation of the configuration
        """
        return str(self.config)
    
    def __repr__(self) -> str:
        """
        Get a string representation of the configuration.
        
        Returns:
            str: String representation of the configuration
        """
        return f"Config({self.config_path})"

# Create a global configuration instance
config = Config()

# Export configuration values for backward compatibility
WATCHLIST = config.get('watchlist', [])
FOREX_WATCHLIST = config.get('forex_watchlist', [])
MAX_TRADES_PER_DAY = config.get('max_trades_per_day', 5)
MIN_SUCCESS_PROBABILITY = config.get('min_success_probability', 0.65)
MAX_POSITION_SIZE_PCT = config.get('max_position_size_pct', 0.05)
STOP_LOSS_PCT = config.get('stop_loss_pct', 0.02)
TAKE_PROFIT_PCT = config.get('take_profit_pct', 0.06)
MAX_DAILY_LOSS_PCT = config.get('max_daily_loss_pct', 0.05)
MARKET_OPEN = config.get('market_open', '09:30')
MARKET_CLOSE = config.get('market_close', '16:00')
TIMEZONE = config.get('timezone', 'America/New_York')
PLATFORMS = config.get('platforms', {})
SLEEP_MODE = config.get('sleep_mode', {
    'enabled': True,
    'sleep_outside_market_hours': True,
    'sleep_when_no_opportunities': True,
    'max_daily_loss_sleep': True
}) 