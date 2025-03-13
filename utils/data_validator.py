#!/usr/bin/env python3
"""
Data Validation Utility for KryptoBot Dashboard

This module provides validation functions to ensure that API responses
meet the expected schema, helping to catch data inconsistencies early.
"""

import json
import logging
from typing import Dict, List, Any, Optional as OptionalType, Union, Callable, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/data_validator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Schema definitions for dashboard data
ACCOUNT_SCHEMA = {
    'equity': float,
    'buying_power': float,
    'cash': float,
    'platform': str,
    'platform_type': str
}

POSITION_SCHEMA = {
    'quantity': float,
    'entry_price': float,
    'current_price': float,
    'market_value': float,
    'unrealized_pl': float,
    'unrealized_plpc': float,
    'platform': str
}

TRADE_SCHEMA = {
    'symbol': str,
    'side': str,
    'quantity': float,
    'entry_price': float,
    'exit_price': float,  # Can be None but we'll handle that in validation
    'entry_time': str,
    'exit_time': str  # Can be None but we'll handle that in validation
}

MARKET_STATUS_SCHEMA = {
    'is_open': bool,
    'next_open': str,  # Can be None
    'next_close': str  # Can be None
}

SLEEP_STATUS_SCHEMA = {
    'is_sleeping': bool,
    'reason': str,  # Can be None
    'next_wake_time': str  # Can be None
}

DAILY_STATS_SCHEMA = {
    'total_trades': int,  # Either total_trades or trades should be present
    'win_rate': float,
    'total_pl': float
}

MODEL_PERFORMANCE_SCHEMA = {
    'accuracy': float,
    'precision': float,
    'recall': float,
    'f1_score': float,
    'auc': float
}

ML_INSIGHTS_SCHEMA = {
    'model_performance': MODEL_PERFORMANCE_SCHEMA,
    'recent_predictions': list,
    'feature_importance': dict
}

MARKET_PREDICTIONS_SCHEMA = {
    'next_day': list,
    'prediction_date': str,
    'model_confidence': float,
    'market_sentiment': str,
    'top_picks': list
}

BOT_ACTIVITY_SCHEMA = {
    'timestamp': str,
    'message': str,
    'level': str
}

LOGS_RESPONSE_SCHEMA = {
    'bot_activity': list
}

PLATFORMS_RESPONSE_SCHEMA = {
    'platforms': list
}

PERFORMANCE_RESPONSE_SCHEMA = {
    'metrics': dict
}

# Main dashboard data schema
DASHBOARD_DATA_SCHEMA = {
    'account': ACCOUNT_SCHEMA,
    'positions': dict,
    'trades': list,
    'bot_activity': list,
    'market_status': MARKET_STATUS_SCHEMA,
    'sleep_status': SLEEP_STATUS_SCHEMA,
    'equity_history': list,
    'daily_stats': DAILY_STATS_SCHEMA,
    'ml_insights': ML_INSIGHTS_SCHEMA,
    'market_predictions': MARKET_PREDICTIONS_SCHEMA
}

def validate_type(value: Any, expected_type: Any, field_name: str) -> bool:
    """
    Validate that a value is of the expected type.
    
    Args:
        value: The value to validate
        expected_type: The expected type or list of types
        field_name: The name of the field being validated
        
    Returns:
        bool: True if the value is of the expected type, False otherwise
    """
    # Handle None values
    if value is None:
        # If None is acceptable for this field
        return True
        
    # Handle basic types
    if expected_type in (int, float, str, bool):
        return isinstance(value, expected_type)
        
    # Handle dictionaries
    if expected_type == dict:
        return isinstance(value, dict)
        
    # Handle lists
    if expected_type == list:
        return isinstance(value, list)
        
    # Default case
    try:
        return isinstance(value, expected_type)
    except TypeError:
        # If expected_type is not a valid type for isinstance
        logger.error(f"Invalid type check: {expected_type} is not a valid type")
        return False

