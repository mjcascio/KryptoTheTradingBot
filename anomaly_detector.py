#!/usr/bin/env python3
"""
Anomaly Detector Module

This module implements an anomaly detection system using deep neural networks
to identify unusual market patterns that may indicate trading opportunities.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Dense, LSTM, RepeatVector, TimeDistributed, Input, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("anomaly_detector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs('models/anomaly_detector', exist_ok=True)
os.makedirs('results/anomaly_detector', exist_ok=True)

class AnomalyDetector:
    """
    Anomaly detector using autoencoder neural network to identify unusual market patterns.
    """
    
    def __init__(self, model_path=None):
        """
        Initialize the anomaly detector
        
        Args:
            model_path: Path to pre-trained model file
        """
        if model_path is None:
            model_path = 'models/anomaly_detector/model.h5'
            
        self.model_path = model_path
        self.model = self._load_model()
        self.scaler = MinMaxScaler()
        self.threshold = 0.1  # Default threshold for anomaly detection
        self.sequence_length = 20  # Number of time steps to consider
        self.threshold_history = []
        
    def _load_model(self):
        """Load pre-trained model or create a new one"""
        if os.path.exists(self.model_path):
            logger.info(f"Loading anomaly detection model from {self.model_path}")
            return load_model(self.model_path)
        else:
            logger.info("No existing anomaly detection model found. Model will be created during training.")
            return None
    
    def _create_model(self, input_dim):
        """
        Create an LSTM autoencoder model
        
        Args:
            input_dim: Input dimension (number of features)
            
        Returns:
            Compiled Keras model
        """
        # Define model architecture
        inputs = Input(shape=(self.sequence_length, input_dim))
        
        # Encoder
        encoded = LSTM(64, activation='relu', return_sequences=False)(inputs)
        encoded = Dropout(0.2)(encoded)
        
        # Decoder
        decoded = RepeatVector(self.sequence_length)(encoded)
        decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
        decoded = Dropout(0.2)(decoded)
        decoded = TimeDistributed(Dense(input_dim))(decoded)
        
        # Create model
        model = Model(inputs=inputs, outputs=decoded)
        
        # Compile model
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        
        logger.info(f"Created LSTM autoencoder model with input dimension {input_dim}")
        model.summary(print_fn=logger.info)
        
        return model
    
    def _prepare_sequences(self, data):
        """
        Prepare sequences for LSTM model
        
        Args:
            data: DataFrame with features
            
        Returns:
            Numpy array of sequences
        """
        sequences = []
        
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data.iloc[i:i+self.sequence_length].values)
            
        return np.array(sequences)
    
    def _extract_features(self, data):
        """
        Extract features for anomaly detection
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with extracted features
        """
        features = pd.DataFrame(index=data.index)
        
        # Price features
        features['close_norm'] = data['close'] / data['close'].rolling(window=20).mean()
        features['high_low_diff'] = (data['high'] - data['low']) / data['close']
        features['open_close_diff'] = (data['close'] - data['open']) / data['open']
        
        # Volume features
        features['volume_norm'] = data['volume'] / data['volume'].rolling(window=20).mean()
        
        # Returns
        features['returns_1d'] = data['close'].pct_change(1)
        features['returns_5d'] = data['close'].pct_change(5)
        
        # Volatility
        features['volatility'] = data['close'].pct_change().rolling(window=20).std()
        
        # Fill NaN values
        features = features.fillna(0)
        
        return features
    
    def train(self, data, epochs=50, batch_size=32, validation_split=0.2):
        """
        Train the anomaly detection model
        
        Args:
            data: DataFrame with OHLCV data
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training history
        """
        try:
            logger.info("Extracting features for anomaly detection...")
            features = self._extract_features(data)
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            scaled_features_df = pd.DataFrame(scaled_features, index=features.index, columns=features.columns)
            
            # Prepare sequences
            sequences = self._prepare_sequences(scaled_features_df)
            
            if len(sequences) < 100:
                logger.error(f"Insufficient data for training: {len(sequences)} sequences")
                return None
                
            logger.info(f"Prepared {len(sequences)} sequences for training")
            
            # Create model if it doesn't exist
            if self.model is None:
                self.model = self._create_model(input_dim=features.shape[1])
            
            # Define callbacks
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
            
            model_checkpoint = ModelCheckpoint(
                self.model_path,
                monitor='val_loss',
                save_best_only=True
            )
            
            # Train model
            logger.info(f"Training anomaly detection model with {len(sequences)} sequences...")
            history = self.model.fit(
                sequences, sequences,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=[early_stopping, model_checkpoint],
                verbose=1
            )
            
            # Save scaler
            joblib.dump(self.scaler, 'models/anomaly_detector/scaler.joblib')
            
            # Calculate threshold based on reconstruction error
            logger.info("Calculating anomaly threshold...")
            reconstructions = self.model.predict(sequences)
            reconstruction_errors = np.mean(np.square(sequences - reconstructions), axis=(1, 2))
            
            # Set threshold as mean + 2*std of reconstruction errors
            self.threshold = np.mean(reconstruction_errors) + 2 * np.std(reconstruction_errors)
            
            # Save threshold
            with open('models/anomaly_detector/threshold.txt', 'w') as f:
                f.write(str(self.threshold))
                
            logger.info(f"Anomaly threshold set to {self.threshold}")
            
            # Plot reconstruction error distribution
            plt.figure(figsize=(10, 6))
            plt.hist(reconstruction_errors, bins=50)
            plt.axvline(self.threshold, color='r', linestyle='--')
            plt.title('Reconstruction Error Distribution')
            plt.xlabel('Reconstruction Error')
            plt.ylabel('Frequency')
            plt.savefig('results/anomaly_detector/reconstruction_error_distribution.png')
            
            # Plot training history
            plt.figure(figsize=(10, 6))
            plt.plot(history.history['loss'], label='Training Loss')
            plt.plot(history.history['val_loss'], label='Validation Loss')
            plt.title('Model Training History')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.legend()
            plt.savefig('results/anomaly_detector/training_history.png')
            
            # Save training results
            results = {
                'threshold': float(self.threshold),
                'training_samples': len(sequences),
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'training_date': datetime.now().isoformat()
            }
            
            # Save results to JSON
            import json
            with open('results/anomaly_detector/training_results.json', 'w') as f:
                json.dump(results, f, indent=4)
            
            logger.info("Anomaly detection model training completed")
            
            return history
            
        except Exception as e:
            logger.error(f"Error training anomaly detection model: {e}")
            return None
    
    def detect_anomalies(self, data):
        """
        Detect anomalies in market data
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with anomaly scores
        """
        try:
            if self.model is None:
                logger.error("No anomaly detection model available. Train or load a model first.")
                return None
                
            # Extract features
            features = self._extract_features(data)
            
            # Scale features
            scaled_features = self.scaler.transform(features)
            scaled_features_df = pd.DataFrame(scaled_features, index=features.index, columns=features.columns)
            
            # Prepare sequences
            sequences = self._prepare_sequences(scaled_features_df)
            
            if len(sequences) == 0:
                logger.warning("No sequences to analyze")
                return None
                
            # Get reconstructions
            reconstructions = self.model.predict(sequences)
            
            # Calculate reconstruction errors
            reconstruction_errors = np.mean(np.square(sequences - reconstructions), axis=(1, 2))
            
            # Create results DataFrame
            results = pd.DataFrame(index=data.index[self.sequence_length-1:])
            results['anomaly_score'] = reconstruction_errors
            results['is_anomaly'] = results['anomaly_score'] > self.threshold
            
            # Add anomaly score to threshold history
            if len(reconstruction_errors) > 0:
                self.threshold_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'score': float(reconstruction_errors[-1]),
                    'threshold': float(self.threshold),
                    'is_anomaly': bool(reconstruction_errors[-1] > self.threshold)
                })
                
                # Keep only the last 100 entries
                if len(self.threshold_history) > 100:
                    self.threshold_history = self.threshold_history[-100:]
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return None
    
    def get_latest_anomaly_status(self):
        """
        Get the latest anomaly status
        
        Returns:
            Dictionary with latest anomaly status
        """
        if not self.threshold_history:
            return {
                'status': 'unknown',
                'score': 0.0,
                'threshold': self.threshold,
                'timestamp': datetime.now().isoformat()
            }
            
        latest = self.threshold_history[-1]
        
        return {
            'status': 'anomaly' if latest['is_anomaly'] else 'normal',
            'score': latest['score'],
            'threshold': latest['threshold'],
            'timestamp': latest['timestamp']
        }
    
    def plot_anomalies(self, data, anomalies, symbol=None):
        """
        Plot price data with anomalies highlighted
        
        Args:
            data: DataFrame with OHLCV data
            anomalies: DataFrame with anomaly scores
            symbol: Symbol name for plot title
            
        Returns:
            Path to saved plot
        """
        try:
            plt.figure(figsize=(12, 8))
            
            # Plot price
            plt.subplot(2, 1, 1)
            plt.plot(data.index, data['close'], label='Close Price')
            
            # Highlight anomalies
            anomaly_points = data.loc[anomalies[anomalies['is_anomaly']].index]
            plt.scatter(anomaly_points.index, anomaly_points['close'], color='red', label='Anomaly')
            
            plt.title(f'Anomaly Detection for {symbol if symbol else "Price Data"}')
            plt.ylabel('Price')
            plt.legend()
            
            # Plot anomaly scores
            plt.subplot(2, 1, 2)
            plt.plot(anomalies.index, anomalies['anomaly_score'], label='Anomaly Score')
            plt.axhline(self.threshold, color='r', linestyle='--', label=f'Threshold ({self.threshold:.4f})')
            
            plt.ylabel('Anomaly Score')
            plt.xlabel('Date')
            plt.legend()
            
            plt.tight_layout()
            
            # Save plot
            filename = f'results/anomaly_detector/{symbol if symbol else "price_data"}_anomalies.png'
            plt.savefig(filename)
            plt.close()
            
            return filename
            
        except Exception as e:
            logger.error(f"Error plotting anomalies: {e}")
            return None

# Create a singleton instance
anomaly_detector = AnomalyDetector()

def get_anomaly_detector():
    """Get the singleton anomaly detector instance"""
    return anomaly_detector 