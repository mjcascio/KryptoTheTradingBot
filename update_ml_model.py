#!/usr/bin/env python3
"""
Update ML Model

This script runs the feature selection process and updates the ML model.
It can be used as a standalone script or imported by other scripts.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_ml_model.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_ml_model(method='auto', threshold=0.05, top_n=5):
    """
    Update the ML model using feature selection
    
    Args:
        method: Feature selection method ('auto', 'threshold', 'top_n', 'rfecv')
        threshold: Importance threshold for 'threshold' method
        top_n: Number of features to select for 'top_n' method
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import feature selector
        from feature_selection import FeatureSelector
        
        # Create feature selector
        selector = FeatureSelector()
        
        # Load training data
        X, y = selector.load_training_data()
        
        if len(X) == 0:
            logger.error("No training data available")
            return False
        
        # Analyze feature importance
        selector.analyze_feature_importance(X, y)
        
        # Select features based on method
        if method == 'threshold':
            logger.info(f"Using importance threshold method with threshold={threshold}")
            selector.select_features_by_importance(threshold=threshold)
            new_enhancer = selector.train_with_selected_features(X, y)
            comparison = selector.compare_models(X, y, selector.ml_enhancer, new_enhancer)
            selector.update_ml_enhancer(new_enhancer)
            
        elif method == 'top_n':
            logger.info(f"Using top N method with n={top_n}")
            selector.select_top_n_features(n=top_n)
            new_enhancer = selector.train_with_selected_features(X, y)
            comparison = selector.compare_models(X, y, selector.ml_enhancer, new_enhancer)
            selector.update_ml_enhancer(new_enhancer)
            
        elif method == 'rfecv':
            logger.info("Using RFECV method")
            selector.select_features_by_rfecv(X, y)
            new_enhancer = selector.train_with_selected_features(X, y)
            comparison = selector.compare_models(X, y, selector.ml_enhancer, new_enhancer)
            selector.update_ml_enhancer(new_enhancer)
            
        else:  # auto - try all methods and select the best
            logger.info("Using auto method - trying all feature selection methods")
            
            # Method 1: Importance threshold
            selector.select_features_by_importance(threshold=threshold)
            new_enhancer_threshold = selector.train_with_selected_features(X, y)
            comparison_threshold = selector.compare_models(X, y, selector.ml_enhancer, new_enhancer_threshold)
            
            # Method 2: Top N features
            selector.select_top_n_features(n=top_n)
            new_enhancer_top_n = selector.train_with_selected_features(X, y)
            comparison_top_n = selector.compare_models(X, y, selector.ml_enhancer, new_enhancer_top_n)
            
            # Method 3: RFECV
            selector.select_features_by_rfecv(X, y)
            new_enhancer_rfecv = selector.train_with_selected_features(X, y)
            comparison_rfecv = selector.compare_models(X, y, selector.ml_enhancer, new_enhancer_rfecv)
            
            # Select the best method based on F1 score improvement
            methods = {
                'importance_threshold': (comparison_threshold, new_enhancer_threshold),
                'top_5': (comparison_top_n, new_enhancer_top_n),
                'rfecv': (comparison_rfecv, new_enhancer_rfecv)
            }
            
            best_method = max(methods.keys(), 
                             key=lambda m: methods[m][0]['improvement']['f1'])
            
            logger.info(f"Best feature selection method: {best_method}")
            
            # Update ML enhancer with best model
            best_comparison, best_enhancer = methods[best_method]
            
            if best_method == 'importance_threshold':
                selector.selection_method = 'importance_threshold'
                selector.selected_features = selector.select_features_by_importance(threshold=threshold)
            elif best_method == 'top_5':
                selector.selection_method = 'top_5'
                selector.selected_features = selector.select_top_n_features(n=top_n)
            else:  # rfecv
                selector.selection_method = 'rfecv'
                selector.selected_features = selector.select_features_by_rfecv(X, y)
                
            selector.update_ml_enhancer(best_enhancer)
            comparison = best_comparison
        
        # Log results
        logger.info(f"ML model updated with {len(selector.selected_features)} selected features")
        logger.info(f"Selected features: {selector.selected_features}")
        logger.info(f"Improvement: {comparison['improvement']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating ML model: {e}")
        return False

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update ML model using feature selection')
    parser.add_argument('--method', type=str, default='auto', choices=['auto', 'threshold', 'top_n', 'rfecv'],
                       help='Feature selection method')
    parser.add_argument('--threshold', type=float, default=0.05,
                       help='Importance threshold for threshold method')
    parser.add_argument('--top-n', type=int, default=5,
                       help='Number of features to select for top_n method')
    args = parser.parse_args()
    
    logger.info("Starting ML model update...")
    
    success = update_ml_model(
        method=args.method,
        threshold=args.threshold,
        top_n=args.top_n
    )
    
    if success:
        logger.info("ML model update completed successfully")
        return 0
    else:
        logger.error("ML model update failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 