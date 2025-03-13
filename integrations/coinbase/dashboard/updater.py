"""Dashboard update manager."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from ..models.market import OrderBook, MarketData
from .charts import CandlestickChart
from .orderbook import OrderBookVisualizer
from ..analytics.risk import RiskAnalyzer, PortfolioRisk

logger = logging.getLogger(__name__)

class DashboardUpdater:
    """Dashboard update manager."""
    
    def __init__(
        self,
        client: Any,
        symbols: List[str],
        update_interval: float = 1.0,
        chart_interval: float = 60.0
    ) -> None:
        """Initialize updater.
        
        Args:
            client: API client
            symbols: Trading pair symbols
            update_interval: Update interval for order book/ticker
            chart_interval: Update interval for charts
        """
        self.client = client
        self.symbols = symbols
        self.update_interval = update_interval
        self.chart_interval = chart_interval
        
        self._running = False
        self._last_update: Dict[str, datetime] = {}
        self._error_count: Dict[str, int] = {}
        self._charts: Dict[str, CandlestickChart] = {}
        self._order_books: Dict[str, OrderBookVisualizer] = {}
    
    async def start(self) -> None:
        """Start dashboard updates."""
        if self._running:
            return
        
        self._running = True
        self._last_update = {sym: datetime.min for sym in self.symbols}
        self._error_count = {sym: 0 for sym in self.symbols}
        
        # Start update tasks
        update_tasks = [
            self._update_market_data(symbol) for symbol in self.symbols
        ]
        chart_tasks = [
            self._update_charts(symbol) for symbol in self.symbols
        ]
        
        await asyncio.gather(*update_tasks, *chart_tasks)
    
    async def stop(self) -> None:
        """Stop dashboard updates."""
        self._running = False
    
    async def _update_market_data(self, symbol: str) -> None:
        """Update market data for symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        while self._running:
            try:
                # Update order book
                order_book = await self.client.get_order_book(symbol)
                if symbol in self._order_books:
                    self._order_books[symbol].update(order_book)
                else:
                    visualizer = OrderBookVisualizer(order_book)
                    visualizer.create_visualization()
                    self._order_books[symbol] = visualizer
                
                # Update last update time and reset error count
                self._last_update[symbol] = datetime.now()
                self._error_count[symbol] = 0
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error updating market data for {symbol}: {str(e)}")
                self._error_count[symbol] += 1
                
                # Increase delay on consecutive errors
                delay = min(30, self.update_interval * (2 ** self._error_count[symbol]))
                await asyncio.sleep(delay)
    
    async def _update_charts(self, symbol: str) -> None:
        """Update charts for symbol.
        
        Args:
            symbol: Trading pair symbol
        """
        while self._running:
            try:
                # Get historical data
                candles = await self.client.get_candles(
                    symbol,
                    start_time=datetime.now() - timedelta(days=30)
                )
                
                # Update or create chart
                if symbol in self._charts:
                    self._charts[symbol].df = candles
                    self._charts[symbol].update_layout()
                else:
                    chart = CandlestickChart(candles, title=f"{symbol} Price")
                    chart.add_candlesticks()
                    chart.add_volume()
                    chart.add_moving_averages()
                    chart.add_bollinger_bands()
                    chart.add_rsi()
                    chart.add_macd()
                    chart.update_layout()
                    self._charts[symbol] = chart
                
                await asyncio.sleep(self.chart_interval)
                
            except Exception as e:
                logger.error(f"Error updating charts for {symbol}: {str(e)}")
                await asyncio.sleep(self.chart_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """Get update status.
        
        Returns:
            Status information
        """
        now = datetime.now()
        return {
            symbol: {
                "last_update": self._last_update[symbol],
                "age_seconds": (now - self._last_update[symbol]).total_seconds(),
                "error_count": self._error_count[symbol],
                "status": "error" if self._error_count[symbol] > 3 else "ok"
            }
            for symbol in self.symbols
        }
    
    def get_visualizations(self, symbol: str) -> Dict[str, Any]:
        """Get visualizations for symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary of visualizations
        """
        return {
            "chart": self._charts.get(symbol),
            "order_book": self._order_books.get(symbol)
        } 