import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
import logging

logger = logging.getLogger(__name__)

class MLSignalEnhancer:
    def __init__(self, model_path=None):
        """
        Initialize the ML Signal Enhancer
        
        Args:
            model_path: Path to pre-trained model file
        """
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        if model_path is None:
            model_path = 'models/signal_model.joblib'
            
        self.model_path = model_path
        self.model = self._load_model()
        self.scaler = StandardScaler()
        self.feature_columns = [
            'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower', 
            'volume_ratio', 'price_change', 'atr', 'trend_strength'
        ]
        
    def _load_model(self):
        """Load pre-trained model or create a new one"""
        if os.path.exists(self.model_path):
            logger.info(f"Loading ML model from {self.model_path}")
            return joblib.load(self.model_path)
        else:
            logger.info("No existing model found. Creating new RandomForest model.")
            return RandomForestClassifier(
                n_estimators=100, 
                max_depth=5,
                random_state=42
            )
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI technical indicator"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD technical indicator"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        return macd_line, signal_line
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands technical indicator"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, lower_band
    
    def _calculate_atr(self, data, period=14):
        """Calculate Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _calculate_trend_strength(self, prices, period=50):
        """Calculate trend strength indicator"""
        # Linear regression slope
        x = np.arange(period)
        regress_slopes = [0] * (period - 1)
        
        for i in range(period - 1, len(prices)):
            y = prices.iloc[i - period + 1:i + 1].values
            slope, _ = np.polyfit(x, y, 1)
            regress_slopes.append(slope)
            
        return pd.Series(regress_slopes, index=prices.index)
    
    def _extract_features(self, data):
        """Extract ML features from price data"""
        features = pd.DataFrame(index=data.index)
        
        # RSI
        features['rsi'] = self._calculate_rsi(data['close'])
        
        # MACD
        macd, signal = self._calculate_macd(data['close'])
        features['macd'] = macd
        features['macd_signal'] = signal
        
        # Bollinger Bands
        upper, lower = self._calculate_bollinger_bands(data['close'])
        features['bb_upper'] = (data['close'] - upper) / upper  # Normalized distance
        features['bb_lower'] = (data['close'] - lower) / lower  # Normalized distance
        
        # Volume features
        features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
        
        # Price action
        features['price_change'] = data['close'].pct_change(5)
        features['atr'] = self._calculate_atr(data)
        
        # Trend strength
        features['trend_strength'] = self._calculate_trend_strength(data['close'])
        
        return features.fillna(0)
    
    def enhance_signal(self, data, base_signal):
        """
        Enhance trading signal with ML prediction
        
        Args:
            data: DataFrame with OHLCV data
            base_signal: Dictionary with base signal parameters
            
        Returns:
            Dictionary with enhanced signal parameters
        """
        try:
            # Extract features
            features = self._extract_features(data)
            latest_features = features.iloc[-1:].values
            
            # Scale features
            scaled_features = self.scaler.fit_transform(latest_features)
            
            # Get probability from model
            probability = self.model.predict_proba(scaled_features)[0][1]
            
            logger.info(f"ML signal enhancement: Base probability: {base_signal['probability']:.2f}, ML probability: {probability:.2f}")
            
            # Combine ML signal with technical signal
            enhanced_signal = {
                'entry_price': base_signal['entry_price'],
                'stop_loss': base_signal['stop_loss'],
                'take_profit': base_signal['take_profit'],
                'ml_probability': probability,
                'combined_score': (base_signal['probability'] + probability) / 2,
                'confidence': probability * base_signal['probability'],
                'position_size_modifier': base_signal['position_size_modifier']
            }
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"Error enhancing signal with ML: {str(e)}")
            return base_signal
    
    def train(self, historical_data, historical_signals, outcomes):
        """
        Train the ML model with historical data
        
        Args:
            historical_data: List of DataFrames with OHLCV data
            historical_signals: List of signal dictionaries
            outcomes: List of trade outcomes (1 for profit, 0 for loss)
            
        Returns:
            Dictionary with training results
        """
        try:
            logger.info("Training ML model with historical data")
            all_features = []
            all_outcomes = []
            
            # Process each historical trade
            for i, data in enumerate(historical_data):
                features = self._extract_features(data)
                outcome = outcomes[i]  # 1 for profitable, 0 for loss
                
                # Add to training data
                all_features.append(features.iloc[-1].values)
                all_outcomes.append(outcome)
            
            # Convert to numpy arrays
            X = np.array(all_features)
            y = np.array(all_outcomes)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            logger.info(f"ML model trained and saved to {self.model_path}")
            
            # Calculate feature importance
            feature_importance = dict(zip(self.feature_columns, 
                                         self.model.feature_importances_))
            
            return {
                'accuracy': self.model.score(X_scaled, y),
                'feature_importance': feature_importance
            }
            
        except Exception as e:
            logger.error(f"Error training ML model: {str(e)}")
            return {'accuracy': 0, 'feature_importance': {}}
            
    def generate_dummy_training_data(self, symbol, market_data_service, num_samples=100):
        """
        Generate dummy training data for initial model training
        
        Args:
            symbol: Stock symbol to use
            market_data_service: Market data service instance
            num_samples: Number of samples to generate
            
        Returns:
            Tuple of (historical_data, outcomes)
        """
        logger.info(f"Generating dummy training data for {symbol}")
        
        try:
            # Get historical data
            data = market_data_service.get_market_data(symbol, timeframe='1D', limit=200)
            
            if data is None or data.empty:
                logger.error("Failed to get market data for dummy training")
                return [], []
                
            # Generate samples
            historical_data = []
            outcomes = []
            
            # Make sure we have enough data
            if len(data) < 50:
                logger.error(f"Not enough data points for {symbol}: {len(data)}")
                return [], []
                
            # Check for NaN values
            if data.isnull().values.any():
                logger.warning(f"Data contains NaN values, filling with forward fill")
                data = data.ffill().bfill()  # Forward fill then backward fill
                
            # Make sure high values are valid
            if (data['high'] <= 0).any():
                logger.error("Data contains invalid high values")
                return [], []
                
            for i in range(min(num_samples, len(data) - 50)):
                # Random start index
                start_idx = np.random.randint(0, len(data) - 50)
                end_idx = start_idx + 50
                
                # Extract sample
                sample = data.iloc[start_idx:end_idx].copy()
                
                # Generate outcome (biased towards success)
                outcome = 1 if np.random.random() > 0.3 else 0
                
                historical_data.append(sample)
                outcomes.append(outcome)
                
            logger.info(f"Generated {len(historical_data)} dummy training samples")
            return historical_data, outcomes
            
        except Exception as e:
            logger.error(f"Error generating dummy training data: {str(e)}")
            return [], [] 