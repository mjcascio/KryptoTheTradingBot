"""Candlestick chart module with technical indicators."""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

class TechnicalAnalysis:
    """Technical analysis calculations."""
    
    @staticmethod
    def calculate_ma(data: pd.Series, period: int) -> pd.Series:
        """Calculate Moving Average.
        
        Args:
            data: Price data
            period: MA period
            
        Returns:
            MA values
        """
        return data.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average.
        
        Args:
            data: Price data
            period: EMA period
            
        Returns:
            EMA values
        """
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index.
        
        Args:
            data: Price data
            period: RSI period
            
        Returns:
            RSI values
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD.
        
        Args:
            data: Price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            MACD line, signal line, and histogram
        """
        fast_ema = TechnicalAnalysis.calculate_ema(data, fast_period)
        slow_ema = TechnicalAnalysis.calculate_ema(data, slow_period)
        
        macd_line = fast_ema - slow_ema
        signal_line = TechnicalAnalysis.calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands.
        
        Args:
            data: Price data
            period: MA period
            std_dev: Standard deviation multiplier
            
        Returns:
            Middle band, upper band, and lower band
        """
        middle_band = TechnicalAnalysis.calculate_ma(data, period)
        rolling_std = data.rolling(window=period).std()
        
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)
        
        return middle_band, upper_band, lower_band

class CandlestickChart:
    """Interactive candlestick chart with technical indicators."""
    
    def __init__(
        self,
        df: pd.DataFrame,
        title: str = "Price Chart",
        height: int = 800
    ) -> None:
        """Initialize chart.
        
        Args:
            df: DataFrame with OHLCV data
            title: Chart title
            height: Chart height
        """
        self.df = df
        self.title = title
        self.height = height
        self.ta = TechnicalAnalysis()
        
        # Create figure with secondary y-axis
        self.fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(title, "Volume", "Indicators")
        )
    
    def add_candlesticks(self) -> None:
        """Add candlestick chart."""
        self.fig.add_trace(
            go.Candlestick(
                x=self.df.index,
                open=self.df["open"],
                high=self.df["high"],
                low=self.df["low"],
                close=self.df["close"],
                name="OHLC"
            ),
            row=1,
            col=1
        )
    
    def add_volume(self) -> None:
        """Add volume bars."""
        colors = ["red" if close < open else "green" 
                 for close, open in zip(self.df["close"], self.df["open"])]
        
        self.fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df["volume"],
                name="Volume",
                marker_color=colors
            ),
            row=2,
            col=1
        )
    
    def add_moving_averages(
        self,
        periods: List[int] = [20, 50, 200]
    ) -> None:
        """Add moving averages.
        
        Args:
            periods: List of MA periods
        """
        for period in periods:
            ma = self.ta.calculate_ma(self.df["close"], period)
            self.fig.add_trace(
                go.Scatter(
                    x=self.df.index,
                    y=ma,
                    name=f"MA{period}",
                    line=dict(width=1)
                ),
                row=1,
                col=1
            )
    
    def add_bollinger_bands(
        self,
        period: int = 20,
        std_dev: float = 2.0
    ) -> None:
        """Add Bollinger Bands.
        
        Args:
            period: MA period
            std_dev: Standard deviation multiplier
        """
        middle, upper, lower = self.ta.calculate_bollinger_bands(
            self.df["close"],
            period,
            std_dev
        )
        
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=middle,
                name="BB Middle",
                line=dict(width=1, color="gray")
            ),
            row=1,
            col=1
        )
        
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=upper,
                name="BB Upper",
                line=dict(width=1, dash="dash", color="gray")
            ),
            row=1,
            col=1
        )
        
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=lower,
                name="BB Lower",
                line=dict(width=1, dash="dash", color="gray")
            ),
            row=1,
            col=1
        )
    
    def add_rsi(self, period: int = 14) -> None:
        """Add RSI indicator.
        
        Args:
            period: RSI period
        """
        rsi = self.ta.calculate_rsi(self.df["close"], period)
        
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=rsi,
                name=f"RSI({period})"
            ),
            row=3,
            col=1
        )
        
        # Add overbought/oversold lines
        self.fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="red",
            row=3,
            col=1
        )
        self.fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="green",
            row=3,
            col=1
        )
    
    def add_macd(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> None:
        """Add MACD indicator.
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
        """
        macd, signal, hist = self.ta.calculate_macd(
            self.df["close"],
            fast_period,
            slow_period,
            signal_period
        )
        
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=macd,
                name="MACD"
            ),
            row=3,
            col=1
        )
        
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=signal,
                name="Signal"
            ),
            row=3,
            col=1
        )
        
        colors = ["red" if val < 0 else "green" for val in hist]
        self.fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=hist,
                name="Histogram",
                marker_color=colors
            ),
            row=3,
            col=1
        )
    
    def update_layout(self) -> None:
        """Update chart layout."""
        self.fig.update_layout(
            height=self.height,
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
        )
        
        # Update y-axes labels
        self.fig.update_yaxes(title_text="Price", row=1, col=1)
        self.fig.update_yaxes(title_text="Volume", row=2, col=1)
        self.fig.update_yaxes(title_text="Indicators", row=3, col=1)
    
    def show(self) -> None:
        """Display the chart."""
        self.fig.show()
    
    def to_html(self) -> str:
        """Convert chart to HTML.
        
        Returns:
            HTML string
        """
        return self.fig.to_html(include_plotlyjs=True, full_html=True) 