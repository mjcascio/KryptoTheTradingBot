"""Strategy parameters for the KryptoBot Trading System."""

# Breakout strategy parameters
BREAKOUT_PARAMS = {
    "lookback_period": 20,
    "volatility_factor": 2.0,
    "min_volume_increase": 1.5,
    "confirmation_candles": 2,
    "stop_loss_atr_multiple": 2.0,
    "take_profit_atr_multiple": 3.0,
    "max_position_size_pct": 0.05,
    "risk_per_trade_pct": 0.01,
    "max_trades_per_day": 5,
    "min_consolidation_days": 5,
    "max_consolidation_days": 30,
    "min_price": 5.0,
    "min_volume": 500000,
    "enabled": True
}

# Trend following strategy parameters
TREND_PARAMS = {
    "fast_ema": 9,
    "slow_ema": 21,
    "signal_ema": 9,
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "atr_period": 14,
    "stop_loss_atr_multiple": 2.0,
    "take_profit_atr_multiple": 3.0,
    "max_position_size_pct": 0.05,
    "risk_per_trade_pct": 0.01,
    "max_trades_per_day": 5,
    "min_price": 5.0,
    "min_volume": 500000,
    "enabled": True
}

# Mean reversion strategy parameters
MEAN_REVERSION_PARAMS = {
    "lookback_period": 20,
    "std_dev_threshold": 2.0,
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "bollinger_period": 20,
    "bollinger_std_dev": 2.0,
    "stop_loss_atr_multiple": 1.5,
    "take_profit_atr_multiple": 2.0,
    "max_position_size_pct": 0.05,
    "risk_per_trade_pct": 0.01,
    "max_trades_per_day": 5,
    "min_price": 5.0,
    "min_volume": 500000,
    "enabled": True
}

# Sentiment-based strategy parameters
SENTIMENT_PARAMS = {
    "min_sentiment_score": 0.6,
    "sentiment_lookback_days": 3,
    "news_weight": 0.4,
    "social_weight": 0.3,
    "analyst_weight": 0.3,
    "stop_loss_atr_multiple": 2.0,
    "take_profit_atr_multiple": 3.0,
    "max_position_size_pct": 0.05,
    "risk_per_trade_pct": 0.01,
    "max_trades_per_day": 3,
    "min_price": 5.0,
    "min_volume": 500000,
    "enabled": True
}

# Machine learning strategy parameters
ML_PARAMS = {
    "model_type": "random_forest",
    "prediction_horizon": 5,  # days
    "training_lookback": 252,  # trading days (1 year)
    "retraining_frequency": 30,  # days
    "feature_selection": True,
    "min_prediction_confidence": 0.65,
    "stop_loss_atr_multiple": 2.0,
    "take_profit_atr_multiple": 3.0,
    "max_position_size_pct": 0.05,
    "risk_per_trade_pct": 0.01,
    "max_trades_per_day": 3,
    "min_price": 5.0,
    "min_volume": 500000,
    "enabled": True
} 