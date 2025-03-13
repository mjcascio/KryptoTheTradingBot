"""Order book visualization module."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import List, Tuple, Dict, Any
from ..models.market import OrderBook

class OrderBookVisualizer:
    """Interactive order book visualization."""
    
    def __init__(
        self,
        order_book: OrderBook,
        depth: int = 50,
        height: int = 600,
        width: int = 800
    ) -> None:
        """Initialize visualizer.
        
        Args:
            order_book: Order book data
            depth: Number of price levels to show
            height: Chart height
            width: Chart width
        """
        self.order_book = order_book
        self.depth = depth
        self.height = height
        self.width = width
        
        # Convert order book to DataFrames
        self.bids_df = pd.DataFrame(
            order_book.bids[:depth],
            columns=["price", "size"]
        )
        self.asks_df = pd.DataFrame(
            order_book.asks[:depth],
            columns=["price", "size"]
        )
        
        # Calculate cumulative sizes
        self.bids_df["cumulative_size"] = self.bids_df["size"].cumsum()
        self.asks_df["cumulative_size"] = self.asks_df["size"].cumsum()
        
        # Calculate total value at each level
        self.bids_df["value"] = self.bids_df["price"] * self.bids_df["size"]
        self.asks_df["value"] = self.asks_df["price"] * self.asks_df["size"]
        self.bids_df["cumulative_value"] = self.bids_df["value"].cumsum()
        self.asks_df["cumulative_value"] = self.asks_df["value"].cumsum()
        
        # Create figure
        self.fig = go.Figure()
    
    def add_depth_chart(self) -> None:
        """Add depth chart showing cumulative size."""
        # Bids depth
        self.fig.add_trace(
            go.Scatter(
                x=self.bids_df["price"],
                y=self.bids_df["cumulative_size"],
                name="Bids",
                line=dict(color="green", width=2),
                fill="tonexty"
            )
        )
        
        # Asks depth
        self.fig.add_trace(
            go.Scatter(
                x=self.asks_df["price"],
                y=self.asks_df["cumulative_size"],
                name="Asks",
                line=dict(color="red", width=2),
                fill="tonexty"
            )
        )
    
    def add_price_levels(self) -> None:
        """Add individual price levels."""
        # Bid price levels
        self.fig.add_trace(
            go.Bar(
                x=self.bids_df["price"],
                y=self.bids_df["size"],
                name="Bid Size",
                marker_color="rgba(0, 255, 0, 0.3)"
            )
        )
        
        # Ask price levels
        self.fig.add_trace(
            go.Bar(
                x=self.asks_df["price"],
                y=self.asks_df["size"],
                name="Ask Size",
                marker_color="rgba(255, 0, 0, 0.3)"
            )
        )
    
    def add_value_areas(self) -> None:
        """Add value area visualization."""
        # Calculate total value
        total_bid_value = self.bids_df["value"].sum()
        total_ask_value = self.asks_df["value"].sum()
        
        # Find value area (70% of total value)
        bid_value_area = self.bids_df[
            self.bids_df["cumulative_value"] <= 0.7 * total_bid_value
        ]
        ask_value_area = self.asks_df[
            self.asks_df["cumulative_value"] <= 0.7 * total_ask_value
        ]
        
        # Add value area shapes
        self.fig.add_vrect(
            x0=bid_value_area["price"].min(),
            x1=bid_value_area["price"].max(),
            fillcolor="green",
            opacity=0.1,
            layer="below",
            line_width=0
        )
        self.fig.add_vrect(
            x0=ask_value_area["price"].min(),
            x1=ask_value_area["price"].max(),
            fillcolor="red",
            opacity=0.1,
            layer="below",
            line_width=0
        )
    
    def add_mid_price_line(self) -> None:
        """Add mid price line."""
        mid_price = (
            self.asks_df["price"].iloc[0] + self.bids_df["price"].iloc[0]
        ) / 2
        
        self.fig.add_vline(
            x=mid_price,
            line_dash="dash",
            line_color="white",
            annotation_text=f"Mid: {mid_price:.2f}"
        )
    
    def add_imbalance_indicators(self) -> None:
        """Add order book imbalance indicators."""
        # Calculate imbalance at each price level
        max_depth = min(len(self.bids_df), len(self.asks_df))
        for i in range(max_depth):
            bid_size = self.bids_df["size"].iloc[i]
            ask_size = self.asks_df["size"].iloc[i]
            
            # Only show significant imbalances (>2x difference)
            if bid_size > 2 * ask_size:
                self.fig.add_annotation(
                    x=self.bids_df["price"].iloc[i],
                    y=bid_size,
                    text="↑",
                    showarrow=False,
                    font=dict(size=12, color="green")
                )
            elif ask_size > 2 * bid_size:
                self.fig.add_annotation(
                    x=self.asks_df["price"].iloc[i],
                    y=ask_size,
                    text="↓",
                    showarrow=False,
                    font=dict(size=12, color="red")
                )
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate order book metrics.
        
        Returns:
            Dictionary of metrics
        """
        bid_ask_spread = self.asks_df["price"].iloc[0] - self.bids_df["price"].iloc[0]
        spread_pct = bid_ask_spread / self.asks_df["price"].iloc[0]
        
        total_bid_size = self.bids_df["size"].sum()
        total_ask_size = self.asks_df["size"].sum()
        bid_ask_ratio = total_bid_size / total_ask_size
        
        return {
            "bid_ask_spread": bid_ask_spread,
            "spread_pct": spread_pct,
            "total_bid_size": total_bid_size,
            "total_ask_size": total_ask_size,
            "bid_ask_ratio": bid_ask_ratio,
            "bid_levels": len(self.bids_df),
            "ask_levels": len(self.asks_df),
            "timestamp": self.order_book.timestamp
        }
    
    def add_metrics_table(self) -> None:
        """Add metrics table to visualization."""
        metrics = self.calculate_metrics()
        
        # Create table text
        table_text = [
            ["Metric", "Value"],
            ["Bid-Ask Spread", f"{metrics['bid_ask_spread']:.8f}"],
            ["Spread %", f"{metrics['spread_pct']:.4%}"],
            ["Bid/Ask Ratio", f"{metrics['bid_ask_ratio']:.2f}"],
            ["Total Bid Size", f"{metrics['total_bid_size']:.4f}"],
            ["Total Ask Size", f"{metrics['total_ask_size']:.4f}"]
        ]
        
        self.fig.add_trace(
            go.Table(
                domain=dict(x=[0, 0.3], y=[0, 0.2]),
                header=dict(
                    values=["<b>Metric</b>", "<b>Value</b>"],
                    line_color="darkslategray",
                    fill_color="gray",
                    font=dict(color="white", size=12),
                    height=30
                ),
                cells=dict(
                    values=list(zip(*table_text[1:])),
                    line_color="darkslategray",
                    fill_color="black",
                    font=dict(color="white", size=11),
                    height=25
                )
            )
        )
    
    def update_layout(self) -> None:
        """Update chart layout."""
        self.fig.update_layout(
            title=f"Order Book - {self.order_book.symbol}",
            xaxis_title="Price",
            yaxis_title="Size",
            height=self.height,
            width=self.width,
            template="plotly_dark",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
    
    def create_visualization(self) -> None:
        """Create complete order book visualization."""
        self.add_depth_chart()
        self.add_price_levels()
        self.add_value_areas()
        self.add_mid_price_line()
        self.add_imbalance_indicators()
        self.add_metrics_table()
        self.update_layout()
    
    def show(self) -> None:
        """Display the visualization."""
        self.fig.show()
    
    def to_html(self) -> str:
        """Convert visualization to HTML.
        
        Returns:
            HTML string
        """
        return self.fig.to_html(include_plotlyjs=True, full_html=True)

class LiveOrderBook:
    """Real-time order book visualization."""
    
    def __init__(
        self,
        symbol: str,
        depth: int = 50,
        update_interval: float = 1.0
    ) -> None:
        """Initialize live order book.
        
        Args:
            symbol: Trading pair symbol
            depth: Order book depth
            update_interval: Update interval in seconds
        """
        self.symbol = symbol
        self.depth = depth
        self.update_interval = update_interval
        self.fig = go.FigureWidget()
        
        # Initialize empty traces
        self.bid_trace = go.Scatter(
            x=[],
            y=[],
            name="Bids",
            line=dict(color="green", width=2)
        )
        self.ask_trace = go.Scatter(
            x=[],
            y=[],
            name="Asks",
            line=dict(color="red", width=2)
        )
        
        self.fig.add_trace(self.bid_trace)
        self.fig.add_trace(self.ask_trace)
        
        # Update layout
        self.fig.update_layout(
            title=f"Live Order Book - {symbol}",
            xaxis_title="Price",
            yaxis_title="Size",
            template="plotly_dark"
        )
    
    def update(self, order_book: OrderBook) -> None:
        """Update order book visualization.
        
        Args:
            order_book: New order book data
        """
        # Convert to DataFrames
        bids_df = pd.DataFrame(
            order_book.bids[:self.depth],
            columns=["price", "size"]
        )
        asks_df = pd.DataFrame(
            order_book.asks[:self.depth],
            columns=["price", "size"]
        )
        
        # Calculate cumulative sizes
        bids_df["cumulative_size"] = bids_df["size"].cumsum()
        asks_df["cumulative_size"] = asks_df["size"].cumsum()
        
        # Update traces
        with self.fig.batch_update():
            self.bid_trace.x = bids_df["price"]
            self.bid_trace.y = bids_df["cumulative_size"]
            self.ask_trace.x = asks_df["price"]
            self.ask_trace.y = asks_df["cumulative_size"]
    
    def show(self) -> None:
        """Display the live visualization."""
        self.fig.show() 