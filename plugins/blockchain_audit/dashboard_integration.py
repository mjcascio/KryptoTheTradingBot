"""
Blockchain Audit Plugin Dashboard Integration.

This module provides integration between the Blockchain Audit Plugin and the dashboard application.
"""

import logging
from typing import Dict, Any

# Import the plugin
from plugins.blockchain_audit.integration import initialize_blockchain_audit
from plugins.blockchain_audit.api import register_blockchain_audit_api
from plugins.blockchain_audit.routes import register_blockchain_audit_routes

# Configure logging
logger = logging.getLogger(__name__)

def integrate_blockchain_audit_with_dashboard(app) -> bool:
    """
    Integrate the blockchain audit plugin with the dashboard application.
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if integration was successful, False otherwise
    """
    try:
        # Initialize blockchain audit
        if not initialize_blockchain_audit():
            logger.error("Failed to initialize blockchain audit")
            return False
        
        # Register API endpoints
        register_blockchain_audit_api(app)
        
        # Register routes
        register_blockchain_audit_routes(app)
        
        # Add blockchain audit link to navbar
        add_blockchain_audit_to_navbar(app)
        
        logger.info("Integrated blockchain audit with dashboard")
        return True
    
    except Exception as e:
        logger.error(f"Error integrating blockchain audit with dashboard: {e}")
        return False

def add_blockchain_audit_to_navbar(app):
    """
    Add blockchain audit link to navbar.
    
    Args:
        app: Flask application instance
    """
    try:
        # Check if app has navbar items
        if not hasattr(app, 'navbar_items'):
            app.navbar_items = []
        
        # Add blockchain audit link to navbar
        app.navbar_items.append({
            'name': 'Blockchain Audit',
            'url': '/blockchain-audit',
            'icon': 'bi-link-45deg'
        })
        
        logger.info("Added blockchain audit link to navbar")
    
    except Exception as e:
        logger.error(f"Error adding blockchain audit link to navbar: {e}")

def record_dashboard_event(event_type: str, event_data: Dict[str, Any]) -> bool:
    """
    Record a dashboard event in the blockchain.
    
    Args:
        event_type (str): Event type
        event_data (Dict[str, Any]): Event data
        
    Returns:
        bool: True if event was recorded successfully, False otherwise
    """
    try:
        from plugins.blockchain_audit.integration import get_blockchain_audit_plugin
        
        # Get plugin instance
        plugin = get_blockchain_audit_plugin()
        
        if not plugin:
            logger.error("Blockchain audit plugin not initialized")
            return False
        
        # Record event
        result = plugin.execute({
            'event_type': event_type,
            'event_data': event_data
        })
        
        if result.get('success'):
            logger.debug(f"Recorded dashboard event: {event_type} (Block #{result['block_index']})")
            return True
        else:
            logger.error(f"Failed to record dashboard event: {event_type} - {result.get('error')}")
            return False
    
    except Exception as e:
        logger.error(f"Error recording dashboard event: {e}")
        return False 