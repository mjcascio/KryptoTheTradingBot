#!/usr/bin/env python3
"""
Market Scanner

This script scans the market after hours to identify potential trading opportunities
for the next trading day. It analyzes stocks based on technical indicators, price patterns,
and other criteria to generate a list of potential trades.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple
import ta
from strategies import TradingStrategy
from telegram_notifications import send_telegram_message
from config import WATCHLIST, BREAKOUT_PARAMS, TREND_PARAMS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market_scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MarketScanner:
    """Market Scanner class for identifying potential trades"""
    
    def __init__(self, watchlist: List[str] = None):
        """
        Initialize the market scanner
        
        Args:
            watchlist: List of symbols to scan (defaults to config WATCHLIST)
        """
        self.watchlist = watchlist or WATCHLIST
        self.strategy = TradingStrategy()
        self.potential_trades = []
        
        # Create directories if they don't exist
        os.makedirs('data/scanner', exist_ok=True)
        
    def fetch_market_data(self, symbol: str, period: str = "60d") -> pd.DataFrame:
        """
        Fetch market data for a symbol
        
        Args:
            symbol: Trading symbol
            period: Data period (e.g., "60d" for 60 days)
            
        Returns:
            DataFrame with market data
        """
        try:
            # Fetch data from Yahoo Finance
            data = yf.download(symbol, period=period, progress=False)
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return None
                
            # Reset index to make Date a column
            data = data.reset_index()
            
            # Rename columns to lowercase
            data.columns = [col.lower() for col in data.columns]
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze a symbol for potential trading opportunities
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with analysis results
        """
        # Fetch data
        data = self.fetch_market_data(symbol)
        if data is None:
            return None
        
        # Calculate technical indicators
        self.calculate_indicators(data)
        
        # Analyze for breakout opportunities
        breakout_score = self.strategy.calculate_breakout_score(data)
        
        # Analyze for trend following opportunities
        trend_score = self.strategy.calculate_trend_score(data)
        
        # Analyze for support/resistance levels
        support, resistance = self.identify_support_resistance(data)
        
        # Calculate volatility
        volatility = self.calculate_volatility(data)
        
        # Calculate risk/reward ratio
        risk_reward = self.calculate_risk_reward(data, support, resistance)
        
        # Determine entry, stop loss, and take profit prices
        entry_price = data['close'].iloc[-1]
        stop_loss = support if breakout_score > trend_score else entry_price * 0.975
        take_profit = resistance if breakout_score > trend_score else entry_price * 1.075
        
        # Determine trade direction (long/short)
        direction = "long" if breakout_score > 0.6 or trend_score > 0.6 else "short"
        
        # Calculate overall score
        overall_score = (breakout_score + trend_score) / 2
        
        # Determine strategy
        strategy = "breakout" if breakout_score > trend_score else "trend_following"
        
        # Generate trade rationale
        rationale = self.generate_rationale(data, breakout_score, trend_score, support, resistance, volatility)
        
        # Create analysis result
        result = {
            "symbol": symbol,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "close_price": entry_price,
            "direction": direction,
            "strategy": strategy,
            "breakout_score": breakout_score,
            "trend_score": trend_score,
            "overall_score": overall_score,
            "support": support,
            "resistance": resistance,
            "volatility": volatility,
            "risk_reward": risk_reward,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "potential_profit": abs(take_profit - entry_price),
            "potential_loss": abs(entry_price - stop_loss),
            "rationale": rationale
        }
        
        return result
    
    def calculate_indicators(self, data: pd.DataFrame) -> None:
        """
        Calculate technical indicators for the data
        
        Args:
            data: DataFrame with market data
        """
        # RSI
        data['rsi'] = ta.momentum.RSIIndicator(data['close']).rsi()
        
        # MACD
        macd = ta.trend.MACD(data['close'])
        data['macd'] = macd.macd()
        data['macd_signal'] = macd.macd_signal()
        data['macd_diff'] = macd.macd_diff()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(data['close'])
        data['bollinger_high'] = bollinger.bollinger_hband()
        data['bollinger_low'] = bollinger.bollinger_lband()
        data['bollinger_mid'] = bollinger.bollinger_mavg()
        
        # Moving Averages
        data['sma_20'] = ta.trend.SMAIndicator(data['close'], window=20).sma_indicator()
        data['sma_50'] = ta.trend.SMAIndicator(data['close'], window=50).sma_indicator()
        data['sma_200'] = ta.trend.SMAIndicator(data['close'], window=200).sma_indicator()
        
        # Volume indicators
        data['volume_sma'] = ta.volume.SMAIndicator(data['volume'], window=20).sma_indicator()
        data['volume_ratio'] = data['volume'] / data['volume_sma']
        
        # ATR for volatility
        data['atr'] = ta.volatility.AverageTrueRange(data['high'], data['low'], data['close']).average_true_range()
    
    def identify_support_resistance(self, data: pd.DataFrame) -> Tuple[float, float]:
        """
        Identify support and resistance levels
        
        Args:
            data: DataFrame with market data
            
        Returns:
            Tuple of (support, resistance) prices
        """
        # Use recent lows for support
        recent_lows = data['low'].tail(10).nsmallest(3).mean()
        
        # Use recent highs for resistance
        recent_highs = data['high'].tail(10).nlargest(3).mean()
        
        return recent_lows, recent_highs
    
    def calculate_volatility(self, data: pd.DataFrame) -> float:
        """
        Calculate volatility based on ATR
        
        Args:
            data: DataFrame with market data
            
        Returns:
            Volatility as a percentage of price
        """
        # Use ATR as a percentage of price
        atr = data['atr'].iloc[-1]
        price = data['close'].iloc[-1]
        
        return (atr / price) * 100
    
    def calculate_risk_reward(self, data: pd.DataFrame, support: float, resistance: float) -> float:
        """
        Calculate risk/reward ratio
        
        Args:
            data: DataFrame with market data
            support: Support level
            resistance: Resistance level
            
        Returns:
            Risk/reward ratio
        """
        price = data['close'].iloc[-1]
        
        # For long positions
        reward = resistance - price
        risk = price - support
        
        # Avoid division by zero
        if risk == 0:
            return 0
            
        return reward / risk
    
    def generate_rationale(self, data: pd.DataFrame, breakout_score: float, trend_score: float, 
                          support: float, resistance: float, volatility: float) -> str:
        """
        Generate trade rationale
        
        Args:
            data: DataFrame with market data
            breakout_score: Breakout score
            trend_score: Trend score
            support: Support level
            resistance: Resistance level
            volatility: Volatility
            
        Returns:
            Trade rationale as a string
        """
        rationale = []
        
        # Price action
        price = data['close'].iloc[-1]
        prev_price = data['close'].iloc[-2]
        price_change = ((price / prev_price) - 1) * 100
        
        if price_change > 0:
            rationale.append(f"Price up {price_change:.2f}% from previous close")
        else:
            rationale.append(f"Price down {abs(price_change):.2f}% from previous close")
        
        # Moving averages
        if price > data['sma_20'].iloc[-1]:
            rationale.append("Price above 20-day SMA")
        else:
            rationale.append("Price below 20-day SMA")
            
        if data['sma_20'].iloc[-1] > data['sma_50'].iloc[-1]:
            rationale.append("20-day SMA above 50-day SMA (bullish)")
        else:
            rationale.append("20-day SMA below 50-day SMA (bearish)")
        
        # RSI
        rsi = data['rsi'].iloc[-1]
        if rsi > 70:
            rationale.append(f"RSI overbought at {rsi:.2f}")
        elif rsi < 30:
            rationale.append(f"RSI oversold at {rsi:.2f}")
        else:
            rationale.append(f"RSI neutral at {rsi:.2f}")
        
        # MACD
        if data['macd_diff'].iloc[-1] > 0:
            rationale.append("MACD bullish")
        else:
            rationale.append("MACD bearish")
        
        # Volume
        if data['volume_ratio'].iloc[-1] > 1.5:
            rationale.append("Volume significantly above average")
        elif data['volume_ratio'].iloc[-1] < 0.5:
            rationale.append("Volume significantly below average")
        
        # Bollinger Bands
        if price > data['bollinger_high'].iloc[-1]:
            rationale.append("Price above upper Bollinger Band (potential reversal)")
        elif price < data['bollinger_low'].iloc[-1]:
            rationale.append("Price below lower Bollinger Band (potential reversal)")
        
        # Support/Resistance
        if abs(price - support) / price < 0.02:
            rationale.append("Price near support level")
        if abs(price - resistance) / price < 0.02:
            rationale.append("Price near resistance level")
        
        # Volatility
        if volatility > 3:
            rationale.append(f"High volatility ({volatility:.2f}%)")
        elif volatility < 1:
            rationale.append(f"Low volatility ({volatility:.2f}%)")
        
        # Strategy-specific rationale
        if breakout_score > 0.7:
            rationale.append(f"Strong breakout potential (score: {breakout_score:.2f})")
        if trend_score > 0.7:
            rationale.append(f"Strong trend following potential (score: {trend_score:.2f})")
        
        return "; ".join(rationale)
    
    def scan_market(self) -> List[Dict[str, Any]]:
        """
        Scan the market for potential trading opportunities
        
        Returns:
            List of potential trades
        """
        logger.info(f"Starting market scan for {len(self.watchlist)} symbols")
        
        potential_trades = []
        
        for symbol in self.watchlist:
            logger.info(f"Analyzing {symbol}")
            
            # Analyze symbol
            analysis = self.analyze_symbol(symbol)
            
            if analysis is None:
                continue
                
            # Filter based on criteria
            if analysis['overall_score'] > 0.6 and analysis['risk_reward'] > 1.5:
                potential_trades.append(analysis)
                logger.info(f"Found potential trade for {symbol} with score {analysis['overall_score']:.2f}")
        
        # Sort by overall score
        potential_trades.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Save results
        self.potential_trades = potential_trades
        self.save_results()
        
        logger.info(f"Market scan completed. Found {len(potential_trades)} potential trades.")
        
        return potential_trades
    
    def save_results(self) -> None:
        """Save scan results to file"""
        try:
            # Create filename with date
            filename = f"data/scanner/scan_results_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(self.potential_trades, f, indent=4)
                
            logger.info(f"Scan results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving scan results: {e}")
    
    def generate_summary(self) -> str:
        """
        Generate a summary of potential trades
        
        Returns:
            Summary as a string
        """
        if not self.potential_trades:
            return "No potential trades found."
        
        # Create summary header
        summary = f"🔍 *KryptoBot Morning Trade Summary*\n"
        summary += f"📅 *Date:* {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Add potential trades
        summary += f"📊 *Potential Trades for Today:* {len(self.potential_trades)}\n\n"
        
        # Add top 5 trades
        for i, trade in enumerate(self.potential_trades[:5]):
            summary += f"*{i+1}. {trade['symbol']}* ({trade['strategy'].upper()})\n"
            summary += f"   Direction: {'🟢 LONG' if trade['direction'] == 'long' else '🔴 SHORT'}\n"
            summary += f"   Entry: ${trade['entry_price']:.2f}\n"
            summary += f"   Stop Loss: ${trade['stop_loss']:.2f}\n"
            summary += f"   Take Profit: ${trade['take_profit']:.2f}\n"
            summary += f"   Risk/Reward: {trade['risk_reward']:.2f}\n"
            summary += f"   Score: {trade['overall_score']:.2f}\n"
            summary += f"   Rationale: {trade['rationale']}\n\n"
        
        # Add footer
        summary += "These are potential trades identified by the scanner. The bot will execute trades based on its strategy and market conditions."
        
        return summary
    
    def send_telegram_summary(self) -> bool:
        """
        Send summary to Telegram
        
        Returns:
            Boolean indicating success
        """
        try:
            # Generate summary
            summary = self.generate_summary()
            
            # Send to Telegram
            success = send_telegram_message(summary)
            
            if success:
                logger.info("Trade summary sent to Telegram successfully")
            else:
                logger.error("Failed to send trade summary to Telegram")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending trade summary to Telegram: {e}")
            return False

def main():
    """Main function"""
    try:
        # Create scanner
        scanner = MarketScanner()
        
        # Scan market
        scanner.scan_market()
        
        # Send summary to Telegram
        scanner.send_telegram_summary()
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in market scanner: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 