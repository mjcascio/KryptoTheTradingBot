"""Constants used throughout the KryptoBot Trading System."""

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

# Default values for dashboard data
DEFAULT_ACCOUNT_INFO = {
    'equity': 100000.0,
    'buying_power': 100000.0,
    'cash': 100000.0
}

DEFAULT_DAILY_STATS = {
    'trades': 0,
    'win_rate': 0.0,
    'total_pl': 0.0
}

DEFAULT_RISK_METRICS = {
    'portfolio_heat': 0.0,
    'drawdown': 0.0,
    'max_drawdown': 0.0,
    'sharpe_ratio': 0.0,
    'profit_factor': 0.0,
    'win_loss_ratio': 0.0,
    'avg_win': 0.0,
    'avg_loss': 0.0,
    'position_count': 0,
    'max_positions': 10,
    'sector_exposure': {}
}

DEFAULT_ML_INSIGHTS = {
    'signal_confidence': {},
    'feature_importance': {},
    'model_performance': {
        'accuracy': 0.0,
        'precision': 0.0,
        'recall': 0.0,
        'f1_score': 0.0,
        'auc': 0.0
    },
    'recent_predictions': []
}

# Market hours (EST)
MARKET_HOURS = {
    'open': '09:30:00',
    'close': '16:00:00'
}

# Market hours as individual constants
MARKET_OPEN = '09:30:00'
MARKET_CLOSE = '16:00:00'
TIMEZONE = 'America/New_York'

# Platform configurations
PLATFORMS = {
    'alpaca': {
        'enabled': True,
        'name': 'Alpaca Markets',
        'type': 'stocks',
        'default': True,
        'paper_trading': True,
        'base_url': 'https://paper-api.alpaca.markets'
    },
    'metatrader': {
        'enabled': False,
        'name': 'MetaTrader',
        'type': 'forex',
        'default': False
    }
}

# Watchlists
WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'V', 'JNJ',
    'PG', 'UNH', 'HD', 'BAC', 'MA', 'XOM', 'CVX', 'LLY', 'AVGO', 'MRK',
    'PEP', 'KO', 'ABBV', 'COST', 'WMT', 'TMO', 'MCD', 'CSCO', 'ACN', 'ABT',
    'CRM', 'DHR', 'NEE', 'NKE', 'TXN', 'ADBE', 'AMD', 'CMCSA', 'INTC', 'QCOM'
]

FOREX_WATCHLIST = [
    'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD',
    'EUR/GBP', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY', 'EUR/AUD', 'EUR/CAD', 'USD/MXN'
]

# Maximum number of entries to keep
MAX_LOG_ENTRIES = 1000
MAX_TRADE_HISTORY = 100
MAX_EQUITY_HISTORY = 90
MAX_PL_HISTORY = 90
MAX_PREDICTIONS = 20 