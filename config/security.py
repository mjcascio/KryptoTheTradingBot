"""Security configuration and utilities for the KryptoBot Trading System."""

import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv

class SecurityError(Exception):
    """Exception raised for security-related errors."""
    pass

class SecureConfig:
    """Handles secure configuration and sensitive data."""

    def __init__(self) -> None:
        """Initialize secure configuration handler."""
        self._load_environment()
        self._init_encryption()
        self._validate_required_vars()

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path('.env')
        if not env_path.exists():
            raise SecurityError(
                "Environment file not found. Please create .env file from .env.template"
            )
        load_dotenv()

    def _init_encryption(self) -> None:
        """Initialize encryption key for sensitive data."""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            with open('.env', 'a') as f:
                f.write(f'\nENCRYPTION_KEY={key.decode()}\n')
        
        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise SecurityError(f"Failed to initialize encryption: {str(e)}")

    def _validate_required_vars(self) -> None:
        """Validate that all required environment variables are present."""
        required_vars = {
            'API_KEYS': [
                'ALPACA_API_KEY',
                'ALPACA_SECRET_KEY'
            ],
            'BROKER_CONFIG': [
                'MT_SERVER',
                'MT_PORT',
                'MT_USERNAME',
                'MT_PASSWORD'
            ],
            'EMAIL': [
                'EMAIL_USERNAME',
                'EMAIL_PASSWORD'
            ],
            'SECURITY': [
                'JWT_SECRET_KEY'
            ]
        }

        missing_vars = []
        for category, vars in required_vars.items():
            for var in vars:
                if not os.getenv(var):
                    missing_vars.append(f"{category}: {var}")

        if missing_vars:
            raise SecurityError(
                "Missing required environment variables:\n" +
                "\n".join(missing_vars)
            )

    def get_api_credentials(self, platform: str) -> Dict[str, str]:
        """Get API credentials for a trading platform.
        
        Args:
            platform: Trading platform name (e.g., 'alpaca', 'metatrader')
            
        Returns:
            Dictionary containing API credentials
            
        Raises:
            SecurityError: If credentials are not found
        """
        try:
            if platform.lower() == 'alpaca':
                return {
                    'api_key': os.environ['ALPACA_API_KEY'],
                    'secret_key': os.environ['ALPACA_SECRET_KEY']
                }
            elif platform.lower() == 'metatrader':
                return {
                    'server': os.environ['MT_SERVER'],
                    'port': os.environ['MT_PORT'],
                    'username': os.environ['MT_USERNAME'],
                    'password': self.decrypt(os.environ['MT_PASSWORD'])
                }
            else:
                raise SecurityError(f"Unknown platform: {platform}")
        except KeyError as e:
            raise SecurityError(f"Missing credentials for {platform}: {str(e)}")

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data in base64 format
        """
        try:
            return base64.b64encode(
                self.cipher.encrypt(data.encode())
            ).decode()
        except Exception as e:
            raise SecurityError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted data
        """
        try:
            return self.cipher.decrypt(
                base64.b64decode(encrypted_data)
            ).decode()
        except Exception as e:
            raise SecurityError(f"Decryption failed: {str(e)}")

    def get_jwt_secret(self) -> str:
        """Get JWT secret key for authentication.
        
        Returns:
            JWT secret key
        """
        secret = os.getenv('JWT_SECRET_KEY')
        if not secret:
            raise SecurityError("JWT secret key not found")
        return secret

    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in dictionaries for logging.
        
        Args:
            data: Dictionary containing potentially sensitive data
            
        Returns:
            Dictionary with sensitive data masked
        """
        sensitive_keys = {
            'password', 'secret', 'key', 'token', 'auth',
            'api_key', 'secret_key', 'private_key'
        }
        
        masked_data = {}
        for key, value in data.items():
            if any(s in key.lower() for s in sensitive_keys):
                masked_data[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_data(value)
            else:
                masked_data[key] = value
        return masked_data

# Create global instance
secure_config = SecureConfig() 