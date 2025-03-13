"""API security utilities for the KryptoBot Trading System."""

import logging
import time
import hashlib
import hmac
import base64
import secrets
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import jwt

logger = logging.getLogger(__name__)

class APISecurityConfig:
    """Configuration for API security."""
    
    def __init__(self, 
                 key_rotation_days: int = 30, 
                 rate_limit_per_minute: int = 60,
                 max_request_size: int = 1024 * 1024):
        """Initialize API security configuration.
        
        Args:
            key_rotation_days: Number of days before API keys are rotated
            rate_limit_per_minute: Maximum number of requests per minute
            max_request_size: Maximum request size in bytes
        """
        self.key_rotation_days = key_rotation_days
        self.rate_limit_per_minute = rate_limit_per_minute
        self.max_request_size = max_request_size
        
class APISecurityManager:
    """Manager for API security operations."""
    
    def __init__(self, config: APISecurityConfig):
        """Initialize API security manager.
        
        Args:
            config: API security configuration
        """
        self.config = config
        self.api_keys = {}
        self.request_counts = {}
        self.last_rotation = datetime.now()
        self.secret_key = self._generate_secret_key()
        logger.info("API security manager initialized")
        
    def _generate_secret_key(self) -> str:
        """Generate a new secret key.
        
        Returns:
            New secret key
        """
        return secrets.token_hex(32)
        
    def create_api_key(self, user_id: str, permissions: List[str]) -> Dict[str, Any]:
        """Create a new API key for a user.
        
        Args:
            user_id: User identifier
            permissions: List of permissions for the API key
            
        Returns:
            Dictionary containing API key information
        """
        api_key = secrets.token_hex(16)
        api_secret = secrets.token_hex(32)
        
        # Store hashed secret
        secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
        
        # Create API key record
        self.api_keys[api_key] = {
            'user_id': user_id,
            'secret_hash': secret_hash,
            'permissions': permissions,
            'created_at': datetime.now(),
            'last_used': None,
            'enabled': True
        }
        
        logger.info(f"Created API key for user {user_id}")
        
        # Return key and secret to user (this is the only time the secret is available)
        return {
            'api_key': api_key,
            'api_secret': api_secret,
            'permissions': permissions,
            'created_at': self.api_keys[api_key]['created_at'].isoformat()
        }
        
    def validate_request(self, api_key: str, signature: str, timestamp: str, payload: str) -> bool:
        """Validate an API request.
        
        Args:
            api_key: API key
            signature: Request signature
            timestamp: Request timestamp
            payload: Request payload
            
        Returns:
            True if the request is valid, False otherwise
        """
        # Check if API key exists
        if api_key not in self.api_keys:
            logger.warning(f"Invalid API key: {api_key}")
            return False
            
        # Check if API key is enabled
        if not self.api_keys[api_key]['enabled']:
            logger.warning(f"Disabled API key used: {api_key}")
            return False
            
        # Check rate limit
        if not self._check_rate_limit(api_key):
            logger.warning(f"Rate limit exceeded for API key: {api_key}")
            return False
            
        # Update last used timestamp
        self.api_keys[api_key]['last_used'] = datetime.now()
        
        # For now, return True (in a real implementation, we would validate the signature)
        return True
        
    def _check_rate_limit(self, api_key: str) -> bool:
        """Check if an API key has exceeded its rate limit.
        
        Args:
            api_key: API key to check
            
        Returns:
            True if the rate limit is not exceeded, False otherwise
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Initialize request count if not exists
        if api_key not in self.request_counts:
            self.request_counts[api_key] = []
            
        # Remove requests older than 1 minute
        self.request_counts[api_key] = [
            ts for ts in self.request_counts[api_key] if ts > minute_ago
        ]
        
        # Check if rate limit is exceeded
        if len(self.request_counts[api_key]) >= self.config.rate_limit_per_minute:
            return False
            
        # Add current request
        self.request_counts[api_key].append(now)
        return True
        
    def rotate_keys_if_needed(self) -> None:
        """Rotate API keys if needed based on configuration."""
        now = datetime.now()
        days_since_rotation = (now - self.last_rotation).days
        
        if days_since_rotation >= self.config.key_rotation_days:
            logger.info("Rotating API keys")
            self._rotate_keys()
            self.last_rotation = now
            
    def _rotate_keys(self) -> None:
        """Rotate all API keys."""
        # Generate new secret key
        self.secret_key = self._generate_secret_key()
        
        # Mark old keys for rotation
        for api_key, key_data in self.api_keys.items():
            # Only rotate keys that have been used
            if key_data['last_used'] is not None:
                # Create a new key with the same permissions
                new_key_data = self.create_api_key(
                    key_data['user_id'],
                    key_data['permissions']
                )
                
                # Disable old key after a grace period (in a real implementation)
                # For now, we'll just log it
                logger.info(f"Key {api_key} marked for rotation")
                
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key.
        
        Args:
            api_key: API key to revoke
            
        Returns:
            True if the key was revoked, False otherwise
        """
        if api_key in self.api_keys:
            self.api_keys[api_key]['enabled'] = False
            logger.info(f"Revoked API key: {api_key}")
            return True
        return False
        
    def generate_jwt_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """Generate a JWT token for a user.
        
        Args:
            user_id: User identifier
            expires_in_hours: Token expiration time in hours
            
        Returns:
            JWT token
        """
        payload = {
            'sub': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
        
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None 