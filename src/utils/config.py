"""Configuration management for the trading bot."""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the trading bot."""
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration manager.
        
        Args:
            config_path: Path to config file, defaults to config.json in current directory
        """
        self.config_path = config_path or 'config.json'
        self.config: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found at {self.config_path}")
                self._create_default_config()
                return
                
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._create_default_config()
            
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
                
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
                logger.info(f"Saved configuration to {self.config_path}")
                
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            
    def _create_default_config(self) -> None:
        """Create default configuration."""
        self.config = {
            "trading": {
                "symbols": ["BTC/USD", "ETH/USD"],
                "timeframe": "1m",
                "max_positions": 3,
                "position_size": 0.1,  # 10% of available balance
                "stop_loss": 0.02,     # 2% stop loss
                "take_profit": 0.05    # 5% take profit
            },
            "broker": {
                "name": "binance",
                "api_key": "",
                "api_secret": "",
                "testnet": True
            },
            "market_data": {
                "cache_enabled": True,
                "cache_expiry": 60,
                "max_workers": 4
            },
            "risk": {
                "max_drawdown": 0.1,   # 10% max drawdown
                "daily_loss_limit": 0.05  # 5% daily loss limit
            },
            "monitoring": {
                "telegram_enabled": False,
                "telegram_bot_token": "",
                "telegram_chat_id": "",
                "log_level": "INFO",
                "metrics_enabled": True,
                "metrics_retention_days": 30
            },
            "system": {
                "pid_file": "trading_bot.pid",
                "log_file": "trading_bot.log",
                "data_dir": "data"
            }
        }
        self.save_config()
        logger.info("Created default configuration")
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the correct nested level
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        # Set the value
        config[keys[-1]] = value
        
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values.
        
        Args:
            updates: Dictionary of updates
        """
        def update_recursive(base: Dict[str, Any], updates: Dict[str, Any]) -> None:
            for key, value in updates.items():
                if isinstance(value, dict) and key in base:
                    update_recursive(base[key], value)
                else:
                    base[key] = value
                    
        update_recursive(self.config, updates)
        
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if configuration is valid
        """
        required_fields = [
            'trading.symbols',
            'trading.timeframe',
            'broker.name',
            'system.pid_file',
            'system.log_file'
        ]
        
        for field in required_fields:
            if not self.get(field):
                logger.error(f"Missing required configuration: {field}")
                return False
                
        # Validate trading parameters
        if not isinstance(self.get('trading.symbols', []), list):
            logger.error("trading.symbols must be a list")
            return False
            
        if self.get('trading.position_size', 0) <= 0:
            logger.error("trading.position_size must be positive")
            return False
            
        # Validate risk parameters
        if self.get('risk.max_drawdown', 0) <= 0:
            logger.error("risk.max_drawdown must be positive")
            return False
            
        return True 