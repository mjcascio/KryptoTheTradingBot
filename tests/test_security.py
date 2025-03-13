"""Security tests for the KryptoBot Trading System."""

import os
import pytest
import tempfile
import json
import base64
from pathlib import Path
from unittest.mock import patch, Mock
from cryptography.fernet import Fernet
from datetime import datetime

from utils.secure_config import SecureConfig, ApiCredentials
from market.data_stream import MarketDataStream, DataStreamError
from utils.logging import setup_logging

@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def secure_config(temp_config_dir):
    """Create a secure configuration instance with a temporary directory."""
    config = SecureConfig(config_dir=temp_config_dir)
    return config

@pytest.fixture
def initialized_config(secure_config):
    """Create an initialized secure configuration."""
    secure_config.initialize("test-master-password")
    return secure_config

class TestSecureConfig:
    """Test secure configuration functionality."""

    def test_directory_permissions(self, secure_config):
        """Test configuration directory permissions."""
        assert oct(secure_config.config_dir.stat().st_mode)[-3:] == '700'

    def test_key_file_permissions(self, initialized_config):
        """Test key file permissions."""
        assert oct(initialized_config.key_file.stat().st_mode)[-3:] == '600'

    def test_config_file_permissions(self, initialized_config):
        """Test configuration file permissions."""
        assert oct(initialized_config.config_file.stat().st_mode)[-3:] == '600'

    def test_encryption_key_generation(self, initialized_config):
        """Test encryption key generation."""
        assert initialized_config._fernet is not None
        assert isinstance(initialized_config._fernet, Fernet)

    def test_invalid_master_password(self, initialized_config):
        """Test loading with invalid master password."""
        with pytest.raises(ValueError, match="Invalid master password"):
            initialized_config.load("wrong-password")

    def test_api_credentials_encryption(self, initialized_config):
        """Test API credentials encryption."""
        # Set credentials
        creds = ApiCredentials(
            api_key="test-key",
            api_secret="test-secret"
        )
        initialized_config.set_api_credentials("test-source", creds)
        
        # Verify file content is encrypted
        with open(initialized_config.config_file, 'rb') as f:
            content = f.read()
            # Ensure content is base64-encoded (encrypted)
            assert base64.b64encode(base64.b64decode(content)) == content

    def test_credential_retrieval(self, initialized_config):
        """Test API credentials retrieval."""
        # Set credentials
        original_creds = ApiCredentials(
            api_key="test-key",
            api_secret="test-secret",
            passphrase="test-pass"
        )
        initialized_config.set_api_credentials("test-source", original_creds)
        
        # Retrieve and verify
        retrieved_creds = initialized_config.get_api_credentials("test-source")
        assert retrieved_creds == original_creds

    def test_config_isolation(self, initialized_config):
        """Test configuration isolation between sources."""
        creds1 = ApiCredentials(api_key="key1", api_secret="secret1")
        creds2 = ApiCredentials(api_key="key2", api_secret="secret2")
        
        initialized_config.set_api_credentials("source1", creds1)
        initialized_config.set_api_credentials("source2", creds2)
        
        assert initialized_config.get_api_credentials("source1") == creds1
        assert initialized_config.get_api_credentials("source2") == creds2

class TestMarketDataSecurity:
    """Test market data stream security."""

    @pytest.fixture
    def market_stream(self):
        """Create a market data stream instance."""
        return MarketDataStream()

    @pytest.fixture
    def mock_credentials(self):
        """Create mock API credentials."""
        return ApiCredentials(
            api_key="test-key",
            api_secret="test-secret",
            passphrase="test-pass"
        )

    def test_credential_verification(self, market_stream):
        """Test credential verification before subscription."""
        with pytest.raises(DataStreamError, match="API credentials not found"):
            async def callback(data):
                pass
            pytest.mark.asyncio(market_stream.subscribe("BTC/USD", callback))

    @pytest.mark.asyncio
    async def test_secure_websocket_connection(self, market_stream, mock_credentials, monkeypatch):
        """Test secure WebSocket connection establishment."""
        # Mock secure_config to return our test credentials
        monkeypatch.setattr(
            "utils.secure_config.secure_config.get_api_credentials",
            lambda x: mock_credentials
        )
        
        # Mock WebSocket connection
        mock_ws = Mock()
        mock_ws.__aenter__ = Mock(return_value=mock_ws)
        mock_ws.__aexit__ = Mock(return_value=None)
        mock_ws.send_json = Mock()
        
        with patch('aiohttp.ClientSession.ws_connect', return_value=mock_ws):
            async def callback(data):
                pass
            
            await market_stream.subscribe("BTC/USD", callback, source="binance")
            
            # Verify secure connection parameters were used
            assert mock_ws.send_json.called
            auth_call = mock_ws.send_json.call_args_list[0]
            assert "method" in auth_call[0][0]
            assert auth_call[0][0]["method"] == "AUTH"

    def test_sensitive_data_logging(self, market_stream, mock_credentials, caplog):
        """Test that sensitive data is not logged."""
        logger = setup_logging(__name__)
        
        # Attempt operations that might log sensitive data
        logger.info(f"Processing trade for {mock_credentials.api_key}")
        logger.error(f"Authentication failed for {mock_credentials.api_secret}")
        
        # Verify sensitive data is not in logs
        assert mock_credentials.api_key not in caplog.text
        assert mock_credentials.api_secret not in caplog.text

