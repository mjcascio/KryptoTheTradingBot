#!/usr/bin/env python3
"""
Test Feature Selection

This script tests the feature selection implementation with a small synthetic dataset.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Import our feature selector
from feature_selection import FeatureSelector
from ml_enhancer import MLSignalEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_synthetic_data(n_samples=1000, n_features=9, n_informative=5):
    """
    Generate synthetic data for testing
    
    Args:
        n_samples: Number of samples
        n_features: Total number of features
        n_informative: Number of informative features
        
    Returns:
        Tuple of (X, y) for training
    """
    logger.info(f"Generating synthetic data with {n_samples} samples, {n_features} features, {n_informative} informative")
    
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_informative,
        n_redundant=n_features - n_informative,
        random_state=42
    )
    
    return X, y

def test_feature_selection():
    """Test feature selection with synthetic data"""
    logger.info("Testing feature selection with synthetic data...")
    
    # Generate synthetic data
    X, y = generate_synthetic_data()
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Create ML enhancer with synthetic feature names
    ml_enhancer = MLSignalEnhancer()
    ml_enhancer.feature_columns = [f'feature_{i}' for i in range(X.shape[1])]
    
    # Create feature selector
    selector = FeatureSelector(ml_enhancer=ml_enhancer)
    
    # Train model with all features
    logger.info("Training model with all features...")
    ml_enhancer.scaler.fit(X_train)
    X_train_scaled = ml_enhancer.scaler.transform(X_train)
    ml_enhancer.model.fit(X_train_scaled, y_train)
    
    # Evaluate model with all features
    X_test_scaled = ml_enhancer.scaler.transform(X_test)
    y_pred = ml_enhancer.model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"Model accuracy with all features: {accuracy:.4f}")
    
    # Get feature importance
    feature_importance = dict(zip(ml_enhancer.feature_columns, ml_enhancer.model.feature_importances_))
    logger.info("Feature importance:")
    for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {feature}: {importance:.4f}")
    
    # Sort features by importance
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    # Select top 5 features
    selector.feature_importance = dict(sorted_features)
    selected_features = selector.select_top_n_features(n=5)
    
    # Train model with selected features
    logger.info("Training model with selected features...")
    new_enhancer = MLSignalEnhancer()
    new_enhancer.feature_columns = selected_features
    
    # Extract selected features
    feature_indices = [ml_enhancer.feature_columns.index(feature) for feature in selected_features]
    X_train_selected = X_train[:, feature_indices]
    X_test_selected = X_test[:, feature_indices]
    
    # Scale and train
    new_enhancer.scaler.fit(X_train_selected)
    X_train_selected_scaled = new_enhancer.scaler.transform(X_train_selected)
    new_enhancer.model.fit(X_train_selected_scaled, y_train)
    
    # Evaluate model with selected features
    X_test_selected_scaled = new_enhancer.scaler.transform(X_test_selected)
    y_pred_selected = new_enhancer.model.predict(X_test_selected_scaled)
    accuracy_selected = accuracy_score(y_test, y_pred_selected)
    logger.info(f"Model accuracy with selected features: {accuracy_selected:.4f}")
    
    # Compare results
    logger.info("\nClassification report with all features:")
    logger.info(classification_report(y_test, y_pred))
    
    logger.info("\nClassification report with selected features:")
    logger.info(classification_report(y_test, y_pred_selected))
    
    logger.info(f"\nAccuracy difference: {accuracy_selected - accuracy:.4f}")
    
    return accuracy_selected >= accuracy * 0.95  # Allow for a small decrease in accuracy (5%)

if __name__ == "__main__":
    success = test_feature_selection()
    
    if success:
        logger.info("Feature selection test passed! Selected features perform adequately compared to all features.")
        sys.exit(0)
    else:
        logger.error("Feature selection test failed. Selected features perform significantly worse than all features.")
        sys.exit(1) 