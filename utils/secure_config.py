"""Secure configuration management for KryptoBot Trading System."""

import os
import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dataclasses import dataclass

from utils.logging import setup_logging

logger = setup_logging(__name__)

@dataclass
class ApiCredentials:
    """Container for API credentials."""
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None

class SecureConfig:
    """Secure configuration manager for sensitive data."""
    
    def __init__(self, config_dir: str = ".kryptobot") -> None:
        """Initialize secure configuration.
        
        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = Path.home() / config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.key_file = self.config_dir / ".key"
        self.config_file = self.config_dir / "config.encrypted"
        self._fernet: Optional[Fernet] = None
        self._config: Dict[str, Any] = {}
        
        # Ensure config directory permissions
        self.config_dir.chmod(0o700)  # Only owner can read/write

    def initialize(self, master_password: str) -> None:
        """Initialize encryption key using master password.
        
        Args:
            master_password: Master password for encryption
        """
        # Generate encryption key from password
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        
        # Save salt and create Fernet instance
        with open(self.key_file, 'wb') as f:
            f.write(salt)
        self.key_file.chmod(0o600)  # Only owner can read
        
        self._fernet = Fernet(key)
        self._save_config({})  # Initialize empty config

    def load(self, master_password: str) -> None:
        """Load configuration using master password.
        
        Args:
            master_password: Master password for decryption
        """
        if not self.key_file.exists():
            raise ValueError("Configuration not initialized")
        
        # Read salt and generate key
        with open(self.key_file, 'rb') as f:
            salt = f.read()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self._fernet = Fernet(key)
        
        # Load encrypted config
        try:
            if self.config_file.exists():
                with open(self.config_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._fernet.decrypt(encrypted_data)
                self._config = json.loads(decrypted_data)
            else:
                self._config = {}
        except Exception as e:
            raise ValueError("Invalid master password or corrupted config") from e

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save encrypted configuration.
        
        Args:
            config: Configuration dictionary
        """
        if not self._fernet:
            raise ValueError("Encryption not initialized")
        
        # Encrypt and save config
        encrypted_data = self._fernet.encrypt(json.dumps(config).encode())
        with open(self.config_file, 'wb') as f:
            f.write(encrypted_data)
        self.config_file.chmod(0o600)  # Only owner can read

    def set_api_credentials(
        self,
        source: str,
        credentials: ApiCredentials
    ) -> None:
        """Set API credentials for a data source.
        
        Args:
            source: Data source name
            credentials: API credentials
        """
        if source not in self._config:
            self._config[source] = {}
        
        self._config[source]['credentials'] = {
            'api_key': credentials.api_key,
            'api_secret': credentials.api_secret
        }
        
        if credentials.passphrase:
            self._config[source]['credentials']['passphrase'] = credentials.passphrase
        
        self._save_config(self._config)

    def get_api_credentials(self, source: str) -> Optional[ApiCredentials]:
        """Get API credentials for a data source.
        
        Args:
            source: Data source name
            
        Returns:
            API credentials or None if not found
        """
        if source not in self._config:
            return None
        
        creds = self._config[source].get('credentials')
        if not creds:
            return None
        
        return ApiCredentials(
            api_key=creds['api_key'],
            api_secret=creds['api_secret'],
            passphrase=creds.get('passphrase')
        )

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        self._save_config(self._config)

    def get_config_value(self, key: str) -> Optional[Any]:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value or None if not found
        """
        return self._config.get(key)

    def remove_config_value(self, key: str) -> None:
        """Remove a configuration value.
        
        Args:
            key: Configuration key
        """
        if key in self._config:
            del self._config[key]
            self._save_config(self._config)

# Create global instance
secure_config = SecureConfig() 