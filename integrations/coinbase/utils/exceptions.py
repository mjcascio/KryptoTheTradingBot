"""Custom exceptions for Coinbase integration."""

class CoinbaseError(Exception):
    """Base exception for Coinbase integration."""
    pass

class CoinbaseAuthError(CoinbaseError):
    """Authentication error."""
    pass

class CoinbaseAPIError(CoinbaseError):
    """API error."""
    pass

class CoinbaseRateLimitError(CoinbaseError):
    """Rate limit exceeded error."""
    pass

class CoinbaseConnectionError(CoinbaseError):
    """Connection error."""
    pass

class CoinbaseValidationError(CoinbaseError):
    """Validation error."""
    pass 