class TestAuthenticationSecurity:
    """Test authentication mechanisms."""

    @pytest.mark.asyncio
    async def test_alpaca_auth_headers(self, market_stream, mock_credentials, monkeypatch):
        """Test Alpaca authentication headers."""
        monkeypatch.setattr(
            "utils.secure_config.secure_config.get_api_credentials",
            lambda x: mock_credentials
        )
        
        with patch('aiohttp.ClientSession.ws_connect') as mock_connect:
            async def callback(data):
                pass
            
            await market_stream.subscribe("AAPL", callback, source="alpaca")
            
            # Verify authentication headers
            call_kwargs = mock_connect.call_args.kwargs
            assert "headers" in call_kwargs
            headers = call_kwargs["headers"]
            assert "APCA-API-KEY-ID" in headers
            assert "APCA-API-SECRET-KEY" in headers

    @pytest.mark.asyncio
    async def test_binance_signature(self, market_stream, mock_credentials, monkeypatch):
        """Test Binance signature generation."""
        monkeypatch.setattr(
            "utils.secure_config.secure_config.get_api_credentials",
            lambda x: mock_credentials
        )
        
        mock_ws = Mock()
        mock_ws.__aenter__ = Mock(return_value=mock_ws)
        mock_ws.__aexit__ = Mock(return_value=None)
        mock_ws.send_json = Mock()
        
        with patch('aiohttp.ClientSession.ws_connect', return_value=mock_ws):
            async def callback(data):
                pass
            
            await market_stream.subscribe("BTC/USD", callback, source="binance")
            
            # Verify signature in authentication message
            auth_call = mock_ws.send_json.call_args_list[0]
            auth_params = auth_call[0][0]["params"]
            assert len(auth_params) == 3  # [api_key, timestamp, signature]
            assert len(auth_params[2]) == 64  # HMAC-SHA256 signature length

    @pytest.mark.asyncio
    async def test_coinbase_authentication(self, market_stream, mock_credentials, monkeypatch):
        """Test Coinbase authentication."""
        monkeypatch.setattr(
            "utils.secure_config.secure_config.get_api_credentials",
            lambda x: mock_credentials
        )
        
        mock_ws = Mock()
        mock_ws.__aenter__ = Mock(return_value=mock_ws)
        mock_ws.__aexit__ = Mock(return_value=None)
        mock_ws.send_json = Mock()
        
        with patch('aiohttp.ClientSession.ws_connect', return_value=mock_ws):
            async def callback(data):
                pass
            
            await market_stream.subscribe("BTC/USD", callback, source="coinbase")
            
            # Verify authentication message
            auth_call = mock_ws.send_json.call_args_list[0]
            auth_data = auth_call[0][0]
            assert "signature" in auth_data
            assert "passphrase" in auth_data
            assert "timestamp" in auth_data

class TestSecurityMisconfiguration:
    """Test security misconfiguration scenarios."""

    def test_missing_config_directory(self, temp_config_dir):
        """Test handling of missing configuration directory."""
        os.rmdir(temp_config_dir)
        config = SecureConfig(config_dir=temp_config_dir)
        assert config.config_dir.exists()

    def test_corrupted_config_file(self, initialized_config):
        """Test handling of corrupted configuration file."""
        # Corrupt the config file
        with open(initialized_config.config_file, 'wb') as f:
            f.write(b'corrupted data')
        
        with pytest.raises(ValueError, match="Invalid master password or corrupted config"):
            initialized_config.load("test-master-password")

    def test_permission_changes(self, initialized_config):
        """Test detection of permission changes."""
        # Change permissions to be too open
        initialized_config.config_file.chmod(0o644)
        
        with pytest.raises(ValueError, match="Configuration file has incorrect permissions"):
            initialized_config.load("test-master-password") 