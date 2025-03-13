#!/usr/bin/env python3
"""
Ensemble Learning Module

This module implements ensemble learning techniques to combine predictions
from multiple ML models for more robust trading signals.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, AdaBoostClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.tree import DecisionTreeClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ensemble_learning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs('models/ensemble', exist_ok=True)
os.makedirs('results/ensemble', exist_ok=True)

class EnsembleLearning:
    """
    Ensemble learning class that combines predictions from multiple ML models.
    """
    
    def __init__(self):
        """Initialize the ensemble learning module"""
        self.models = {}
        self.ensemble_model = None
        self.feature_columns = []
        self.voting_weights = None
        self.scaler = None
        
    def load_base_models(self):
        """
        Load or create base models for the ensemble
        
        Returns:
            Dictionary of base models
        """
        logger.info("Loading base models for ensemble...")
        
        # Load existing ML enhancer model if available
        try:
            from ml_enhancer import MLSignalEnhancer
            ml_enhancer = MLSignalEnhancer()
            self.feature_columns = ml_enhancer.feature_columns
            
            # Add RandomForest model from ML enhancer
            if os.path.exists(ml_enhancer.model_path):
                self.models['random_forest'] = joblib.load(ml_enhancer.model_path)
                self.scaler = joblib.load('models/scaler.joblib')
                logger.info("Loaded RandomForest model from ML enhancer")
            else:
                logger.warning("ML enhancer model not found, creating new RandomForest model")
                self.models['random_forest'] = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=5,
                    random_state=42
                )
        except Exception as e:
            logger.error(f"Error loading ML enhancer model: {e}")
            logger.info("Creating new RandomForest model")
            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        
        # Create GradientBoosting model
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        # Create AdaBoost model
        self.models['adaboost'] = AdaBoostClassifier(
            base_estimator=DecisionTreeClassifier(max_depth=3),
            n_estimators=100,
            learning_rate=0.1,
            random_state=42
        )
        
        logger.info(f"Loaded {len(self.models)} base models for ensemble")
        return self.models
    
    def create_ensemble_model(self, voting='soft', weights=None):
        """
        Create an ensemble model using voting
        
        Args:
            voting: Voting type ('hard' or 'soft')
            weights: Weights for each model in the ensemble
            
        Returns:
            VotingClassifier ensemble model
        """
        logger.info(f"Creating ensemble model with {voting} voting...")
        
        # Load base models if not already loaded
        if not self.models:
            self.load_base_models()
        
        # Create list of (name, model) tuples for VotingClassifier
        estimators = [(name, model) for name, model in self.models.items()]
        
        # Set default weights if not provided
        if weights is None:
            weights = [1] * len(estimators)
        
        self.voting_weights = weights
        
        # Create voting classifier
        self.ensemble_model = VotingClassifier(
            estimators=estimators,
            voting=voting,
            weights=weights
        )
        
        logger.info(f"Created ensemble model with {len(estimators)} base models")
        return self.ensemble_model
    
    def train(self, X, y, test_size=0.2):
        """
        Train the ensemble model and its base models
        
        Args:
            X: Feature matrix
            y: Target vector
            test_size: Fraction of data to use for testing
            
        Returns:
            Dictionary with training results
        """
        try:
            logger.info("Training ensemble model...")
            
            # Create ensemble model if not already created
            if self.ensemble_model is None:
                self.create_ensemble_model()
            
            # Split data into train and test sets
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Scale features if scaler is available
            if self.scaler is not None:
                X_train = self.scaler.transform(X_train)
                X_test = self.scaler.transform(X_test)
            
            # Train each base model
            base_metrics = {}
            for name, model in self.models.items():
                logger.info(f"Training {name} model...")
                model.fit(X_train, y_train)
                
                # Evaluate model
                y_pred = model.predict(X_test)
                metrics = {
                    'accuracy': accuracy_score(y_test, y_pred),
                    'precision': precision_score(y_test, y_pred),
                    'recall': recall_score(y_test, y_pred),
                    'f1': f1_score(y_test, y_pred)
                }
                base_metrics[name] = metrics
                logger.info(f"{name} metrics: {metrics}")
                
                # Save model
                joblib.dump(model, f'models/ensemble/{name}_model.joblib')
            
            # Train ensemble model
            logger.info("Training ensemble model...")
            self.ensemble_model.fit(X_train, y_train)
            
            # Evaluate ensemble model
            y_pred_ensemble = self.ensemble_model.predict(X_test)
            ensemble_metrics = {
                'accuracy': accuracy_score(y_test, y_pred_ensemble),
                'precision': precision_score(y_test, y_pred_ensemble),
                'recall': recall_score(y_test, y_pred_ensemble),
                'f1': f1_score(y_test, y_pred_ensemble)
            }
            logger.info(f"Ensemble metrics: {ensemble_metrics}")
            
            # Save ensemble model
            joblib.dump(self.ensemble_model, 'models/ensemble/ensemble_model.joblib')
            
            # Save feature columns
            with open('models/ensemble/feature_columns.txt', 'w') as f:
                f.write('\n'.join(self.feature_columns))
            
            # Save voting weights
            np.save('models/ensemble/voting_weights.npy', self.voting_weights)
            
            # Plot model comparison
            self._plot_model_comparison(base_metrics, ensemble_metrics)
            
            # Save training results
            results = {
                'base_metrics': base_metrics,
                'ensemble_metrics': ensemble_metrics,
                'feature_columns': self.feature_columns,
                'voting_weights': self.voting_weights,
                'training_date': datetime.now().isoformat()
            }
            
            import json
            with open('results/ensemble/training_results.json', 'w') as f:
                json.dump(results, f, indent=4, default=str)
            
            logger.info("Ensemble model training completed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error training ensemble model: {e}")
            return None
    
    def predict(self, X):
        """
        Generate predictions using the ensemble model
        
        Args:
            X: Feature matrix
            
        Returns:
            Predicted classes and probabilities
        """
        try:
            # Load ensemble model if not already loaded
            if self.ensemble_model is None:
                self.load_ensemble_model()
            
            # Scale features if scaler is available
            if self.scaler is not None:
                X = self.scaler.transform(X)
            
            # Generate predictions
            y_pred = self.ensemble_model.predict(X)
            
            # Generate probabilities if using soft voting
            if hasattr(self.ensemble_model, 'predict_proba'):
                y_prob = self.ensemble_model.predict_proba(X)
                return y_pred, y_prob
            
            return y_pred, None
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return None, None
    
    def load_ensemble_model(self):
        """
        Load the trained ensemble model
        
        Returns:
            Loaded ensemble model
        """
        try:
            logger.info("Loading ensemble model...")
            
            # Load ensemble model
            model_path = 'models/ensemble/ensemble_model.joblib'
            if os.path.exists(model_path):
                self.ensemble_model = joblib.load(model_path)
                logger.info("Loaded ensemble model")
            else:
                logger.warning("Ensemble model not found")
                return None
            
            # Load feature columns
            feature_columns_path = 'models/ensemble/feature_columns.txt'
            if os.path.exists(feature_columns_path):
                with open(feature_columns_path, 'r') as f:
                    self.feature_columns = f.read().splitlines()
                logger.info(f"Loaded {len(self.feature_columns)} feature columns")
            
            # Load voting weights
            weights_path = 'models/ensemble/voting_weights.npy'
            if os.path.exists(weights_path):
                self.voting_weights = np.load(weights_path)
                logger.info(f"Loaded voting weights: {self.voting_weights}")
            
            # Load scaler
            scaler_path = 'models/scaler.joblib'
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded scaler")
            
            return self.ensemble_model
            
        except Exception as e:
            logger.error(f"Error loading ensemble model: {e}")
            return None
    
    def _plot_model_comparison(self, base_metrics, ensemble_metrics):
        """
        Plot comparison of base models and ensemble model
        
        Args:
            base_metrics: Dictionary of base model metrics
            ensemble_metrics: Dictionary of ensemble model metrics
        """
        try:
            # Create DataFrame for plotting
            metrics = ['accuracy', 'precision', 'recall', 'f1']
            models = list(base_metrics.keys()) + ['ensemble']
            
            data = []
            for metric in metrics:
                for model in base_metrics:
                    data.append({
                        'Model': model,
                        'Metric': metric,
                        'Value': base_metrics[model][metric]
                    })
                data.append({
                    'Model': 'ensemble',
                    'Metric': metric,
                    'Value': ensemble_metrics[metric]
                })
            
            df = pd.DataFrame(data)
            
            # Plot comparison
            plt.figure(figsize=(12, 8))
            sns.barplot(x='Metric', y='Value', hue='Model', data=df)
            plt.title('Model Comparison')
            plt.ylim(0, 1)
            plt.tight_layout()
            plt.savefig('results/ensemble/model_comparison.png')
            
            # Plot metrics by model
            plt.figure(figsize=(12, 8))
            for i, metric in enumerate(metrics):
                plt.subplot(2, 2, i+1)
                metric_df = df[df['Metric'] == metric]
                sns.barplot(x='Model', y='Value', data=metric_df)
                plt.title(f'{metric.capitalize()} by Model')
                plt.ylim(0, 1)
            
            plt.tight_layout()
            plt.savefig('results/ensemble/metrics_by_model.png')
            
        except Exception as e:
            logger.error(f"Error plotting model comparison: {e}")

def main():
    """Main function"""
    logger.info("Starting ensemble learning...")
    
    try:
        # Import training data generator
        from train_ml_model import generate_training_data
        
        # Generate training data
        X, y = generate_training_data()
        
        if len(X) == 0:
            logger.error("No training data available")
            return
        
        # Create and train ensemble model
        ensemble = EnsembleLearning()
        ensemble.load_base_models()
        ensemble.create_ensemble_model(voting='soft')
        results = ensemble.train(X, y)
        
        if results:
            logger.info("Ensemble learning completed successfully")
        else:
            logger.error("Ensemble learning failed")
            
    except Exception as e:
        logger.error(f"Error in ensemble learning: {e}")

if __name__ == "__main__":
    main() 