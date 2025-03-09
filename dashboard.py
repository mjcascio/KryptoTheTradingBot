from flask import Flask, render_template, jsonify, request
import threading
from datetime import datetime, timedelta
import json
import os
import logging
import signal
import sys
import psutil
import numpy as np
import pandas as pd
import yfinance as yf
from typing import List, Dict, Any
from config import WATCHLIST, PLATFORMS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'dashboard.log'))
    ]
)
logger = logging.getLogger(__name__)

# Sector mapping for stocks in the watchlist
SECTOR_MAPPING = {
    # Technology
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", 
    "AMZN": "Technology", "META": "Technology", "NVDA": "Technology", 
    "AMD": "Technology", "TSLA": "Technology", "INTC": "Technology", 
    "CRM": "Technology", "ADBE": "Technology", "ORCL": "Technology", 
    "CSCO": "Technology", "IBM": "Technology", "QCOM": "Technology",
    "NOW": "Technology", "SNOW": "Technology", "ZS": "Technology", 
    "PANW": "Technology", "FTNT": "Technology", "NET": "Technology", 
    "ANET": "Technology", "MU": "Technology", "AVGO": "Technology", 
    "TXN": "Technology",
    
    # Financial
    "JPM": "Financial", "V": "Financial", "BAC": "Financial", 
    "MA": "Financial", "WFC": "Financial", "GS": "Financial", 
    "MS": "Financial", "BLK": "Financial", "C": "Financial", 
    "AXP": "Financial", "SCHW": "Financial", "USB": "Financial", 
    "PNC": "Financial", "TFC": "Financial", "COF": "Financial",
    "SPGI": "Financial", "MCO": "Financial", "ICE": "Financial", 
    "CME": "Financial", "COIN": "Financial",
    
    # Healthcare
    "JNJ": "Healthcare", "PFE": "Healthcare", "UNH": "Healthcare", 
    "ABT": "Healthcare", "TMO": "Healthcare", "DHR": "Healthcare", 
    "BMY": "Healthcare", "ABBV": "Healthcare", "LLY": "Healthcare", 
    "AMGN": "Healthcare", "CVS": "Healthcare", "MRK": "Healthcare", 
    "MDT": "Healthcare", "ISRG": "Healthcare", "GILD": "Healthcare",
    "REGN": "Healthcare", "VRTX": "Healthcare", "HUM": "Healthcare",
    
    # Consumer
    "WMT": "Consumer", "PG": "Consumer", "HD": "Consumer", 
    "COST": "Consumer", "TGT": "Consumer", "NKE": "Consumer", 
    "SBUX": "Consumer", "MCD": "Consumer", "KO": "Consumer", 
    "PEP": "Consumer", "DIS": "Consumer", "LOW": "Consumer", 
    "TJX": "Consumer", "LULU": "Consumer", "ULTA": "Consumer",
    
    # Industrial & Energy
    "XOM": "Energy", "CVX": "Energy", "CAT": "Industrial", 
    "BA": "Industrial", "HON": "Industrial", "UNP": "Industrial", 
    "GE": "Industrial", "MMM": "Industrial", "LMT": "Industrial", 
    "RTX": "Industrial", "DE": "Industrial", "DUK": "Energy", 
    "NEE": "Energy", "SLB": "Energy", "EOG": "Energy",
    
    # Communication
    "NFLX": "Communication", "CMCSA": "Communication", "VZ": "Communication", 
    "T": "Communication", "TMUS": "Communication", "ATVI": "Communication", 
    "EA": "Communication", "ROKU": "Communication", "TTD": "Communication", 
    "SNAP": "Communication", "PINS": "Communication", "SPOT": "Communication",
    
    # Materials
    "LIN": "Materials", "APD": "Materials", "ECL": "Materials", 
    "DD": "Materials", "NEM": "Materials", "FCX": "Materials", 
    "DOW": "Materials", "NUE": "Materials", "CF": "Materials", 
    "MOS": "Materials",
    
    # Real Estate
    "AMT": "Real Estate", "PLD": "Real Estate", "CCI": "Real Estate", 
    "EQIX": "Real Estate", "PSA": "Real Estate", "SPG": "Real Estate", 
    "AVB": "Real Estate", "EQR": "Real Estate", "VMC": "Real Estate", 
    "MLM": "Real Estate"
}

# Recommended sector allocations based on market conditions
RECOMMENDED_ALLOCATIONS = {
    "bull_market": {
        "Technology": 0.30,
        "Financial": 0.20,
        "Healthcare": 0.10,
        "Consumer": 0.10,
        "Industrial": 0.10,
        "Energy": 0.05,
        "Communication": 0.10,
        "Materials": 0.03,
        "Real Estate": 0.02
    },
    "bear_market": {
        "Technology": 0.15,
        "Financial": 0.10,
        "Healthcare": 0.20,
        "Consumer": 0.20,
        "Industrial": 0.05,
        "Energy": 0.10,
        "Communication": 0.05,
        "Materials": 0.05,
        "Real Estate": 0.10
    },
    "neutral_market": {
        "Technology": 0.25,
        "Financial": 0.15,
        "Healthcare": 0.15,
        "Consumer": 0.15,
        "Industrial": 0.08,
        "Energy": 0.07,
        "Communication": 0.07,
        "Materials": 0.04,
        "Real Estate": 0.04
    }
}

