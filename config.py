from typing import Dict, List

# Trading schedule
MARKET_OPEN = "09:30"
MARKET_CLOSE = "16:00"
TIMEZONE = "America/New_York"

# Trading parameters - ADJUSTED FOR MORE AGGRESSIVE TRADING (LEVEL 4/10)
MAX_POSITION_SIZE_PCT = 0.08   # Increased from 5% to 8% of portfolio per position
TOTAL_RISK_PCT = 0.03         # Increased from 2% to 3% risk per trade
MIN_SUCCESS_PROBABILITY = 0.55  # Lowered from 0.65 to 0.55 probability threshold
MIN_POSITION_SIZE = 800      # Lowered from 1000 to 800 dollars

# Technical Analysis Parameters - ADJUSTED FOR MORE AGGRESSIVE TRADING
BREAKOUT_PARAMS = {
    "volume_threshold": 1.3,      # Lowered from 1.5 to 1.3x average volume
    "price_threshold": 0.012,     # Lowered from 1.5% to 1.2% price movement
    "lookback_period": 12,        # Shortened from 15 to 12 days for more recent patterns
    "consolidation_threshold": 0.012  # Decreased from 1.5% to 1.2% for consolidation
}

TREND_PARAMS = {
    "short_ma": 8,               # Shortened from 9 to 8 for faster signals
    "medium_ma": 18,             # Shortened from 20 to 18
    "long_ma": 45,               # Shortened from 50 to 45
    "rsi_period": 12,            # Shortened from 14 to 12 for faster signals
    "rsi_overbought": 70,        # Increased from 65 to 70
    "rsi_oversold": 30,          # Decreased from 35 to 30
    "volume_ma": 15              # Shortened from 20 to 15
}

# Risk Management - ADJUSTED FOR MORE AGGRESSIVE TRADING
STOP_LOSS_PCT = 0.025           # Increased from 2% to 2.5% stop loss
TAKE_PROFIT_PCT = 0.075         # Increased from 6% to 7.5% take profit
MAX_DAILY_LOSS_PCT = 0.07       # Increased from 5% to 7% max daily loss
POSITION_SIZING_VOLATILITY_MULTIPLIER = 1.8  # Increased from 1.5 to 1.8

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

# Forex Trading Universe - Not used since MetaTrader is disabled
FOREX_WATCHLIST: List[str] = []

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

# Sleep Mode Configuration
SLEEP_MODE = {
    "enabled": True,
    "night": {
        "enabled": True,
        "sleep_time": "20:00",    # Market close + 4 hours
        "wake_time": "09:15",     # 15 minutes before market open
        "timezone": TIMEZONE
    },
    "weekend": {
        "enabled": True,
        "sleep_day": 5,           # Friday
        "sleep_time": "20:00",    # Market close + 4 hours
        "wake_day": 1,            # Monday
        "wake_time": "09:15",     # 15 minutes before market open
        "timezone": TIMEZONE
    },
    "logging": {
        "sleep_events": True,     # Log when bot enters/exits sleep mode
        "state_changes": True     # Log all sleep-related state changes
    }
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Multi-Platform Configuration
PLATFORMS = {
    "alpaca": {
        "enabled": True,
        "default": True,
        "type": "stocks",
        "watchlist": WATCHLIST,
        "options_enabled": True  # Enable options trading
    },
    "metatrader": {
        "enabled": False,
        "default": False,
        "type": "forex",
        "watchlist": FOREX_WATCHLIST
    }
}

# Options Trading Configuration
OPTIONS_CONFIG = {
    "enabled": True,
    "min_volume": 100,           # Minimum average daily volume
    "min_open_interest": 50,     # Minimum open interest
    "max_bid_ask_spread": 0.10,  # Maximum bid-ask spread as percentage
    "preferred_expiries": [7, 14, 30, 45, 60],  # Preferred days to expiration
    "strategy_weights": {
        "momentum": 0.4,
        "volatility": 0.3,
        "mean_reversion": 0.3
    },
    "position_sizing": {
        "max_position_size_pct": 0.05,  # Maximum position size as percentage of portfolio
        "max_loss_per_trade_pct": 0.02  # Maximum loss per trade as percentage of portfolio
    }
} 