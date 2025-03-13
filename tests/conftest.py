"""Test configuration and shared fixtures for KryptoBot tests."""

import os
import pytest
from typing import Dict, Any
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from trading.orders import Order, OrderManager
from trading.risk import RiskManager
from trading.portfolio import PortfolioManager

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Fixture providing test configuration data."""
    return {
        'dashboard': {
            'host': 'localhost',
            'port': 5001,
            'directories': {
                'templates': 'tests/data/templates',
                'static': 'tests/data/static',
                'data': 'tests/data/data',
                'logs': 'tests/data/logs'
            }
        },
        'trading': {
            'max_trades_per_day': 5,
            'min_success_probability': 0.6,
            'position_sizing': {
                'max_position_pct': 0.02,
                'min_position_size': 1000
            },
            'risk_management': {
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'max_daily_loss_pct': 0.05
            }
        },
        'market': {
            'timezone': 'America/New_York',
            'hours': {
                'open': '09:30:00',
                'close': '16:00:00'
            }
        }
    }

@pytest.fixture
def mock_settings(test_config):
    """Fixture providing a mocked Settings instance."""
    settings = MagicMock(spec=Settings)
    settings._config = test_config
    settings.get = lambda path, default=None: _get_nested_value(test_config, path, default)
    return settings

@pytest.fixture
def order_manager():
    """Fixture providing an OrderManager instance."""
    return OrderManager()

@pytest.fixture
def risk_manager():
    """Fixture providing a RiskManager instance."""
    return RiskManager(initial_equity=100000.0)

@pytest.fixture
def portfolio_manager():
    """Fixture providing a PortfolioManager instance."""
    return PortfolioManager(equity=100000.0, max_positions=10)

@pytest.fixture
def sample_order():
    """Fixture providing a sample order for testing."""
    return Order(
        symbol="AAPL",
        side="buy",
        quantity=100,
        price=150.0
    )

@pytest.fixture
def test_data_dir(tmp_path):
    """Fixture providing a temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, test_data_dir):
    """Fixture to set up test environment variables."""
    env_vars = {
        'ALPACA_API_KEY': 'test_api_key',
        'ALPACA_SECRET_KEY': 'test_secret_key',
        'MT_SERVER': 'test_server',
        'MT_PORT': '1234',
        'MT_USERNAME': 'test_user',
        'MT_PASSWORD': 'test_pass',
        'EMAIL_USERNAME': 'test@example.com',
        'EMAIL_PASSWORD': 'test_email_pass'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    # Set up test directories
    for subdir in ['logs', 'data', 'templates', 'static']:
        (test_data_dir / subdir).mkdir(exist_ok=True)

def _get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Helper function to get nested dictionary values using dot notation."""
    try:
        value = data
        for key in path.split('.'):
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default 