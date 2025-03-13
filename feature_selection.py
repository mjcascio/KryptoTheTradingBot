#!/usr/bin/env python3
"""
Feature Selection Module

This module implements feature selection techniques to identify and select
the most predictive features for the ML model.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_selection import SelectFromModel, RFECV
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Import our ML modules
from ml_enhancer import MLSignalEnhancer
from train_ml_model import generate_training_data, train_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("feature_selection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs('models', exist_ok=True)
os.makedirs('results/feature_selection', exist_ok=True)

class FeatureSelector:
    """
    Feature selector class that implements various feature selection techniques.
    """
    
    def __init__(self, ml_enhancer=None):
        """
        Initialize the feature selector
        
        Args:
            ml_enhancer: MLSignalEnhancer instance (optional)
        """
        self.ml_enhancer = ml_enhancer or MLSignalEnhancer()
        self.original_features = self.ml_enhancer.feature_columns.copy()
        self.selected_features = []
        self.feature_importance = {}
        self.selection_method = None
        self.threshold = 0.05  # Default importance threshold
        
    def load_training_data(self):
        """
        Load or generate training data
        
        Returns:
            Tuple of (X, y) for training
        """
        logger.info("Loading training data...")
        
        # Check if we have cached training data
        if os.path.exists('models/training_data.npz'):
            logger.info("Loading cached training data...")
            data = np.load('models/training_data.npz')
            X = data['X']
            y = data['y']
            logger.info(f"Loaded {len(X)} training samples with {sum(y)} positive outcomes")
            return X, y
        
        # Generate new training data
        logger.info("Generating new training data...")
        X, y = generate_training_data()
        
        # Cache the training data
        np.savez('models/training_data.npz', X=X, y=y)
        
        return X, y
    
    def analyze_feature_importance(self, X, y):
        """
        Analyze feature importance from the trained model
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            Dictionary with feature importance
        """
        logger.info("Analyzing feature importance...")
        
        # Train model if not already trained
        if not os.path.exists(self.ml_enhancer.model_path):
            logger.info("Training model to analyze feature importance...")
            self.ml_enhancer = train_model(X, y)
        else:
            logger.info("Loading existing model...")
            self.ml_enhancer.model = joblib.load(self.ml_enhancer.model_path)
        
        # Get feature importance
        feature_importance = dict(zip(self.original_features, 
                                     self.ml_enhancer.model.feature_importances_))
        
        # Sort by importance
        feature_importance = {k: v for k, v in sorted(feature_importance.items(), 
                                                     key=lambda item: item[1], 
                                                     reverse=True)}
        
        self.feature_importance = feature_importance
        
        # Log feature importance
        for feature, importance in feature_importance.items():
            logger.info(f"Feature importance: {feature}: {importance:.4f}")
        
        # Plot feature importance
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(feature_importance.values()), y=list(feature_importance.keys()))
        plt.title('Feature Importance')
        plt.tight_layout()
        plt.savefig('results/feature_selection/feature_importance.png')
        
        return feature_importance
    
    def select_features_by_importance(self, threshold=0.05):
        """
        Select features based on importance threshold
        
        Args:
            threshold: Importance threshold (default: 0.05)
            
        Returns:
            List of selected features
        """
        logger.info(f"Selecting features with importance >= {threshold}...")
        
        self.threshold = threshold
        self.selection_method = "importance_threshold"
        
        # Select features with importance >= threshold
        selected_features = [feature for feature, importance in self.feature_importance.items() 
                            if importance >= threshold]
        
        logger.info(f"Selected {len(selected_features)} features: {selected_features}")
        self.selected_features = selected_features
        
        return selected_features
    
    def select_features_by_rfecv(self, X, y, cv=5):
        """
        Select features using Recursive Feature Elimination with Cross-Validation
        
        Args:
            X: Feature matrix
            y: Target vector
            cv: Number of cross-validation folds
            
        Returns:
            List of selected features
        """
        logger.info(f"Selecting features using RFECV with {cv} folds...")
        
        self.selection_method = "rfecv"
        
        # Scale features
        X_scaled = self.ml_enhancer.scaler.fit_transform(X)
        
        # Create RFECV selector
        selector = RFECV(
            estimator=self.ml_enhancer.model,
            step=1,
            cv=StratifiedKFold(cv),
            scoring='accuracy',
            min_features_to_select=1,
            n_jobs=-1
        )
        
        # Fit selector
        selector.fit(X_scaled, y)
        
        # Get selected features
        selected_features = [feature for feature, selected in zip(self.original_features, selector.support_) 
                            if selected]
        
        logger.info(f"Selected {len(selected_features)} features: {selected_features}")
        self.selected_features = selected_features
        
        # Plot number of features vs. cross-validation scores
        plt.figure(figsize=(10, 6))
        plt.xlabel("Number of features selected")
        plt.ylabel("Cross validation score (accuracy)")
        plt.plot(range(1, len(selector.grid_scores_) + 1), selector.grid_scores_)
        plt.title('RFECV Feature Selection')
        plt.tight_layout()
        plt.savefig('results/feature_selection/rfecv_scores.png')
        
        return selected_features
    
    def select_top_n_features(self, n=5):
        """
        Select top N features by importance
        
        Args:
            n: Number of features to select
            
        Returns:
            List of selected features
        """
        logger.info(f"Selecting top {n} features...")
        
        self.selection_method = f"top_{n}"
        
        # Select top N features
        selected_features = list(self.feature_importance.keys())[:n]
        
        logger.info(f"Selected {len(selected_features)} features: {selected_features}")
        self.selected_features = selected_features
        
        return selected_features
    
    def train_with_selected_features(self, X, y):
        """
        Train model with only selected features
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            Trained MLSignalEnhancer
        """
        logger.info(f"Training model with {len(self.selected_features)} selected features...")
        
        # Create new ML enhancer with selected features
        new_enhancer = MLSignalEnhancer(model_path=f'models/signal_model_{self.selection_method}.joblib')
        new_enhancer.feature_columns = self.selected_features
        
        # Extract selected features
        feature_indices = [self.original_features.index(feature) for feature in self.selected_features]
        X_selected = X[:, feature_indices]
        
        # Scale features
        X_scaled = new_enhancer.scaler.fit_transform(X_selected)
        
        # Train model
        logger.info("Training model with selected features...")
        new_enhancer.model.fit(X_scaled, y)
        
        # Save model
        joblib.dump(new_enhancer.model, new_enhancer.model_path)
        
        # Save scaler
        joblib.dump(new_enhancer.scaler, f'models/scaler_{self.selection_method}.joblib')
        
        logger.info(f"Model trained and saved to {new_enhancer.model_path}")
        
        # Calculate and log model accuracy
        accuracy = new_enhancer.model.score(X_scaled, y)
        logger.info(f"Model accuracy with selected features: {accuracy:.4f}")
        
        # Save selected features
        with open(f'models/selected_features_{self.selection_method}.txt', 'w') as f:
            f.write('\n'.join(self.selected_features))
        
        return new_enhancer
    
    def compare_models(self, X, y, original_enhancer, new_enhancer):
        """
        Compare performance of original and new models
        
        Args:
            X: Feature matrix
            y: Target vector
            original_enhancer: Original MLSignalEnhancer
            new_enhancer: New MLSignalEnhancer with selected features
            
        Returns:
            Dictionary with comparison results
        """
        logger.info("Comparing model performance...")
        
        # Extract selected features
        feature_indices = [self.original_features.index(feature) for feature in self.selected_features]
        X_selected = X[:, feature_indices]
        
        # Scale features
        X_scaled_original = original_enhancer.scaler.transform(X)
        X_scaled_new = new_enhancer.scaler.transform(X_selected)
        
        # Get predictions
        y_pred_original = original_enhancer.model.predict(X_scaled_original)
        y_pred_new = new_enhancer.model.predict(X_scaled_new)
        
        # Calculate metrics
        metrics_original = {
            'accuracy': accuracy_score(y, y_pred_original),
            'precision': precision_score(y, y_pred_original),
            'recall': recall_score(y, y_pred_original),
            'f1': f1_score(y, y_pred_original)
        }
        
        metrics_new = {
            'accuracy': accuracy_score(y, y_pred_new),
            'precision': precision_score(y, y_pred_new),
            'recall': recall_score(y, y_pred_new),
            'f1': f1_score(y, y_pred_new)
        }
        
        # Log metrics
        logger.info(f"Original model metrics: {metrics_original}")
        logger.info(f"New model metrics: {metrics_new}")
        
        # Calculate improvement
        improvement = {
            'accuracy': metrics_new['accuracy'] - metrics_original['accuracy'],
            'precision': metrics_new['precision'] - metrics_original['precision'],
            'recall': metrics_new['recall'] - metrics_original['recall'],
            'f1': metrics_new['f1'] - metrics_original['f1']
        }
        
        logger.info(f"Improvement: {improvement}")
        
        # Plot comparison
        metrics = ['accuracy', 'precision', 'recall', 'f1']
        original_values = [metrics_original[m] for m in metrics]
        new_values = [metrics_new[m] for m in metrics]
        
        plt.figure(figsize=(10, 6))
        x = np.arange(len(metrics))
        width = 0.35
        
        plt.bar(x - width/2, original_values, width, label='Original Model')
        plt.bar(x + width/2, new_values, width, label='Model with Selected Features')
        
        plt.xlabel('Metrics')
        plt.ylabel('Score')
        plt.title('Model Performance Comparison')
        plt.xticks(x, metrics)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'results/feature_selection/model_comparison_{self.selection_method}.png')
        
        # Save comparison results
        results = {
            'original_model': {
                'features': self.original_features,
                'metrics': metrics_original
            },
            'new_model': {
                'features': self.selected_features,
                'metrics': metrics_new,
                'selection_method': self.selection_method
            },
            'improvement': improvement,
            'timestamp': datetime.now().isoformat()
        }
        
        import json
        with open(f'results/feature_selection/comparison_{self.selection_method}.json', 'w') as f:
            json.dump(results, f, indent=4)
        
        return results
    
    def update_ml_enhancer(self, new_enhancer):
        """
        Update the ML enhancer with selected features
        
        Args:
            new_enhancer: New MLSignalEnhancer with selected features
            
        Returns:
            Updated MLSignalEnhancer
        """
        logger.info("Updating ML enhancer with selected features...")
        
        # Copy model and scaler to main model files
        joblib.dump(new_enhancer.model, 'models/signal_model.joblib')
        joblib.dump(new_enhancer.scaler, 'models/scaler.joblib')
        
        # Update feature columns in ml_enhancer.py
        self._update_feature_columns_in_code()
        
        logger.info("ML enhancer updated with selected features")
        
        return MLSignalEnhancer()
    
    def _update_feature_columns_in_code(self):
        """Update feature columns in ml_enhancer.py"""
        try:
            # Read ml_enhancer.py
            with open('ml_enhancer.py', 'r') as f:
                lines = f.readlines()
            
            # Find feature_columns definition
            for i, line in enumerate(lines):
                if 'self.feature_columns = [' in line:
                    # Replace feature columns
                    feature_str = "        self.feature_columns = [\n"
                    for feature in self.selected_features:
                        feature_str += f"            '{feature}',\n"
                    feature_str += "        ]\n"
                    
                    # Replace lines
                    end_idx = i + 1
                    while ']' not in lines[end_idx]:
                        end_idx += 1
                    
                    lines[i:end_idx+1] = [feature_str]
                    break
            
            # Write updated file
            with open('ml_enhancer.py', 'w') as f:
                f.writelines(lines)
                
            logger.info("Updated feature columns in ml_enhancer.py")
            
        except Exception as e:
            logger.error(f"Error updating feature columns in code: {e}")

def main():
    """Main function"""
    logger.info("Starting feature selection...")
    
    # Create feature selector
    selector = FeatureSelector()
    
    # Load training data
    X, y = selector.load_training_data()
    
    if len(X) == 0:
        logger.error("No training data available")
        return
    
    # Analyze feature importance
    selector.analyze_feature_importance(X, y)
    
    # Select features using different methods
    
    # Method 1: Importance threshold
    selector.select_features_by_importance(threshold=0.05)
    new_enhancer_threshold = selector.train_with_selected_features(X, y)
    selector.compare_models(X, y, selector.ml_enhancer, new_enhancer_threshold)
    
    # Method 2: Top N features
    selector.select_top_n_features(n=5)
    new_enhancer_top_n = selector.train_with_selected_features(X, y)
    selector.compare_models(X, y, selector.ml_enhancer, new_enhancer_top_n)
    
    # Method 3: RFECV
    selector.select_features_by_rfecv(X, y)
    new_enhancer_rfecv = selector.train_with_selected_features(X, y)
    comparison = selector.compare_models(X, y, selector.ml_enhancer, new_enhancer_rfecv)
    
    # Select the best model based on F1 score improvement
    best_method = max(['importance_threshold', 'top_5', 'rfecv'], 
                     key=lambda m: selector.compare_models(X, y, selector.ml_enhancer, 
                                                         {'importance_threshold': new_enhancer_threshold, 
                                                          'top_5': new_enhancer_top_n, 
                                                          'rfecv': new_enhancer_rfecv}[m])['improvement']['f1'])
    
    logger.info(f"Best feature selection method: {best_method}")
    
    # Update ML enhancer with best model
    if best_method == 'importance_threshold':
        selector.selection_method = 'importance_threshold'
        selector.selected_features = selector.select_features_by_importance(threshold=0.05)
        selector.update_ml_enhancer(new_enhancer_threshold)
    elif best_method == 'top_5':
        selector.selection_method = 'top_5'
        selector.selected_features = selector.select_top_n_features(n=5)
        selector.update_ml_enhancer(new_enhancer_top_n)
    else:  # rfecv
        selector.selection_method = 'rfecv'
        selector.selected_features = selector.select_features_by_rfecv(X, y)
        selector.update_ml_enhancer(new_enhancer_rfecv)
    
    logger.info("Feature selection completed")

if __name__ == "__main__":
    main() 