def get_sector_mappings(symbols: List[str]) -> Dict[str, str]:
    """Get sector mappings for a list of stock symbols"""
    result = {}
    for symbol in symbols:
        if symbol in SECTOR_MAPPING:
            result[symbol] = SECTOR_MAPPING[symbol]
        else:
            # If not in our mapping, try to fetch from yfinance
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                if 'sector' in info and info['sector']:
                    result[symbol] = info['sector']
                else:
                    result[symbol] = "Unknown"
            except Exception as e:
                logger.warning(f"Could not get sector for {symbol}: {str(e)}")
                result[symbol] = "Unknown"
    return result

def calculate_sector_allocation(positions: Dict[str, Dict], sector_mappings: Dict[str, str]) -> Dict[str, float]:
    """Calculate current sector allocation based on positions"""
    sector_values = {}
    total_value = 0
    
    # Calculate total value and value per sector
    for symbol, position in positions.items():
        if 'quantity' in position and 'current_price' in position:
            position_value = position['quantity'] * position['current_price']
            total_value += position_value
            
            sector = sector_mappings.get(symbol, "Unknown")
            if sector in sector_values:
                sector_values[sector] += position_value
            else:
                sector_values[sector] = position_value
    
    # Calculate percentages
    sector_allocation = {}
    if total_value > 0:
        for sector, value in sector_values.items():
            sector_allocation[sector] = value / total_value
    
    return sector_allocation

def get_recommended_allocation() -> Dict[str, float]:
    """Get recommended sector allocation based on current market conditions"""
    # This could be enhanced to dynamically determine market conditions
    # For now, we'll use a neutral market assumption
    return RECOMMENDED_ALLOCATIONS["neutral_market"]

def calculate_correlation_matrix(symbols: List[str]) -> Dict:
    """Calculate correlation matrix for a list of stock symbols"""
    if not symbols:
        return {"error": "No symbols provided"}
    
    try:
        # Get historical data for the past year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Fetch data from yfinance
        data = yf.download(symbols, start=start_date, end=end_date)['Adj Close']
        
        # Calculate correlation matrix
        correlation = data.corr().round(2)
        
        # Convert to dictionary format for JSON
        result = {
            "symbols": symbols,
            "matrix": correlation.to_dict()
        }
        
        return result
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {str(e)}")
        return {"error": str(e)}

def generate_diversification_recommendations(
    positions: Dict[str, Dict],
    current_allocation: Dict[str, float],
    recommended_allocation: Dict[str, float],
    correlation_data: Dict,
    risk_metrics: Dict
) -> Dict[str, Any]:
    """Generate recommendations for improving portfolio diversification"""
    recommendations = {
        "overweight_sectors": [],
        "underweight_sectors": [],
        "high_correlation_pairs": [],
        "suggested_additions": []
    }
    
    # Identify overweight and underweight sectors
    for sector, recommended_pct in recommended_allocation.items():
        current_pct = current_allocation.get(sector, 0)
        difference = current_pct - recommended_pct
        
        if difference > 0.05:  # More than 5% overweight
            recommendations["overweight_sectors"].append({
                "sector": sector,
                "current_allocation": current_pct,
                "recommended_allocation": recommended_pct,
                "difference": difference
            })
        elif difference < -0.05:  # More than 5% underweight
            recommendations["underweight_sectors"].append({
                "sector": sector,
                "current_allocation": current_pct,
                "recommended_allocation": recommended_pct,
                "difference": difference
            })
    
    # Identify highly correlated pairs
    if "matrix" in correlation_data and "symbols" in correlation_data:
        symbols = correlation_data["symbols"]
        matrix = correlation_data["matrix"]
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i < j:  # Only check each pair once
                    correlation = matrix.get(symbol1, {}).get(symbol2, 0)
                    if correlation > 0.8:  # High correlation threshold
                        recommendations["high_correlation_pairs"].append({
                            "symbol1": symbol1,
                            "symbol2": symbol2,
                            "correlation": correlation
                        })
    
    # Suggest additions from watchlist for underweight sectors
    underweight_sectors = [r["sector"] for r in recommendations["underweight_sectors"]]
    if underweight_sectors:
        for symbol in WATCHLIST:
            if symbol not in positions:
                sector = SECTOR_MAPPING.get(symbol)
                if sector in underweight_sectors:
                    recommendations["suggested_additions"].append({
                        "symbol": symbol,
                        "sector": sector
                    })
    
    return recommendations

def calculate_diversification_score(sector_allocation: Dict[str, float]) -> float:
    """Calculate a diversification score (0-100) based on sector allocation"""
    if not sector_allocation:
        return 0
    
    # Calculate Herfindahl-Hirschman Index (HHI)
    # Lower HHI means better diversification
    hhi = sum(pct**2 for pct in sector_allocation.values())
    
    # Convert to a 0-100 score where 100 is perfectly diversified
    # Perfect diversification would be 1/n for each sector
    # For 9 sectors, perfect HHI would be 9 * (1/9)^2 = 1/9 ≈ 0.111
    perfect_hhi = 1 / len(RECOMMENDED_ALLOCATIONS["neutral_market"])
    
    # Scale the score: 100 for perfect diversification, 0 for complete concentration
    score = max(0, min(100, 100 * (1 - (hhi - perfect_hhi) / (1 - perfect_hhi))))
    
    return round(score, 1)

