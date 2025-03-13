#!/usr/bin/env python3
"""
Core Trading Bot Module

This module coordinates all components of the trading bot.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from src.integrations.alpaca import AlpacaIntegration
from src.strategies.stock import StockStrategy
from src.strategies.options import OptionsStrategy
from src.core.market_data import MarketData
from src.core.risk_management import RiskManager
from src.integrations.telegram_notifications import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TradingBot:
    """Main trading bot class"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        stock_strategy: Optional[StockStrategy] = None,
        options_strategy: Optional[OptionsStrategy] = None,
        risk_manager: Optional[RiskManager] = None,
        telegram_notifier: Optional[TelegramNotifier] = None,
        paper_trading: bool = True
    ):
        """Initialize trading bot
        
        Args:
            api_key (str): Alpaca API key
            api_secret (str): Alpaca API secret
            stock_strategy (StockStrategy): Stock trading strategy
            options_strategy (OptionsStrategy): Options trading strategy
            risk_manager (RiskManager): Risk management system
            telegram_notifier (TelegramNotifier): Telegram notifications
            paper_trading (bool): Whether to use paper trading
        """
        # Initialize components
        self.market_data = MarketData(
            api_key=api_key,
            api_secret=api_secret,
            paper_trading=paper_trading
        )
        self.alpaca = AlpacaIntegration(
            api_key=api_key,
            api_secret=api_secret,
            paper_trading=paper_trading
        )
        self.risk_manager = risk_manager or RiskManager()
        self.telegram = telegram_notifier
        
        # Initialize strategies
        self.stock_strategy = stock_strategy or StockStrategy(
            name="Default Stock Strategy",
            description="Basic stock trading strategy"
        )
        self.options_strategy = options_strategy or OptionsStrategy(
            name="Default Options Strategy",
            description="Basic options trading strategy"
        )
        
        # Trading state
        self.is_running = False
        self.start_time = None
        self.last_update = None
        self.watchlist: List[str] = []
        self.active_strategies = []
        
        if self.stock_strategy:
            self.active_strategies.append("stocks")
        if self.options_strategy:
            self.active_strategies.append("options")
        
        logger.info("Trading bot initialized")

    def get_status(self) -> Dict:
        """Get current bot status
        
        Returns:
            Dict: Bot status information
        """
        status = {
            "running": self.is_running,
            "uptime": str(datetime.now() - self.start_time) if self.start_time else "Not started",
            "active_strategies": self.active_strategies,
            "open_positions": self.alpaca.get_positions() or [],
            "last_update": self.last_update.strftime("%Y-%m-%d %H:%M:%S") if self.last_update else None,
            "paper_trading": self.alpaca.paper_trading
        }
        return status
    
    def get_positions(self) -> List[Dict]:
        """Get current positions
        
        Returns:
            List[Dict]: List of open positions
        """
        return self.alpaca.get_positions() or []
    
    def get_recent_trades(self) -> List[Dict]:
        """Get recent trades
        
        Returns:
            List[Dict]: List of recent trades
        """
        return self.alpaca.get_recent_trades() or []
    
    def get_performance(self) -> Dict:
        """Get performance metrics
        
        Returns:
            Dict: Performance metrics
        """
        account = self.alpaca.get_account_info()
        if not account:
            return {}
        
        # Calculate daily P&L
        positions = self.get_positions()
        daily_pl = sum(float(pos.get('unrealized_intraday_pl', 0)) for pos in positions)
        
        # Calculate total P&L
        total_pl = float(account.get('equity', 0)) - float(account.get('initial_margin', 0))
        
        # Get trading history
        trades = self.get_recent_trades()
        win_rate = 0.0
        if trades:
            winning_trades = sum(1 for t in trades if float(t.get('profit_loss', 0)) > 0)
            win_rate = (winning_trades / len(trades)) * 100
        
        return {
            "daily_pl": daily_pl,
            "total_pl": total_pl,
            "win_rate": win_rate,
            "sharpe_ratio": 0.0  # TODO: Implement Sharpe ratio calculation
        }
    
    def check_api_connection(self) -> bool:
        """Check if API connection is working
        
        Returns:
            bool: True if connection is working
        """
        return self.alpaca.check_connection()
    
    def check_market_data(self) -> bool:
        """Check if market data is available
        
        Returns:
            bool: True if market data is available
        """
        return self.market_data.check_connection()
    
    def start_stock_trading(self) -> bool:
        """Start stock trading
        
        Returns:
            bool: True if started successfully
        """
        if "stocks" not in self.active_strategies:
            self.active_strategies.append("stocks")
            logger.info("Stock trading enabled")
            return True
        return False
    
    def stop_stock_trading(self) -> bool:
        """Stop stock trading
        
        Returns:
            bool: True if stopped successfully
        """
        if "stocks" in self.active_strategies:
            self.active_strategies.remove("stocks")
            logger.info("Stock trading disabled")
            return True
        return False
    
    def start_options_trading(self) -> bool:
        """Start options trading
        
        Returns:
            bool: True if started successfully
        """
        if "options" not in self.active_strategies:
            self.active_strategies.append("options")
            logger.info("Options trading enabled")
            return True
        return False
    
    def stop_options_trading(self) -> bool:
        """Stop options trading
        
        Returns:
            bool: True if stopped successfully
        """
        if "options" in self.active_strategies:
            self.active_strategies.remove("options")
            logger.info("Options trading disabled")
            return True
        return False

    def start(self) -> bool:
        """Start the trading bot
        
        Returns:
            bool: True if started successfully
        """
        try:
            # Get initial account info
            account_info = self.alpaca.get_account_info()
            if account_info is None:
                logger.error("Failed to get account information")
                return False
            
            # Update risk manager
            self.risk_manager.update_account_status(account_info)
            
            # Start trading loop
            self.is_running = True
            self.start_time = datetime.now()
            self.last_update = datetime.now()
            
            logger.info("Trading bot started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            return False

    def stop(self) -> bool:
        """Stop the trading bot
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            self.is_running = False
            logger.info("Trading bot stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")
            return False

    def update(self) -> None:
        """Update trading bot state"""
        if not self.is_running:
            return
        
        try:
            # Get current market data
            market_data = {}
            for symbol in self.watchlist:
                data = self.market_data.get_current_data(symbol)
                if data is not None:
                    market_data[symbol] = data
            
            # Get account info
            account_info = self.alpaca.get_account_info()
            if account_info is None:
                logger.error("Failed to get account information")
                return
            
            # Update risk manager
            self.risk_manager.update_account_status(account_info)
            
            # Get current positions
            positions = self.alpaca.get_positions(suppress_notifications=True)
            self.risk_manager.update_position_count(len(positions))
            
            # Analyze market and generate signals
            stock_signals = self.stock_strategy.analyze_market(market_data)
            options_signals = self.options_strategy.analyze_market(market_data)
            
            # Process signals
            self._process_signals(stock_signals, options_signals, account_info)
            
            # Update last update time
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating trading bot: {e}")

    def _process_signals(
        self,
        stock_signals: List[Dict],
        options_signals: List[Dict],
        account_info: Dict
    ) -> None:
        """Process trading signals
        
        Args:
            stock_signals (List[Dict]): Stock trading signals
            options_signals (List[Dict]): Options trading signals
            account_info (Dict): Account information
        """
        # Process stock signals
        for signal in stock_signals:
            if self._validate_signal(signal, account_info):
                self._execute_stock_trade(signal, account_info)
        
        # Process options signals
        for signal in options_signals:
            if self._validate_signal(signal, account_info):
                self._execute_options_trade(signal, account_info)

    def _validate_signal(self, signal: Dict, account_info: Dict) -> bool:
        """Validate a trading signal
        
        Args:
            signal (Dict): Trading signal
            account_info (Dict): Account information
            
        Returns:
            bool: True if signal is valid
        """
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            entry_price=signal['price'],
            stop_loss=signal.get('stop_loss', signal['price'] * 0.98),
            account_info=account_info,
            volatility=signal.get('volatility', 0.0)
        )
        
        if position_size is None:
            return False
        
        # Check if position can be opened
        return self.risk_manager.can_open_position(position_size, account_info)

    def _execute_stock_trade(self, signal: Dict, account_info: Dict) -> None:
        """Execute a stock trade
        
        Args:
            signal (Dict): Trading signal
            account_info (Dict): Account information
        """
        try:
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                entry_price=signal['price'],
                stop_loss=signal.get('stop_loss', signal['price'] * 0.98),
                account_info=account_info
            )
            
            if position_size is None:
                return
            
            # Place order
            order = self.alpaca.place_market_order(
                symbol=signal['symbol'],
                side=signal['action'],
                quantity=position_size
            )
            
            if order is not None:
                logger.info(f"Stock order placed: {order}")
                
        except Exception as e:
            logger.error(f"Error executing stock trade: {e}")

    def _execute_options_trade(self, signal: Dict, account_info: Dict) -> None:
        """Execute an options trade
        
        Args:
            signal (Dict): Trading signal
            account_info (Dict): Account information
        """
        try:
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                entry_price=signal['price'],
                stop_loss=signal.get('stop_loss', signal['price'] * 0.98),
                account_info=account_info,
                volatility=signal.get('volatility', 0.0)
            )
            
            if position_size is None:
                return
            
            # Place order (to be implemented with options broker)
            logger.info(f"Options trade signal: {signal}")
            
        except Exception as e:
            logger.error(f"Error executing options trade: {e}")

    def add_to_watchlist(self, symbol: str) -> bool:
        """Add a symbol to the watchlist
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            bool: True if added successfully
        """
        try:
            if symbol not in self.watchlist:
                self.watchlist.append(symbol)
                logger.info(f"Added {symbol} to watchlist")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding symbol to watchlist: {e}")
            return False

    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove a symbol from the watchlist
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            bool: True if removed successfully
        """
        try:
            if symbol in self.watchlist:
                self.watchlist.remove(symbol)
                logger.info(f"Removed {symbol} from watchlist")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing symbol from watchlist: {e}")
            return False

    def get_status(self) -> Dict:
        """Get trading bot status
        
        Returns:
            Dictionary with status information
        """
        return {
            'is_running': self.is_running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'watchlist': self.watchlist,
            'risk_metrics': self.risk_manager.get_risk_metrics(),
            'positions': self.alpaca.get_positions(suppress_notifications=True)
        } 