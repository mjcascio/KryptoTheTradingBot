"""
Blockchain Audit Plugin API.

This module provides API endpoints for the Blockchain Audit Plugin.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from flask import Blueprint, jsonify, request, Response

# Import the plugin
from plugins.blockchain_audit.blockchain_audit import BlockchainAuditPlugin
from plugins.blockchain_audit.integration import get_blockchain_audit_plugin

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
blockchain_audit_api = Blueprint('blockchain_audit_api', __name__)

@blockchain_audit_api.route('/api/blockchain/blocks', methods=['GET'])
def get_blocks():
    """
    Get blockchain blocks.
    
    Query Parameters:
        page (int): Page number (1-indexed)
        limit (int): Number of blocks per page
        event_type (str): Filter by event type
        
    Returns:
        JSON response with blocks and stats
    """
    try:
        # Get plugin instance
        plugin = get_blockchain_audit_plugin()
        
        if not plugin:
            return jsonify({
                'error': 'Blockchain audit plugin not initialized'
            }), 500
        
        # Get query parameters
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        event_type = request.args.get('event_type', default=None, type=str)
        
        # Validate parameters
        if page < 1:
            page = 1
        
        if limit < 1 or limit > 100:
            limit = 10
        
        # Get blocks
        blocks = []
        
        if event_type:
            # Get blocks by event type
            blocks = plugin.get_blocks_by_event_type(event_type)
        else:
            # Get all blocks
            for i in range(len(plugin._blockchain.chain)):
                block = plugin.get_block(i)
                if block:
                    blocks.append(block)
        
        # Calculate pagination
        total_blocks = len(blocks)
        total_pages = (total_blocks + limit - 1) // limit
        
        # Apply pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_blocks = blocks[start_index:end_index]
        
        # Get blockchain stats
        stats = plugin.get_blockchain_stats()
        
        return jsonify({
            'blocks': paginated_blocks,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_blocks': total_blocks,
                'total_pages': total_pages
            },
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting blockchain blocks: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@blockchain_audit_api.route('/api/blockchain/blocks/<int:block_index>', methods=['GET'])
def get_block(block_index):
    """
    Get a specific blockchain block.
    
    Path Parameters:
        block_index (int): Block index
        
    Returns:
        JSON response with block data
    """
    try:
        # Get plugin instance
        plugin = get_blockchain_audit_plugin()
        
        if not plugin:
            return jsonify({
                'error': 'Blockchain audit plugin not initialized'
            }), 500
        
        # Get block
        block = plugin.get_block(block_index)
        
        if not block:
            return jsonify({
                'error': f'Block with index {block_index} not found'
            }), 404
        
        return jsonify(block)
    
    except Exception as e:
        logger.error(f"Error getting blockchain block: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@blockchain_audit_api.route('/api/blockchain/events/<event_type>', methods=['GET'])
def get_events_by_type(event_type):
    """
    Get blockchain events by type.
    
    Path Parameters:
        event_type (str): Event type
        
    Query Parameters:
        page (int): Page number (1-indexed)
        limit (int): Number of events per page
        
    Returns:
        JSON response with events
    """
    try:
        # Get plugin instance
        plugin = get_blockchain_audit_plugin()
        
        if not plugin:
            return jsonify({
                'error': 'Blockchain audit plugin not initialized'
            }), 500
        
        # Get query parameters
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        
        # Validate parameters
        if page < 1:
            page = 1
        
        if limit < 1 or limit > 100:
            limit = 10
        
        # Get blocks by event type
        blocks = plugin.get_blocks_by_event_type(event_type)
        
        # Calculate pagination
        total_blocks = len(blocks)
        total_pages = (total_blocks + limit - 1) // limit
        
        # Apply pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_blocks = blocks[start_index:end_index]
        
        return jsonify({
            'events': paginated_blocks,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_events': total_blocks,
                'total_pages': total_pages
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting blockchain events: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@blockchain_audit_api.route('/api/blockchain/stats', methods=['GET'])
def get_stats():
    """
    Get blockchain statistics.
    
    Returns:
        JSON response with blockchain statistics
    """
    try:
        # Get plugin instance
        plugin = get_blockchain_audit_plugin()
        
        if not plugin:
            return jsonify({
                'error': 'Blockchain audit plugin not initialized'
            }), 500
        
        # Get blockchain stats
        stats = plugin.get_blockchain_stats()
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting blockchain stats: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@blockchain_audit_api.route('/api/blockchain/verify', methods=['GET'])
def verify_blockchain():
    """
    Verify blockchain integrity.
    
    Returns:
        JSON response with verification result
    """
    try:
        # Get plugin instance
        plugin = get_blockchain_audit_plugin()
        
        if not plugin:
            return jsonify({
                'error': 'Blockchain audit plugin not initialized'
            }), 500
        
        # Verify blockchain
        is_valid = plugin.verify_blockchain()
        
        return jsonify({
            'is_valid': is_valid
        })
    
    except Exception as e:
        logger.error(f"Error verifying blockchain: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@blockchain_audit_api.route('/api/blockchain/export', methods=['GET'])
def export_blockchain():
    """
    Export blockchain data.
    
    Returns:
        JSON file with blockchain data
    """
    try:
        # Get plugin instance
        plugin = get_blockchain_audit_plugin()
        
        if not plugin:
            return jsonify({
                'error': 'Blockchain audit plugin not initialized'
            }), 500
        
        # Get all blocks
        blocks = []
        
        for i in range(len(plugin._blockchain.chain)):
            block = plugin.get_block(i)
            if block:
                blocks.append(block)
        
        # Create response
        response = Response(
            json.dumps({
                'blocks': blocks,
                'stats': plugin.get_blockchain_stats()
            }, indent=2),
            mimetype='application/json'
        )
        
        # Set headers for file download
        response.headers['Content-Disposition'] = f'attachment; filename=blockchain_export.json'
        
        return response
    
    except Exception as e:
        logger.error(f"Error exporting blockchain: {e}")
        return jsonify({
            'error': str(e)
        }), 500

def register_blockchain_audit_api(app):
    """
    Register blockchain audit API with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(blockchain_audit_api)
    logger.info("Registered blockchain audit API endpoints") 