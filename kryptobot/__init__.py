"""
KryptoBot Trading System

A modular, extensible trading system for algorithmic trading across multiple markets.
"""

__version__ = '1.0.0'
__author__ = 'KryptoBot Team'

# Import key classes for backward compatibility
from kryptobot.core.bot import TradingBot
from kryptobot.data.market_data import MarketDataService
from kryptobot.trading.strategy import TradingStrategy
from kryptobot.ml.enhancer import MLSignalEnhancer
from kryptobot.dashboard.dashboard import TradingDashboard, run_dashboard
from kryptobot.risk.manager import RiskManager
from kryptobot.utils.notifications import NotificationSystem
from kryptobot.utils.sleep_manager import SleepManager


