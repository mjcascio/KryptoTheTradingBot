#!/usr/bin/env python3
"""
ML Integration Module

This module integrates the ML models with the trading bot.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import json

# Import our ML modules
from ml_enhancer import MLSignalEnhancer
from anomaly_detector import get_anomaly_detector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ml_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MLIntegration:
    """
    ML Integration class that connects ML models with the trading bot.
    """
    
    def __init__(self):
        """Initialize the ML integration"""
        # Initialize ML enhancer
        self.ml_enhancer = MLSignalEnhancer()
        
        # Initialize anomaly detector
        self.anomaly_detector = get_anomaly_detector()
        
        # ML settings
        self.ml_enabled = True
        self.anomaly_detection_enabled = True
        self.min_confidence_threshold = 0.6
        self.position_size_multiplier = 1.0
        
        # Load settings if available
        self._load_settings()
        
        logger.info("ML Integration initialized")
    
    def _load_settings(self):
        """Load ML settings from file"""
        settings_file = 'config/ml_settings.json'
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                self.ml_enabled = settings.get('ml_enabled', True)
                self.anomaly_detection_enabled = settings.get('anomaly_detection_enabled', True)
                self.min_confidence_threshold = settings.get('min_confidence_threshold', 0.6)
                self.position_size_multiplier = settings.get('position_size_multiplier', 1.0)
                
                logger.info(f"Loaded ML settings: {settings}")
            except Exception as e:
                logger.error(f"Error loading ML settings: {e}")
    
    def save_settings(self):
        """Save ML settings to file"""
        settings_file = 'config/ml_settings.json'
        
        # Create directory if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        settings = {
            'ml_enabled': self.ml_enabled,
            'anomaly_detection_enabled': self.anomaly_detection_enabled,
            'min_confidence_threshold': self.min_confidence_threshold,
            'position_size_multiplier': self.position_size_multiplier,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            logger.info(f"Saved ML settings: {settings}")
        except Exception as e:
            logger.error(f"Error saving ML settings: {e}")
    
    def enhance_signal(self, data, base_signal):
        """
        Enhance a trading signal using ML
        
        Args:
            data: DataFrame with OHLCV data
            base_signal: Dictionary with base signal parameters
            
        Returns:
            Dictionary with enhanced signal parameters
        """
        if not self.ml_enabled:
            logger.info("ML enhancement disabled")
            return base_signal
        
        try:
            # Enhance signal with ML
            enhanced_signal = self.ml_enhancer.enhance_signal(data, base_signal)
            
            # Check if confidence meets threshold
            if enhanced_signal.get('confidence', 0) < self.min_confidence_threshold:
                logger.info(f"Signal confidence {enhanced_signal.get('confidence', 0):.2f} below threshold {self.min_confidence_threshold}")
                return None
            
            # Adjust position size based on confidence
            confidence = enhanced_signal.get('confidence', 0)
            position_size_modifier = enhanced_signal.get('position_size_modifier', 1.0)
            
            # Scale position size based on confidence and settings
            adjusted_position_size = position_size_modifier * (0.5 + 0.5 * confidence) * self.position_size_multiplier
            enhanced_signal['position_size_modifier'] = adjusted_position_size
            
            logger.info(f"Enhanced signal: confidence={confidence:.2f}, position_size_modifier={adjusted_position_size:.2f}")
            
            return enhanced_signal
        except Exception as e:
            logger.error(f"Error enhancing signal: {e}")
            return base_signal
    
    def check_for_anomalies(self, data, symbol=None):
        """
        Check for anomalies in market data
        
        Args:
            data: DataFrame with OHLCV data
            symbol: Symbol name for logging
            
        Returns:
            Dictionary with anomaly information
        """
        if not self.anomaly_detection_enabled:
            logger.info("Anomaly detection disabled")
            return {'is_anomaly': False, 'score': 0.0}
        
        try:
            # Detect anomalies
            anomalies = self.anomaly_detector.detect_anomalies(data)
            
            if anomalies is None or len(anomalies) == 0:
                logger.warning("No anomaly data available")
                return {'is_anomaly': False, 'score': 0.0}
            
            # Get the latest anomaly score
            latest_score = anomalies['anomaly_score'].iloc[-1]
            is_anomaly = anomalies['is_anomaly'].iloc[-1]
            
            # Log anomaly information
            if is_anomaly:
                logger.info(f"Anomaly detected for {symbol}: score={latest_score:.4f}")
                
                # Plot anomalies if a symbol is provided
                if symbol:
                    self.anomaly_detector.plot_anomalies(data, anomalies, symbol=symbol)
            
            return {
                'is_anomaly': bool(is_anomaly),
                'score': float(latest_score),
                'threshold': float(self.anomaly_detector.threshold),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking for anomalies: {e}")
            return {'is_anomaly': False, 'score': 0.0}
    
    def get_ml_status(self):
        """
        Get the current status of ML components
        
        Returns:
            Dictionary with ML status information
        """
        # Check if ML models are available
        ml_enhancer_available = os.path.exists(self.ml_enhancer.model_path)
        anomaly_detector_available = self.anomaly_detector.model is not None
        
        # Get anomaly status
        anomaly_status = self.anomaly_detector.get_latest_anomaly_status()
        
        return {
            'ml_enabled': self.ml_enabled,
            'anomaly_detection_enabled': self.anomaly_detection_enabled,
            'ml_enhancer_available': ml_enhancer_available,
            'anomaly_detector_available': anomaly_detector_available,
            'min_confidence_threshold': self.min_confidence_threshold,
            'position_size_multiplier': self.position_size_multiplier,
            'anomaly_status': anomaly_status,
            'timestamp': datetime.now().isoformat()
        }
    
    def connect_to_bot(self, bot):
        """
        Connect ML integration to the trading bot
        
        Args:
            bot: Trading bot instance
        """
        # Connect ML enhancer to bot
        self.ml_enhancer.connect_to_bot(bot)
        
        logger.info("ML integration connected to trading bot")

# Create a singleton instance
ml_integration = MLIntegration()

def get_ml_integration():
    """Get the singleton ML integration instance"""
    return ml_integration 