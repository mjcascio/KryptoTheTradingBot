"""Tests for the configuration management system."""

import os
import pytest
from config.settings import Settings, ConfigurationError

@pytest.mark.config
class TestSettings:
    """Test suite for Settings class."""
    
    def test_settings_initialization(self, mock_settings):
        """Test that Settings can be initialized properly."""
        assert mock_settings is not None
        assert isinstance(mock_settings._config, dict)
    
    def test_get_config_value(self, mock_settings):
        """Test retrieving configuration values using dot notation."""
        assert mock_settings.get('trading.max_trades_per_day') == 5
        assert mock_settings.get('market.timezone') == 'America/New_York'
        assert mock_settings.get('nonexistent.path', 'default') == 'default'
    
    def test_get_nested_config(self, mock_settings):
        """Test retrieving nested configuration values."""
        risk_config = mock_settings.get('trading.risk_management')
        assert isinstance(risk_config, dict)
        assert risk_config['stop_loss_pct'] == 0.02
        assert risk_config['take_profit_pct'] == 0.04
    
    def test_environment_variables(self, setup_test_env):
        """Test retrieving environment variables."""
        settings = Settings()
        assert settings.get_env('ALPACA_API_KEY') == 'test_api_key'
        assert settings.get_env('ALPACA_SECRET_KEY') == 'test_secret_key'
    
    def test_missing_environment_variable(self):
        """Test handling of missing environment variables."""
        settings = Settings()
        with pytest.raises(ConfigurationError):
            settings.get_env('NONEXISTENT_VAR')
    
    def test_optional_environment_variable(self):
        """Test handling of optional environment variables."""
        settings = Settings()
        assert settings.get_env('OPTIONAL_VAR', required=False) is None
    
    def test_property_access(self, mock_settings):
        """Test accessing configuration sections via properties."""
        assert isinstance(mock_settings.dashboard, dict)
        assert isinstance(mock_settings.trading, dict)
        assert isinstance(mock_settings.market, dict)
    
    @pytest.mark.parametrize('section', [
        'dashboard',
        'trading',
        'market',
        'platforms',
        'logging'
    ])
    def test_required_sections(self, section, test_config):
        """Test validation of required configuration sections."""
        config = test_config.copy()
        del config[section]
        
        with pytest.raises(ConfigurationError) as exc_info:
            settings = Settings()
            settings._config = config
            settings._validate_config()
        
        assert section in str(exc_info.value)
    
    def test_trading_parameters(self, mock_settings):
        """Test trading-specific configuration parameters."""
        position_sizing = mock_settings.get('trading.position_sizing')
        assert position_sizing['max_position_pct'] == 0.02
        assert position_sizing['min_position_size'] == 1000
    
    def test_market_hours(self, mock_settings):
        """Test market hours configuration."""
        hours = mock_settings.get('market.hours')
        assert hours['open'] == '09:30:00'
        assert hours['close'] == '16:00:00'
    
    def test_dashboard_directories(self, mock_settings):
        """Test dashboard directory configuration."""
        dirs = mock_settings.get('dashboard.directories')
        assert all(key in dirs for key in ['templates', 'static', 'data', 'logs'])
        
    @pytest.mark.integration
    def test_file_paths_creation(self, test_data_dir):
        """Test that required directories are created."""
        settings = Settings()
        
        # Check that directories exist
        for dir_name in ['logs', 'data', 'templates', 'static']:
            dir_path = test_data_dir / dir_name
            assert dir_path.exists()
            assert dir_path.is_dir() 