def validate_dict(data: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> List[str]:
    """Validate a dictionary against a schema."""
    errors = []
    
    # Special case for daily_stats with either 'total_trades' or 'trades'
    if path == "daily_stats" and "total_trades" in schema:
        if "total_trades" not in data and "trades" not in data:
            errors.append(f"Required field '{path}.total_trades' or '{path}.trades' is missing")
        elif "trades" in data and not isinstance(data["trades"], int):
            errors.append(f"Field '{path}.trades' has invalid type. Expected int, got {type(data['trades']).__name__}")
    
    # Check for required fields
    for field_name, expected_type in schema.items():
        field_path = f"{path}.{field_name}" if path else field_name
        
        # Skip the total_trades check if we already handled it in the special case
        if path == "daily_stats" and field_name == "total_trades":
            continue
            
        if field_name not in data:
            # Some fields can be None or missing
            if field_name in ["exit_price", "exit_time", "next_open", "next_close", "reason", "next_wake_time"]:
                continue
            errors.append(f"Required field '{field_path}' is missing")
            continue
            
        # Validate field type
        if not validate_type(data[field_name], expected_type, field_name):
            errors.append(f"Field '{field_path}' has invalid type. Expected {expected_type.__name__}, got {type(data[field_name]).__name__}")
    
    return errors

def validate_dashboard_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the dashboard data against the schema.
    
    Args:
        data: The dashboard data to validate
        
    Returns:
        Tuple of (is_valid, errors)
    """
    errors = []
    
    try:
        # Validate top-level fields
        for field in DASHBOARD_DATA_SCHEMA:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")
                continue
                
            # Validate field based on its type
            if field == 'positions':
                # Positions validation
                if not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' has invalid type. Expected dict")
            elif field == 'trades':
                # Trades validation
                if not isinstance(data[field], list):
                    errors.append(f"Field '{field}' has invalid type. Expected list")
            elif field == 'account':
                # Account validation
                if not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' has invalid type. Expected dict")
                    
                # Check required account fields
                for account_field in ['equity', 'buying_power', 'cash', 'platform', 'platform_type']:
                    if account_field not in data[field]:
                        errors.append(f"Required account field '{account_field}' is missing")
            elif field == 'market_status':
                if not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' has invalid type. Expected dict, got {type(data[field]).__name__}")
                else:
                    # Check required fields in market_status
                    for status_field in ['is_open', 'next_open', 'next_close']:
                        if status_field not in data[field]:
                            errors.append(f"Required field '{field}.{status_field}' is missing")
            elif field == 'sleep_status':
                if not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' has invalid type. Expected dict, got {type(data[field]).__name__}")
                else:
                    # Check required fields in sleep_status
                    for status_field in ['is_sleeping', 'reason', 'next_wake_time']:
                        if status_field not in data[field]:
                            errors.append(f"Required field '{field}.{status_field}' is missing")
            elif field == 'daily_stats':
                if not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' has invalid type. Expected dict, got {type(data[field]).__name__}")
                else:
                    # Check for either total_trades or trades in daily_stats
                    if 'total_trades' not in data[field] and 'trades' not in data[field]:
                        errors.append(f"Required field '{field}.total_trades' or '{field}.trades' is missing")
                    # Check other required fields
                    for stats_field in ['win_rate', 'total_pl']:
                        if stats_field not in data[field]:
                            errors.append(f"Required field '{field}.{stats_field}' is missing")
            elif field == 'ml_insights':
                if not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' has invalid type. Expected dict, got {type(data[field]).__name__}")
                else:
                    # Check required fields in ml_insights
                    for insights_field in ['model_performance', 'recent_predictions', 'feature_importance']:
                        if insights_field not in data[field]:
                            errors.append(f"Required field '{field}.{insights_field}' is missing")
            elif field == 'market_predictions':
                if not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' has invalid type. Expected dict, got {type(data[field]).__name__}")
                else:
                    # Check required fields in market_predictions
                    for pred_field in ['next_day', 'prediction_date', 'model_confidence', 'market_sentiment', 'top_picks']:
                        if pred_field not in data[field]:
                            errors.append(f"Required field '{field}.{pred_field}' is missing")
        
        # Log validation results
        if errors:
            logger.warning(f"Dashboard data validation failed: {len(errors)} errors")
            for error in errors[:10]:  # Log first 10 errors
                logger.warning(f"  - {error}")
        else:
            logger.info("Dashboard data validation complete")
            
    except Exception as e:
        logger.error(f"Error validating dashboard data: {e}")
        errors.append(f"Validation error: {str(e)}")
    
    # Return validation result
    is_valid = len(errors) == 0
    logger.info("Dashboard data validation complete")
    return is_valid, errors

def validate_api_response(endpoint: str, data: Dict[str, Any]) -> List[str]:
    """
    Validate an API response against the appropriate schema.
    
    Args:
        endpoint: The API endpoint
        data: The response data
        
    Returns:
        List of validation errors, empty list if validation passed
    """
    errors = []
    
    try:
        # Select schema based on endpoint
        if endpoint == '/api/data':
            is_valid, validation_errors = validate_dashboard_data(data)
            if not is_valid:
                errors = validation_errors
        elif endpoint == '/api/logs':
            if 'bot_activity' not in data:
                errors.append("Missing required field 'bot_activity'")
            elif not isinstance(data['bot_activity'], list):
                errors.append("Field 'bot_activity' has invalid type. Expected list")
        elif endpoint == '/api/platforms':
            if 'platforms' not in data:
                errors.append("Missing required field 'platforms'")
            elif not isinstance(data['platforms'], list):
                errors.append("Field 'platforms' has invalid type. Expected list")
        elif endpoint == '/api/ml/predictions':
            if 'insights' not in data:
                errors.append("Missing required field 'insights'")
            elif not isinstance(data['insights'], dict):
                errors.append("Field 'insights' has invalid type. Expected dict")
                
            if 'predictions' not in data:
                errors.append("Missing required field 'predictions'")
            elif not isinstance(data['predictions'], dict):
                errors.append("Field 'predictions' has invalid type. Expected dict")
        elif endpoint == '/api/performance':
            if 'metrics' not in data:
                errors.append("Missing required field 'metrics'")
            elif not isinstance(data['metrics'], dict):
                errors.append("Field 'metrics' has invalid type. Expected dict")
        
        # Log validation results
        if errors:
            logger.warning(f"Data validation failed for {endpoint}: {len(errors)} errors")
            for error in errors[:10]:  # Log first 10 errors
                logger.warning(f"  - {error}")
        else:
            logger.info(f"Validation passed for {data}")
            
    except Exception as e:
        logger.error(f"Error validating {endpoint}: {e}")
        errors.append(f"Validation error: {str(e)}")
    
    return errors

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Validating {file_path}...")
        result = validate_api_response(file_path, DASHBOARD_DATA_SCHEMA)
        
        if result:
            print(f"✅ Validation passed for {file_path}")
        else:
            print(f"❌ Validation failed for {file_path} with {len(result)} errors:")
            for error in result:
                print(f"  - {error}")
    else:
        print("Usage: python data_validator.py <json_file>")
        print("Example: python data_validator.py data/dashboard_data.json") 