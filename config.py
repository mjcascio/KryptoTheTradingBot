from typing import Dict, List

# Trading schedule
MARKET_OPEN = "09:30"
MARKET_CLOSE = "16:00"
TIMEZONE = "America/New_York"

# Trading parameters
MAX_POSITION_SIZE_PCT = 0.05   # Maximum 5% of portfolio per position
TOTAL_RISK_PCT = 0.02         # Maximum 2% risk per trade
MAX_TRADES_PER_DAY = 5        # Maximum number of trades per day
MIN_SUCCESS_PROBABILITY = 0.7  # Minimum probability of success for a trade
MIN_POSITION_SIZE = 1000      # Minimum position size in dollars

# Technical Analysis Parameters
BREAKOUT_PARAMS = {
    "volume_threshold": 1.5,      # Lowered from 2.0 to 1.5x average volume
    "price_threshold": 0.015,     # Lowered from 2% to 1.5% price movement
    "lookback_period": 15,        # Shortened from 20 to 15 days for more recent patterns
    "consolidation_threshold": 0.015  # Increased from 1% to 1.5% for consolidation
}

TREND_PARAMS = {
    "short_ma": 9,               # Keeping short-term MA
    "medium_ma": 20,             # Slightly adjusted from 21 to 20
    "long_ma": 50,               # Keeping long-term MA
    "rsi_period": 14,            # Keeping standard RSI period
    "rsi_overbought": 65,        # Lowered from 70 to 65
    "rsi_oversold": 35,          # Raised from 30 to 35
    "volume_ma": 20              # Keeping volume MA period
}

# Risk Management (keeping conservative)
STOP_LOSS_PCT = 0.02            # Keeping 2% stop loss
TAKE_PROFIT_PCT = 0.06          # Keeping 6% take profit
MAX_DAILY_LOSS_PCT = 0.05       # Keeping 5% max daily loss
POSITION_SIZING_VOLATILITY_MULTIPLIER = 1.5

# Trading Universe
WATCHLIST: List[str] = [
    # Tech Giants & Software (25 stocks)
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "TSLA",
    "INTC", "CRM", "ADBE", "ORCL", "CSCO", "IBM", "QCOM",
    "NOW", "SNOW", "ZS", "PANW", "FTNT", "NET", "ANET", "MU", "AVGO", "TXN",
    
    # Financial Services (20 stocks)
    "JPM", "V", "BAC", "MA", "WFC", "GS", "MS", "BLK", 
    "C", "AXP", "SCHW", "USB", "PNC", "TFC", "COF",
    "SPGI", "MCO", "ICE", "CME", "COIN",
    
    # Healthcare & Biotech (18 stocks)
    "JNJ", "PFE", "UNH", "ABT", "TMO", "DHR", "BMY", "ABBV",
    "LLY", "AMGN", "CVS", "MRK", "MDT", "ISRG", "GILD",
    "REGN", "VRTX", "HUM",
    
    # Consumer & Retail (15 stocks)
    "WMT", "PG", "HD", "COST", "TGT", "NKE", "SBUX", "MCD",
    "KO", "PEP", "DIS", "LOW", "TJX", "LULU", "ULTA",
    
    # Industrial & Energy (15 stocks)
    "XOM", "CVX", "CAT", "BA", "HON", "UNP", "GE", "MMM",
    "LMT", "RTX", "DE", "DUK", "NEE", "SLB", "EOG",
    
    # Communication & Media (12 stocks)
    "NFLX", "CMCSA", "VZ", "T", "TMUS", "ATVI", "EA",
    "ROKU", "TTD", "SNAP", "PINS", "SPOT",
    
    # Materials & Chemicals (10 stocks)
    "LIN", "APD", "ECL", "DD", "NEM", "FCX", "DOW", "NUE", "CF", "MOS",
    
    # Real Estate & Construction (10 stocks)
    "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "AVB", "EQR", "VMC", "MLM"
]

# Strategy Weights for Scoring
STRATEGY_WEIGHTS: Dict[str, float] = {
    "breakout": 0.4,
    "trend": 0.4,
    "volume": 0.2
}

# API Configuration
API_RATE_LIMIT = 200  # requests per minute
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 