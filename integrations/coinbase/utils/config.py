"""Configuration management system."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """API configuration."""
    
    base_url: str
    api_key: str
    api_secret: str
    passphrase: str
    sandbox: bool = False
    rate_limit: int = 10
    timeout: float = 30.0

@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    path: str
    max_connections: int = 10
    timeout: float = 30.0
    cleanup_interval: int = 86400  # 24 hours
    max_age: int = 2592000  # 30 days

@dataclass
class CacheConfig:
    """Cache configuration."""
    
    enabled: bool = True
    ttl: Dict[str, int] = None
    cleanup_interval: int = 300  # 5 minutes
    max_size: int = 10000

@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    
    enabled: bool = True
    interval: float = 1.0
    history_size: int = 3600
    log_level: str = "INFO"
    metrics_port: int = 9090

@dataclass
class Config:
    """Global configuration."""
    
    api: APIConfig
    database: DatabaseConfig
    cache: CacheConfig
    monitoring: MonitoringConfig
    log_dir: Optional[str] = None
    debug: bool = False

class ConfigManager:
    """Configuration manager."""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Configuration directory
        """
        self.config_dir = config_dir or os.getenv(
            "COINBASE_CONFIG_DIR",
            str(Path.home() / ".coinbase")
        )
        self.config_file = Path(self.config_dir) / "config.json"
        self.env_file = Path(self.config_dir) / ".env"
        
        # Create config directory if it doesn't exist
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Config:
        """Load configuration from files.
        
        Returns:
            Configuration object
        """
        # Load environment variables
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Load config file
        config_data = {}
        if self.config_file.exists():
            with open(self.config_file) as f:
                config_data = json.load(f)
        
        # API configuration
        api_config = APIConfig(
            base_url=os.getenv(
                "COINBASE_API_URL",
                config_data.get("api", {}).get(
                    "base_url",
                    "https://api.pro.coinbase.com"
                )
            ),
            api_key=os.getenv(
                "COINBASE_API_KEY",
                config_data.get("api", {}).get("api_key", "")
            ),
            api_secret=os.getenv(
                "COINBASE_API_SECRET",
                config_data.get("api", {}).get("api_secret", "")
            ),
            passphrase=os.getenv(
                "COINBASE_PASSPHRASE",
                config_data.get("api", {}).get("passphrase", "")
            ),
            sandbox=os.getenv(
                "COINBASE_SANDBOX",
                config_data.get("api", {}).get("sandbox", "")
            ).lower() == "true",
            rate_limit=int(os.getenv(
                "COINBASE_RATE_LIMIT",
                config_data.get("api", {}).get("rate_limit", 10)
            )),
            timeout=float(os.getenv(
                "COINBASE_TIMEOUT",
                config_data.get("api", {}).get("timeout", 30.0)
            ))
        )
        
        # Database configuration
        database_config = DatabaseConfig(
            path=os.getenv(
                "COINBASE_DB_PATH",
                config_data.get("database", {}).get(
                    "path",
                    str(Path(self.config_dir) / "coinbase.db")
                )
            ),
            max_connections=int(os.getenv(
                "COINBASE_DB_MAX_CONNECTIONS",
                config_data.get("database", {}).get("max_connections", 10)
            )),
            timeout=float(os.getenv(
                "COINBASE_DB_TIMEOUT",
                config_data.get("database", {}).get("timeout", 30.0)
            )),
            cleanup_interval=int(os.getenv(
                "COINBASE_DB_CLEANUP_INTERVAL",
                config_data.get("database", {}).get("cleanup_interval", 86400)
            )),
            max_age=int(os.getenv(
                "COINBASE_DB_MAX_AGE",
                config_data.get("database", {}).get("max_age", 2592000)
            ))
        )
        
        # Cache configuration
        cache_config = CacheConfig(
            enabled=os.getenv(
                "COINBASE_CACHE_ENABLED",
                config_data.get("cache", {}).get("enabled", "true")
            ).lower() == "true",
            ttl=config_data.get("cache", {}).get("ttl", {
                "market_data": 60,
                "order_book": 1,
                "ticker": 1
            }),
            cleanup_interval=int(os.getenv(
                "COINBASE_CACHE_CLEANUP_INTERVAL",
                config_data.get("cache", {}).get("cleanup_interval", 300)
            )),
            max_size=int(os.getenv(
                "COINBASE_CACHE_MAX_SIZE",
                config_data.get("cache", {}).get("max_size", 10000)
            ))
        )
        
        # Monitoring configuration
        monitoring_config = MonitoringConfig(
            enabled=os.getenv(
                "COINBASE_MONITORING_ENABLED",
                config_data.get("monitoring", {}).get("enabled", "true")
            ).lower() == "true",
            interval=float(os.getenv(
                "COINBASE_MONITORING_INTERVAL",
                config_data.get("monitoring", {}).get("interval", 1.0)
            )),
            history_size=int(os.getenv(
                "COINBASE_MONITORING_HISTORY_SIZE",
                config_data.get("monitoring", {}).get("history_size", 3600)
            )),
            log_level=os.getenv(
                "COINBASE_LOG_LEVEL",
                config_data.get("monitoring", {}).get("log_level", "INFO")
            ),
            metrics_port=int(os.getenv(
                "COINBASE_METRICS_PORT",
                config_data.get("monitoring", {}).get("metrics_port", 9090)
            ))
        )
        
        return Config(
            api=api_config,
            database=database_config,
            cache=cache_config,
            monitoring=monitoring_config,
            log_dir=os.getenv(
                "COINBASE_LOG_DIR",
                config_data.get("log_dir")
            ),
            debug=os.getenv(
                "COINBASE_DEBUG",
                config_data.get("debug", "false")
            ).lower() == "true"
        )
    
    def save_config(self) -> None:
        """Save configuration to file."""
        config_data = {
            "api": {
                "base_url": self.config.api.base_url,
                "sandbox": self.config.api.sandbox,
                "rate_limit": self.config.api.rate_limit,
                "timeout": self.config.api.timeout
            },
            "database": {
                "path": self.config.database.path,
                "max_connections": self.config.database.max_connections,
                "timeout": self.config.database.timeout,
                "cleanup_interval": self.config.database.cleanup_interval,
                "max_age": self.config.database.max_age
            },
            "cache": {
                "enabled": self.config.cache.enabled,
                "ttl": self.config.cache.ttl,
                "cleanup_interval": self.config.cache.cleanup_interval,
                "max_size": self.config.cache.max_size
            },
            "monitoring": {
                "enabled": self.config.monitoring.enabled,
                "interval": self.config.monitoring.interval,
                "history_size": self.config.monitoring.history_size,
                "log_level": self.config.monitoring.log_level,
                "metrics_port": self.config.monitoring.metrics_port
            },
            "log_dir": self.config.log_dir,
            "debug": self.config.debug
        }
        
        with open(self.config_file, "w") as f:
            json.dump(config_data, f, indent=4)
        
        logger.info(f"Configuration saved to {self.config_file}")
    
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if configuration is valid
        """
        # Check required API settings
        if not all([
            self.config.api.base_url,
            self.config.api.api_key,
            self.config.api.api_secret,
            self.config.api.passphrase
        ]):
            logger.error("Missing required API configuration")
            return False
        
        # Check database path
        db_path = Path(self.config.database.path)
        if not db_path.parent.exists():
            logger.error(f"Database directory does not exist: {db_path.parent}")
            return False
        
        # Check log directory
        if self.config.log_dir and not Path(self.config.log_dir).exists():
            logger.error(f"Log directory does not exist: {self.config.log_dir}")
            return False
        
        return True
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration.
        
        Returns:
            API configuration
        """
        return self.config.api
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration.
        
        Returns:
            Database configuration
        """
        return self.config.database
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration.
        
        Returns:
            Cache configuration
        """
        return self.config.cache
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration.
        
        Returns:
            Monitoring configuration
        """
        return self.config.monitoring 