# Create Flask app with proper static folder configuration
app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

# Global dashboard instance
dashboard = None

# Track dashboard start time for uptime calculation
dashboard_start_time = datetime.now()

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logger.info("Shutting down dashboard...")
    # Save data before exit
    if dashboard:
        dashboard._save_data()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class TradingDashboard:
    def __init__(self):
        """Initialize the trading dashboard"""
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Calculate market times
        market_status = self.calculate_market_times()
        
        self.trading_data = {
            'positions': {},
            'daily_stats': {
                'trades': 0,
                'win_rate': 0.0,
                'total_pl': 0.0
            },
            'trade_history': [],
            'account_info': {
                'equity': 100000.0,  # Default value
                'buying_power': 100000.0,  # Default value
                'cash': 100000.0  # Default value
            },
            'market_status': market_status,
            'equity_history': [
                # Format: [timestamp, equity_value]
                [datetime.now().strftime('%Y-%m-%d'), 100000.0]  # Initial equity
            ],
            'daily_pl_history': [
                # Format: [date, pl_value]
                [datetime.now().strftime('%Y-%m-%d'), 0.0]  # Initial P/L
            ],
            'strategy_performance': {
                'breakout': {'trades': 0, 'wins': 0, 'losses': 0, 'pl': 0.0},
                'trend': {'trades': 0, 'wins': 0, 'losses': 0, 'pl': 0.0},
                'mean_reversion': {'trades': 0, 'wins': 0, 'losses': 0, 'pl': 0.0},
                'momentum': {'trades': 0, 'wins': 0, 'losses': 0, 'pl': 0.0}
            },
            'risk_metrics': {
                'portfolio_heat': 0.0,  # Percentage of capital at risk
                'drawdown': 0.0,        # Current drawdown percentage
                'max_drawdown': 0.0,    # Maximum historical drawdown
                'sharpe_ratio': 0.0,    # Sharpe ratio
                'profit_factor': 0.0,   # Gross profit / Gross loss
                'win_loss_ratio': 0.0,  # Average win / Average loss
                'avg_win': 0.0,         # Average winning trade
                'avg_loss': 0.0,        # Average losing trade
                'position_count': 0,    # Current number of positions
                'max_positions': 10,    # Maximum allowed positions
                'sector_exposure': {}   # Exposure by sector
            },
            'ml_insights': {
                'signal_confidence': {},  # Symbol -> confidence score
                'feature_importance': {},  # Feature -> importance score
                'model_performance': {
                    'accuracy': 0.0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1_score': 0.0,
                    'auc': 0.0
                },
                'recent_predictions': []  # List of recent predictions with outcomes
            },
            'bot_activity': [],  # List of bot activity logs
            'accounts': {
                'current': 'paper',  # Current active account
                'available': {
                    'paper': {
                        'name': 'Paper Trading',
                        'type': 'paper',
                        'api_key': '',
                        'api_secret': '',
                        'equity': 100000.0
                    }
                    # Live accounts will be added here
                }
            }
        }
        self.lock = threading.Lock()
        self.data_file = 'data/dashboard_data.json'
        self.log_file = 'trading_bot.log'
        self.max_log_entries = 1000  # Maximum number of log entries to keep
        
        # Load data if available
        self._load_data()
        
        # Load initial bot activity logs
        self._load_bot_logs()
        
        logger.info("Trading Dashboard initialized")
        
    def calculate_market_times(self):
        """Calculate current market status and next market times"""
        now = datetime.now()
        current_time = now.time()
        
        # Define market hours (EST)
        market_open_time = datetime.strptime('09:30:00', '%H:%M:%S').time()
        market_close_time = datetime.strptime('16:00:00', '%H:%M:%S').time()
        
        # Check if it's a weekday
        is_weekday = now.weekday() < 5
        
        # Calculate next market open time
        if is_weekday:
            if current_time < market_open_time:
                # Market opens today
                next_open = now.replace(hour=9, minute=30, second=0)
            else:
                # Market opens next business day
                next_open = now + timedelta(days=1)
                while next_open.weekday() >= 5:
                    next_open += timedelta(days=1)
                next_open = next_open.replace(hour=9, minute=30, second=0)
        else:
            # Find next Monday
            days_until_monday = (7 - now.weekday())
            next_open = now + timedelta(days=days_until_monday)
            next_open = next_open.replace(hour=9, minute=30, second=0)
        
        # Calculate next market close time
        if is_weekday and current_time < market_close_time:
            # Market closes today
            next_close = now.replace(hour=16, minute=0, second=0)
        else:
            # Market closes next business day
            next_close = next_open.replace(hour=16, minute=0, second=0)
        
        # Determine if market is currently open
        is_open = (
            is_weekday and
            market_open_time <= current_time < market_close_time
        )
        
        return {
            'is_open': is_open,
            'next_open': next_open.strftime('%Y-%m-%d %H:%M:%S'),
            'next_close': next_close.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    def update_position(self, symbol: str, position_data: dict):
        """Update position data"""
        with self.lock:
            self.trading_data['positions'][symbol] = position_data
            logger.info(f"Updated position for {symbol}: {position_data}")
            self._save_data()
            
    def update_daily_stats(self, stats: dict):
        """Update daily statistics"""
        with self.lock:
            self.trading_data['daily_stats'] = stats
            logger.info(f"Updated daily stats: {stats}")
            self._save_data()
            
    def add_trade(self, trade_data: dict):
        """Add a trade to the history"""
        with self.lock:
            self.trading_data['trade_history'].append(trade_data)
            logger.info(f"Added trade to history: {trade_data}")
            
            # Keep history manageable
            if len(self.trading_data['trade_history']) > 100:
                self.trading_data['trade_history'] = self.trading_data['trade_history'][-100:]
                
            self._save_data()
            
    def update_account(self, account_data: dict):
        """Update account information"""
        with self.lock:
            self.trading_data['account_info'] = account_data
            logger.info(f"Updated account info: {account_data}")
            self._save_data()
            
    def update_market_status(self, is_open: bool = None, next_open: str = None, next_close: str = None):
        """Update market status information"""
        with self.lock:
            if all(v is None for v in [is_open, next_open, next_close]):
                # If no parameters provided, recalculate market times
                self.trading_data['market_status'] = self.calculate_market_times()
            else:
                # Update with provided values
                if is_open is not None:
                    self.trading_data['market_status']['is_open'] = is_open
                if next_open is not None:
                    self.trading_data['market_status']['next_open'] = next_open
                if next_close is not None:
                    self.trading_data['market_status']['next_close'] = next_close
            
            logger.info(f"Updated market status: {self.trading_data['market_status']}")
            self._save_data()
            
    def update_equity(self, equity_value: float):
        """Update equity history with current value"""
        with self.lock:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Check if we already have an entry for today
            if self.trading_data['equity_history'] and self.trading_data['equity_history'][-1][0] == today:
                # Update today's entry
                self.trading_data['equity_history'][-1][1] = equity_value
            else:
                # Add new entry for today
                self.trading_data['equity_history'].append([today, equity_value])
                
            # Keep history manageable (last 90 days)
            if len(self.trading_data['equity_history']) > 90:
                self.trading_data['equity_history'] = self.trading_data['equity_history'][-90:]
                
            logger.info(f"Updated equity history: {today} = ${equity_value:.2f}")
            self._save_data()
            
    def update_daily_pl(self, pl_value: float):
        """Update daily P/L history with current value"""
        with self.lock:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Check if we already have an entry for today
            if self.trading_data['daily_pl_history'] and self.trading_data['daily_pl_history'][-1][0] == today:
                # Update today's entry
                self.trading_data['daily_pl_history'][-1][1] = pl_value
            else:
                # Add new entry for today
                self.trading_data['daily_pl_history'].append([today, pl_value])
                
            # Keep history manageable (last 90 days)
            if len(self.trading_data['daily_pl_history']) > 90:
                self.trading_data['daily_pl_history'] = self.trading_data['daily_pl_history'][-90:]
                
            logger.info(f"Updated daily P/L history: {today} = ${pl_value:.2f}")
            self._save_data()
            
    def update_strategy_performance(self, strategy: str, trade_result: dict):
        """Update strategy performance metrics"""
        with self.lock:
            if strategy not in self.trading_data['strategy_performance']:
                self.trading_data['strategy_performance'][strategy] = {
                    'trades': 0, 'wins': 0, 'losses': 0, 'pl': 0.0
                }
                
            # Update strategy metrics
            self.trading_data['strategy_performance'][strategy]['trades'] += 1
            
            if trade_result.get('profit', 0) > 0:
                self.trading_data['strategy_performance'][strategy]['wins'] += 1
            else:
                self.trading_data['strategy_performance'][strategy]['losses'] += 1
                
            self.trading_data['strategy_performance'][strategy]['pl'] += trade_result.get('profit', 0)
            
            logger.info(f"Updated strategy performance for {strategy}: {self.trading_data['strategy_performance'][strategy]}")
            self._save_data()
            
    def update_risk_metrics(self, risk_data: dict):
        """Update risk metrics"""
        with self.lock:
            self.trading_data['risk_metrics'].update(risk_data)
            logger.info(f"Updated risk metrics: {risk_data}")
            self._save_data()
            
    def update_sector_exposure(self, sector_data: dict):
        """Update sector exposure data"""
        with self.lock:
            self.trading_data['risk_metrics']['sector_exposure'] = sector_data
            logger.info(f"Updated sector exposure: {len(sector_data)} sectors")
            self._save_data()
            
    def update_ml_signal_confidence(self, symbol: str, confidence: float):
        """Update ML signal confidence for a symbol"""
        with self.lock:
            self.trading_data['ml_insights']['signal_confidence'][symbol] = confidence
            logger.info(f"Updated ML signal confidence for {symbol}: {confidence:.2f}")
            self._save_data()
            
    def update_feature_importance(self, feature_importance: dict):
        """Update feature importance data"""
        with self.lock:
            self.trading_data['ml_insights']['feature_importance'] = feature_importance
            logger.info(f"Updated feature importance with {len(feature_importance)} features")
            self._save_data()
            
    def update_model_performance(self, performance_metrics: dict):
        """Update ML model performance metrics"""
        with self.lock:
            self.trading_data['ml_insights']['model_performance'].update(performance_metrics)
            logger.info(f"Updated model performance metrics: {performance_metrics}")
            self._save_data()
            
    def add_prediction(self, prediction_data: dict):
        """Add a prediction to the recent predictions list"""
        with self.lock:
            self.trading_data['ml_insights']['recent_predictions'].append(prediction_data)
            
            # Keep history manageable (last 20 predictions)
            if len(self.trading_data['ml_insights']['recent_predictions']) > 20:
                self.trading_data['ml_insights']['recent_predictions'] = self.trading_data['ml_insights']['recent_predictions'][-20:]
                
            logger.info(f"Added prediction for {prediction_data.get('symbol')}")
            self._save_data()
            
    def add_bot_activity(self, activity_data: dict):
        """Add a bot activity log entry"""
        with self.lock:
            timestamp = activity_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Ensure activity data has required fields
            if 'message' not in activity_data:
                activity_data['message'] = 'No message provided'
                
            if 'level' not in activity_data:
                activity_data['level'] = 'INFO'
                
            # Add timestamp if not provided
            if 'timestamp' not in activity_data:
                activity_data['timestamp'] = timestamp
                
            # Add the activity to the list
            self.trading_data['bot_activity'].append(activity_data)
            
            # Keep list at a reasonable size
            if len(self.trading_data['bot_activity']) > self.max_log_entries:
                self.trading_data['bot_activity'] = self.trading_data['bot_activity'][-self.max_log_entries:]
                
            logger.info(f"Added bot activity: {activity_data['message']}")
            self._save_data()
            
    def log_trade_activity(self, trade_data: dict):
        """Log trade monitoring activity"""
        with self.lock:
            # Create a formatted message for the trade activity
            symbol = trade_data.get('symbol', 'UNKNOWN')
            action = trade_data.get('action', 'UNKNOWN')
            price = trade_data.get('price', 0.0)
            quantity = trade_data.get('quantity', 0)
            reason = trade_data.get('reason', '')
            strategy = trade_data.get('strategy', '')
            
            # Format the message based on the action type
            if action.upper() in ['BUY', 'SELL']:
                message = f"TRADE: {action.upper()} {quantity} {symbol} @ ${price:.2f}"
                if strategy:
                    message += f" | Strategy: {strategy}"
                if reason:
                    message += f" | Reason: {reason}"
            elif action.upper() in ['MONITOR', 'SCAN', 'ANALYZE']:
                message = f"MONITOR: {action.upper()} {symbol}"
                if reason:
                    message += f" | {reason}"
            elif action.upper() in ['STOP_LOSS', 'TAKE_PROFIT', 'TRAILING_STOP']:
                message = f"ORDER: {action.upper()} for {symbol} @ ${price:.2f}"
                if reason:
                    message += f" | {reason}"
            else:
                message = f"TRADE_ACTIVITY: {action} for {symbol}"
                if price:
                    message += f" @ ${price:.2f}"
                if reason:
                    message += f" | {reason}"
            
            # Create the activity data
            activity_data = {
                'timestamp': trade_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'level': 'INFO',
                'source': 'trade_monitor',
                'message': message,
                'trade_data': trade_data,  # Store the original trade data for reference
                'category': 'trade'  # Add a category to easily filter trade-related logs
            }
            
            # Add to bot activity
            self.add_bot_activity(activity_data)
            
            return message
            
    def _load_bot_logs(self):
        """Load recent bot logs from the log file"""
        try:
            if os.path.exists(self.log_file):
                # Read the last 100 lines from the log file
                from collections import deque
                with open(self.log_file, 'r') as f:
                    last_lines = deque(f, 100)
                
                # Parse log lines and add to bot activity
                for line in last_lines:
                    try:
                        # Parse log line (format: timestamp - name - level - message)
                        parts = line.strip().split(' - ', 3)
                        if len(parts) >= 4:
                            timestamp, name, level, message = parts
                            
                            # Add to bot activity
                            self.add_bot_activity({
                                'timestamp': timestamp,
                                'source': name,
                                'level': level,
                                'message': message
                            })
                    except Exception as e:
                        logger.error(f"Error parsing log line: {str(e)}")
                
                logger.info(f"Loaded {len(self.trading_data['bot_activity'])} bot activity logs")
        except Exception as e:
            logger.error(f"Failed to load bot logs: {str(e)}")
            
    def update_account_settings(self, account_data: dict):
        """Update account settings"""
        with self.lock:
            # Update accounts data
            if 'accounts' in account_data:
                self.trading_data['accounts']['available'].update(account_data['accounts'])
                
            # Switch active account if specified
            if 'current' in account_data:
                new_account = account_data['current']
                if new_account in self.trading_data['accounts']['available']:
                    old_account = self.trading_data['accounts']['current']
                    self.trading_data['accounts']['current'] = new_account
                    logger.info(f"Switched active account from {old_account} to {new_account}")
                    
                    # Add activity log for account switch
                    self.add_bot_activity({
                        'message': f"Switched active account from {old_account} to {new_account}",
                        'level': 'INFO',
                        'source': 'dashboard'
                    })
                else:
                    logger.error(f"Cannot switch to non-existent account: {new_account}")
            
            self._save_data()
            
    def get_active_account(self):
        """Get the currently active account"""
        return {
            'current': self.trading_data['accounts']['current'],
            'details': self.trading_data['accounts']['available'].get(
                self.trading_data['accounts']['current'], {}
            )
        }
    
    def _validate_data(self):
        """Validate and ensure all required data fields are present"""
        try:
            # Ensure all required top-level keys exist
            required_keys = [
                'positions', 'daily_stats', 'trade_history', 'account_info',
                'market_status', 'equity_history', 'daily_pl_history',
                'strategy_performance', 'risk_metrics', 'ml_insights', 'bot_activity'
            ]
            
            for key in required_keys:
                if key not in self.trading_data:
                    if key in ['positions', 'trade_history', 'bot_activity', 'equity_history', 'daily_pl_history']:
                        # Initialize as empty collections
                        self.trading_data[key] = [] if key in ['trade_history', 'bot_activity', 'equity_history', 'daily_pl_history'] else {}
                    else:
                        # Initialize as empty objects
                        self.trading_data[key] = {}
            
            # Ensure daily_stats has required fields
            if 'daily_stats' in self.trading_data:
                daily_stats_fields = ['trades', 'win_rate', 'total_pl']
                for field in daily_stats_fields:
                    if field not in self.trading_data['daily_stats']:
                        self.trading_data['daily_stats'][field] = 0.0
            
            # Ensure account_info has required fields
            if 'account_info' in self.trading_data:
                account_fields = ['equity', 'buying_power', 'cash']
                for field in account_fields:
                    if field not in self.trading_data['account_info']:
                        self.trading_data['account_info'][field] = 0.0
            
            # Ensure market_status has required fields
            if 'market_status' in self.trading_data:
                market_fields = ['is_open', 'next_open', 'next_close']
                for field in market_fields:
                    if field not in self.trading_data['market_status']:
                        if field == 'is_open':
                            self.trading_data['market_status'][field] = False
                        else:
                            self.trading_data['market_status'][field] = ""
            
            # Ensure ml_insights has required fields
            if 'ml_insights' in self.trading_data:
                ml_fields = ['signal_confidence', 'feature_importance', 'model_performance', 'recent_predictions']
                for field in ml_fields:
                    if field not in self.trading_data['ml_insights']:
                        if field in ['signal_confidence', 'feature_importance']:
                            self.trading_data['ml_insights'][field] = {}
                        elif field == 'model_performance':
                            self.trading_data['ml_insights'][field] = {
                                'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0, 'auc': 0.0
                            }
                        else:
                            self.trading_data['ml_insights'][field] = []
            
            # Ensure risk_metrics has required fields
            if 'risk_metrics' in self.trading_data:
                risk_fields = [
                    'portfolio_heat', 'drawdown', 'max_drawdown', 'sharpe_ratio', 
                    'profit_factor', 'win_loss_ratio', 'avg_win', 'avg_loss', 
                    'position_count', 'max_positions', 'sector_exposure'
                ]
                for field in risk_fields:
                    if field not in self.trading_data['risk_metrics']:
                        if field == 'sector_exposure':
                            self.trading_data['risk_metrics'][field] = {}
                        elif field == 'max_positions':
                            self.trading_data['risk_metrics'][field] = 10
                        else:
                            self.trading_data['risk_metrics'][field] = 0.0
            
            # Ensure strategy_performance has required fields
            if 'strategy_performance' in self.trading_data:
                strategy_types = ['breakout', 'trend', 'mean_reversion', 'momentum']
                for strategy in strategy_types:
                    if strategy not in self.trading_data['strategy_performance']:
                        self.trading_data['strategy_performance'][strategy] = {
                            'trades': 0, 'wins': 0, 'losses': 0, 'pl': 0.0
                        }
            
            logger.info("Dashboard data validation complete")
            return True
        except Exception as e:
            logger.error(f"Error validating dashboard data: {str(e)}")
            return False
            
    def _save_data(self):
        """Save trading data to file"""
        try:
            # Validate data before saving
            self._validate_data()
            
            with open(self.data_file, 'w') as f:
                json_data = json.dumps(self.trading_data)
                f.write(json_data)
                logger.info(f"Saved dashboard data to {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to save dashboard data: {str(e)}")
            
    def _load_data(self):
        """Load trading data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    import json
                    self.trading_data = json.load(f)
                
                # Validate loaded data
                self._validate_data()
                
                logger.info(f"Loaded dashboard data with {len(self.trading_data['trade_history'])} trades and {len(self.trading_data['positions'])} positions")
        except Exception as e:
            logger.error(f"Failed to load dashboard data: {str(e)}")

# Route handlers
@app.route('/')
def home():
    """Render dashboard home page"""
    return render_template('dashboard.html')

@app.route('/logs')
def logs():
    """Render bot activity logs page"""
    return render_template('logs.html')

@app.route('/accounts')
def accounts():
    """Render account management page"""
    return render_template('accounts.html')

@app.route('/api/data')
def get_data():
    """API endpoint to get dashboard data."""
    try:
        # Get account info from the trading bot
        account_info = trading_bot.get_account_info()
        
        # Add platform information to account info
        account_info['platform'] = trading_bot.active_broker.platform_id if trading_bot.active_broker else 'alpaca'
        
        # Get positions from the trading bot
        positions = trading_bot.get_positions()
        
        # Get trades from the data store
        trades = _load_data()
        
        # Ensure each trade has platform information
        for trade in trades:
            if 'platform' not in trade:
                # Default to alpaca for backward compatibility
                trade['platform'] = 'alpaca'
        
        # Return the data as JSON
        return jsonify({
            'account': account_info,
            'positions': positions,
            'trades': trades
        })
    except Exception as e:
        app.logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """Get bot activity logs as JSON"""
    return jsonify(dashboard.trading_data.get('bot_activity', []))

@app.route('/api/test')
def test_api():
    """Test API endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'API is working'
    })

