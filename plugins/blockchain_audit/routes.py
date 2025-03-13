"""
Blockchain Audit Plugin Routes.

This module provides route handlers for the Blockchain Audit Plugin.
"""

import logging
from flask import Blueprint, render_template

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
blockchain_audit_routes = Blueprint('blockchain_audit_routes', __name__)

@blockchain_audit_routes.route('/blockchain-audit')
def blockchain_audit():
    """
    Render the blockchain audit dashboard.
    
    Returns:
        Rendered template
    """
    return render_template('blockchain_audit.html')

def register_blockchain_audit_routes(app):
    """
    Register blockchain audit routes with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(blockchain_audit_routes)
    logger.info("Registered blockchain audit routes") 