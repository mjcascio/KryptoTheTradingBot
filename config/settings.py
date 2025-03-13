"""Settings configuration for the KryptoBot Trading System."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import certifi

# Base directories
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / 'logs'
DATA_DIR = BASE_DIR / 'data'

# Ensure directories exist
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Log file paths
DASHBOARD_LOG_DIR = LOG_DIR / 'dashboard'
TRADING_BOT_LOG = LOG_DIR / 'trading_bot.log'
DASHBOARD_LOG = LOG_DIR / 'dashboard.log'
API_LOG = LOG_DIR / 'api.log'
ERROR_LOG = LOG_DIR / 'error.log'

class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass

class Settings:
    """Configuration settings manager.
    
    This class handles loading and accessing configuration settings from both
    YAML files and environment variables. It ensures that sensitive data is
    properly handled and that all required settings are present.
    """
    
    def __init__(self):
        """Initialize the settings manager."""
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML and environment variables."""
        try:
            # Load environment variables
            load_dotenv()
            
            # Load YAML configuration
            config_path = Path(__file__).parent / 'settings.yaml'
            if not config_path.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(config_path) as f:
                self._config = yaml.safe_load(f)
            
            # Validate and process configuration
            self._validate_config()
            self._process_environment_variables()
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def _validate_config(self):
        """Validate the loaded configuration."""
        required_sections = ['dashboard', 'trading', 'market', 'platforms', 'logging']
        for section in required_sections:
            if section not in self._config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
    
    def _process_environment_variables(self):
        """Process and validate environment variables."""
        # Required environment variables
        required_env_vars = {
            'alpaca': ['ALPACA_API_KEY'],  # ALPACA_SECRET_KEY is now optional
            # MetaTrader is now optional
            # 'metatrader': ['MT_SERVER', 'MT_PORT', 'MT_USERNAME', 'MT_PASSWORD'],
            'email': ['EMAIL_USERNAME', 'EMAIL_PASSWORD'],
            'ssl': ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE']
        }
        
        # Check for required variables
        missing_vars = []
        for section, vars in required_env_vars.items():
            # Skip metatrader section if it's disabled in the config
            if section == 'metatrader' and not self._config.get('platforms', {}).get('metatrader', {}).get('enabled', False):
                continue
                
            for var in vars:
                if not os.getenv(var):
                    missing_vars.append(var)
        
        if missing_vars:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.
        
        Args:
            path: Configuration path (e.g., 'trading.max_trades_per_day')
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        parts = path.split('.')
        value = self._config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
                
        return value
    
    def set(self, path: str, value: Any) -> None:
        """Set a configuration value using dot notation.
        
        Args:
            path: Configuration path (e.g., 'trading.max_trades_per_day')
            value: Value to set
        """
        parts = path.split('.')
        config = self._config
        
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
            
        config[parts[-1]] = value
    
    def get_env(self, var_name: str, required: bool = True) -> Optional[str]:
        """Get an environment variable.
        
        Args:
            var_name: Name of the environment variable
            required: Whether the variable is required
            
        Returns:
            Environment variable value or None
            
        Raises:
            ConfigurationError: If a required variable is missing
        """
        value = os.getenv(var_name)
        if required and not value:
            raise ConfigurationError(f"Required environment variable not set: {var_name}")
        return value
    
    @property
    def dashboard(self) -> Dict[str, Any]:
        """Get dashboard configuration."""
        return self._config.get('dashboard', {})
    
    @property
    def trading(self) -> Dict[str, Any]:
        """Get trading configuration."""
        return self._config.get('trading', {})
    
    @property
    def market(self) -> Dict[str, Any]:
        """Get market configuration."""
        return self._config.get('market', {})
    
    @property
    def platforms(self) -> Dict[str, Any]:
        """Get platforms configuration."""
        return self._config.get('platforms', {})
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get('logging', {})
    
    @property
    def notifications(self) -> Dict[str, Any]:
        """Get notifications configuration."""
        return self._config.get('notifications', {})

# Create global settings instance
settings = Settings()

# Export commonly used settings
DASHBOARD_HOST = settings.get('dashboard.host', '0.0.0.0')
DASHBOARD_PORT = settings.get('dashboard.port', 5001)
DASHBOARD_TEMPLATE_DIR = settings.get('dashboard.directories.templates', 'templates')
DASHBOARD_STATIC_DIR = settings.get('dashboard.directories.static', 'static')
DASHBOARD_DATA_DIR = settings.get('dashboard.directories.data', 'data')
DASHBOARD_LOG_DIR = settings.get('dashboard.directories.logs', 'logs')
DASHBOARD_DATA_FILE = os.path.join(
    DASHBOARD_DATA_DIR,
    settings.get('dashboard.files.data', 'dashboard_data.json')
)

# Trading settings
MAX_TRADES_PER_DAY = settings.get('trading.max_trades_per_day', 10)
MIN_SUCCESS_PROBABILITY = settings.get('trading.min_success_probability', 0.6)
MAX_POSITION_SIZE_PCT = settings.get('trading.position_sizing.max_position_pct', 0.02)
MIN_POSITION_SIZE = settings.get('trading.position_sizing.min_position_size', 1000)
STOP_LOSS_PCT = settings.get('trading.risk_management.stop_loss_pct', 0.02)
TAKE_PROFIT_PCT = settings.get('trading.risk_management.take_profit_pct', 0.04)
MAX_DAILY_LOSS_PCT = settings.get('trading.risk_management.max_daily_loss_pct', 0.05)

# Market settings
TIMEZONE = settings.get('market.timezone', 'America/New_York')
MARKET_HOURS = settings.get('market.hours', {'open': '09:30:00', 'close': '16:00:00'})
DASHBOARD_UPDATE_INTERVAL = settings.get('market.update_intervals.dashboard', 5)
MARKET_CHECK_INTERVAL = settings.get('market.update_intervals.market_check', 60)

# Platform settings
PLATFORMS = settings.get('platforms', {})

# SSL settings
SSL_CERT_FILE = settings.get_env('SSL_CERT_FILE')
REQUESTS_CA_BUNDLE = settings.get_env('REQUESTS_CA_BUNDLE')

# Set SSL certificate paths in environment
os.environ['SSL_CERT_FILE'] = SSL_CERT_FILE
os.environ['REQUESTS_CA_BUNDLE'] = REQUESTS_CA_BUNDLE

# Create required directories
for directory in [DASHBOARD_DATA_DIR, DASHBOARD_TEMPLATE_DIR, DASHBOARD_LOG_DIR, DASHBOARD_STATIC_DIR]:
    os.makedirs(directory, exist_ok=True) 