@app.route('/api/accounts')
def get_accounts():
    """Get account information as JSON"""
    return jsonify(dashboard.get_active_account())

@app.route('/api/accounts/switch', methods=['POST'])
def switch_account():
    """Switch the active trading account"""
    try:
        data = request.json
        if not data or 'account' not in data:
            return jsonify({'error': 'Missing account parameter'}), 400
            
        account_id = data['account']
        dashboard.update_account_settings({'current': account_id})
        
        return jsonify({
            'success': True,
            'message': f'Switched to account: {account_id}',
            'account': dashboard.get_active_account()
        })
    except Exception as e:
        logger.error(f"Error switching account: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/add', methods=['POST'])
def add_account():
    """Add a new trading account"""
    try:
        data = request.json
        if not data or 'account_id' not in data or 'account_data' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        account_id = data['account_id']
        account_data = data['account_data']
        
        # Add the new account
        dashboard.update_account_settings({
            'accounts': {
                account_id: account_data
            }
        })
        
        return jsonify({
            'success': True,
            'message': f'Added account: {account_id}',
            'accounts': dashboard.trading_data['accounts']
        })
    except Exception as e:
        logger.error(f"Error adding account: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """API endpoint for health check"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0.0',
        'dashboard_uptime': get_uptime()
    }
    return jsonify(status)

@app.route('/api/status')
def system_status():
    """Get system status information"""
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    
    # Get dashboard uptime
    uptime = get_uptime()
    
    # Get bot status - check if main.py is running
    bot_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' and any('main.py' in cmd for cmd in proc.info['cmdline'] if cmd):
                bot_running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Get market status from dashboard data
    market_status = {}
    if dashboard:
        with dashboard.lock:
            if 'market_status' in dashboard.trading_data:
                market_status = dashboard.trading_data['market_status']
    
    return jsonify({
        'status': 'ok',
        'bot_running': bot_running,
        'dashboard_uptime': uptime,
        'market_status': market_status,
        'system_metrics': {
            'cpu_usage': cpu_percent,
            'memory_usage': memory_percent,
            'disk_usage': disk_percent
        }
    })

@app.route('/api/portfolio/diversification')
def portfolio_diversification():
    """Get portfolio diversification analysis"""
    if not dashboard:
        return jsonify({'error': 'Dashboard not initialized'}), 500
    
    with dashboard.lock:
        # Get current positions
        positions = dashboard.trading_data.get('positions', {})
        
        # Get sector mappings for stocks in positions
        sector_mappings = get_sector_mappings([symbol for symbol in positions])
        
        # Calculate current sector allocation
        sector_allocation = calculate_sector_allocation(positions, sector_mappings)
        
        # Get recommended sector allocation based on market conditions
        recommended_allocation = get_recommended_allocation()
        
        # Calculate correlation matrix for current holdings
        correlation_matrix = calculate_correlation_matrix([symbol for symbol in positions])
        
        # Generate diversification recommendations
        recommendations = generate_diversification_recommendations(
            positions, 
            sector_allocation, 
            recommended_allocation,
            correlation_matrix,
            dashboard.trading_data.get('risk_metrics', {})
        )
        
        return jsonify({
            'status': 'ok',
            'current_allocation': sector_allocation,
            'recommended_allocation': recommended_allocation,
            'correlation_data': correlation_matrix,
            'recommendations': recommendations,
            'diversification_score': calculate_diversification_score(sector_allocation)
        })

@app.route('/vision-test')
def vision_test():
    """Test endpoint for vision features"""
    return render_template('vision_test.html')

@app.route('/api/platforms')
def get_platforms():
    """Get available trading platforms"""
    platforms = []
    for platform_id, platform_config in PLATFORMS.items():
        if platform_config.get('enabled', False):
            platforms.append({
                'id': platform_id,
                'name': platform_config.get('name', platform_id),
                'type': platform_config.get('type', 'unknown'),
                'default': platform_config.get('default', False)
            })
    
    # Get the active platform from the trading bot
    active_platform = ""
    try:
        from trading_bot import trading_bot
        if trading_bot and hasattr(trading_bot, 'get_active_platform'):
            active_platform = trading_bot.get_active_platform()
    except:
        pass
    
    return jsonify({
        'platforms': platforms,
        'active_platform': active_platform
    })

@app.route('/api/platforms/switch', methods=['POST'])
def switch_platform():
    """Switch the active trading platform"""
    try:
        data = request.json
        if not data or 'platform' not in data:
            return jsonify({'error': 'Missing platform parameter'}), 400
            
        platform_id = data['platform']
        
        # Switch the platform in the trading bot
        from trading_bot import trading_bot
        if not trading_bot or not hasattr(trading_bot, 'switch_platform'):
            return jsonify({'error': 'Trading bot not available'}), 500
            
        success = trading_bot.switch_platform(platform_id)
        if not success:
            return jsonify({'error': f'Failed to switch to platform: {platform_id}'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Switched to platform: {platform_id}',
            'platform': platform_id
        })
    except Exception as e:
        logger.error(f"Error switching platform: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_uptime():
    """Calculate dashboard uptime"""
    uptime = datetime.now() - dashboard_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def run_dashboard():
    """Run the dashboard server"""
    try:
        # Always use port 5001 for consistency
        app.run(host='0.0.0.0', port=5001, threaded=True)
    except Exception as e:
        logger.error(f"Error running dashboard: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        # Create necessary directories
        os.makedirs('data', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Create dashboard template if it doesn't exist
        template_path = os.path.join('templates', 'dashboard.html')
        if not os.path.exists(template_path):
            logger.info(f"Creating dashboard template at {template_path}")
            with open(template_path, 'w') as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KryptoBot Trading Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .card {
            margin-bottom: 20px;
        }
        .position-card {
            border-left: 4px solid #007bff;
        }
        .profit {
            color: #28a745;
        }
        .loss {
            color: #dc3545;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">KryptoBot Trading Dashboard</span>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Account Summary -->
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Account Summary</h5>
                        <p>Equity: $<span id="equity">0.00</span></p>
                        <p>Buying Power: $<span id="buying-power">0.00</span></p>
                        <p>Cash: $<span id="cash">0.00</span></p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Daily Statistics</h5>
                        <p>Total Trades: <span id="total-trades">0</span></p>
                        <p>Win Rate: <span id="win-rate">0.00</span>%</p>
                        <p>Total P/L: $<span id="total-pl">0.00</span></p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Bot Status</h5>
                        <p>Status: <span id="bot-status" class="badge bg-success">Running</span></p>
                        <p>Last Update: <span id="last-update">-</span></p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Active Positions -->
        <div class="row mt-4">
            <div class="col-12">
                <h4>Active Positions</h4>
                <div id="positions-container"></div>
            </div>
        </div>

        <!-- Trade History -->
        <div class="row mt-4">
            <div class="col-12">
                <h4>Trade History</h4>
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Quantity</th>
                                <th>Price</th>
                                <th>Type</th>
                            </tr>
                        </thead>
                        <tbody id="trade-history">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    // Update account info
                    document.getElementById('equity').textContent = data.account_info.equity.toFixed(2);
                    document.getElementById('buying-power').textContent = data.account_info.buying_power.toFixed(2);
                    document.getElementById('cash').textContent = data.account_info.cash.toFixed(2);

                    // Update daily stats
                    document.getElementById('total-trades').textContent = data.daily_stats.trades;
                    document.getElementById('win-rate').textContent = data.daily_stats.win_rate.toFixed(2);
                    document.getElementById('total-pl').textContent = data.daily_stats.total_pl.toFixed(2);

                    // Update positions
                    const positionsContainer = document.getElementById('positions-container');
                    positionsContainer.innerHTML = '';
                    
                    Object.entries(data.positions).forEach(([symbol, position]) => {
                        const card = document.createElement('div');
                        card.className = 'card position-card mb-3';
                        card.innerHTML = `
                            <div class="card-body">
                                <h5 class="card-title">${symbol}</h5>
                                <div class="row">
                                    <div class="col-md-4">
                                        <p>Quantity: ${position.quantity}</p>
                                        <p>Entry Price: $${position.entry_price.toFixed(2)}</p>
                                    </div>
                                    <div class="col-md-4">
                                        <p>Current Price: $${position.current_price.toFixed(2)}</p>
                                        <p class="${position.unrealized_pl >= 0 ? 'profit' : 'loss'}">
                                            P/L: $${position.unrealized_pl.toFixed(2)}
                                        </p>
                                    </div>
                                    <div class="col-md-4">
                                        <p>Stop Loss: $${position.stop_loss.toFixed(2)}</p>
                                        <p>Take Profit: $${position.take_profit.toFixed(2)}</p>
                                    </div>
                                </div>
                            </div>
                        `;
                        positionsContainer.appendChild(card);
                    });

                    // Update trade history
                    const tradeHistory = document.getElementById('trade-history');
                    tradeHistory.innerHTML = '';
                    
                    data.trade_history.slice(-10).reverse().forEach(trade => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${trade.time}</td>
                            <td>${trade.symbol}</td>
                            <td>${trade.side}</td>
                            <td>${trade.quantity}</td>
                            <td>$${trade.price.toFixed(2)}</td>
                            <td>${trade.type}</td>
                        `;
                        tradeHistory.appendChild(row);
                    });

                    // Update last update time
                    document.getElementById('last-update').textContent = new Date().toLocaleString();
                });
        }

        // Update dashboard every 5 seconds
        setInterval(updateDashboard, 5000);
        updateDashboard();  // Initial update
    </script>
</body>
</html>""")
        
        # Initialize dashboard
        logger.info("Starting dashboard server...")
        dashboard = TradingDashboard()
        
        # Write PID file for process management
        with open('dashboard.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Run dashboard
        run_dashboard()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1) 