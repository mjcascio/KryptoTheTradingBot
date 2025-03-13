"""
MetaTrader API Bridge

This script creates a REST API server that acts as a bridge between KryptoBot and MetaTrader.
It should be run on the same machine as MetaTrader, and it will communicate with MetaTrader
using the MetaTrader Expert Advisor (EA) that implements the ZeroMQ socket communication.

Requirements:
- Flask
- ZeroMQ (pyzmq)
- MetaTrader with ZeroMQ EA installed

Usage:
1. Install the ZeroMQ EA in MetaTrader
2. Run this script
3. Configure KryptoBot to use the MetaTrader broker with the API URL pointing to this server
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import zmq
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# Set SSL certificate path
ssl_cert_file = os.getenv('SSL_CERT_FILE', certifi.where())
requests_ca_bundle = os.getenv('REQUESTS_CA_BUNDLE', certifi.where())
os.environ['SSL_CERT_FILE'] = ssl_cert_file
os.environ['REQUESTS_CA_BUNDLE'] = requests_ca_bundle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mt_api_bridge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ZeroMQ configuration
ZMQ_HOST = os.getenv('ZMQ_HOST', 'localhost')
ZMQ_PORT_REQ = int(os.getenv('ZMQ_PORT_REQ', '5555'))
ZMQ_PORT_SUB = int(os.getenv('ZMQ_PORT_SUB', '5556'))
ZMQ_TIMEOUT = int(os.getenv('ZMQ_TIMEOUT', '10000'))  # 10 seconds

# API key for authentication
API_KEY = os.getenv('MT_API_KEY', 'your_api_key_here')

# ZeroMQ context
context = zmq.Context()

# Request socket (REQ/REP pattern)
req_socket = context.socket(zmq.REQ)
req_socket.connect(f"tcp://{ZMQ_HOST}:{ZMQ_PORT_REQ}")
req_socket.setsockopt(zmq.RCVTIMEO, ZMQ_TIMEOUT)

# Subscription socket (PUB/SUB pattern)
sub_socket = context.socket(zmq.SUB)
sub_socket.connect(f"tcp://{ZMQ_HOST}:{ZMQ_PORT_SUB}")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
sub_socket.setsockopt(zmq.RCVTIMEO, 0)  # Non-blocking

# Authentication middleware
def require_api_key(f):
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Helper function to send command to MetaTrader
def send_command(command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Send a command to MetaTrader via ZeroMQ
    
    Args:
        command: The command to send
        params: The parameters for the command
        
    Returns:
        The response from MetaTrader
    """
    try:
        # Prepare the request
        request_data = {
            'command': command,
            'params': params or {}
        }
        
        # Send the request
        req_socket.send_string(json.dumps(request_data))
        
        # Wait for the response
        response = req_socket.recv_string()
        
        # Parse the response
        response_data = json.loads(response)
        
        return response_data
    except zmq.error.Again:
        logger.error(f"Timeout waiting for response to command: {command}")
        return {'error': 'Timeout waiting for response'}
    except Exception as e:
        logger.error(f"Error sending command {command}: {e}")
        return {'error': str(e)}

# API routes
@app.route('/connect', methods=['GET'])
@require_api_key
def connect():
    """Connect to MetaTrader"""
    account = request.args.get('account', '')
    
    response = send_command('CONNECT', {'account': account})
    
    return jsonify(response)

@app.route('/disconnect', methods=['GET'])
@require_api_key
def disconnect():
    """Disconnect from MetaTrader"""
    account = request.args.get('account', '')
    
    response = send_command('DISCONNECT', {'account': account})
    
    return jsonify(response)

@app.route('/account', methods=['GET'])
@require_api_key
def get_account():
    """Get account information"""
    account = request.args.get('account', '')
    
    response = send_command('GET_ACCOUNT', {'account': account})
    
    return jsonify(response)

@app.route('/positions', methods=['GET'])
@require_api_key
def get_positions():
    """Get current positions"""
    account = request.args.get('account', '')
    
    response = send_command('GET_POSITIONS', {'account': account})
    
    return jsonify(response)

@app.route('/orders', methods=['GET'])
@require_api_key
def get_orders():
    """Get open orders"""
    account = request.args.get('account', '')
    
    response = send_command('GET_ORDERS', {'account': account})
    
    return jsonify(response)

@app.route('/history_orders', methods=['GET'])
@require_api_key
def get_history_orders():
    """Get order history"""
    account = request.args.get('account', '')
    
    response = send_command('GET_HISTORY_ORDERS', {'account': account})
    
    return jsonify(response)

@app.route('/order', methods=['GET', 'POST', 'DELETE'])
@require_api_key
def order():
    """Manage orders"""
    if request.method == 'GET':
        # Get order by ticket
        account = request.args.get('account', '')
        ticket = request.args.get('ticket', '')
        
        response = send_command('GET_ORDER', {'account': account, 'ticket': ticket})
        
        return jsonify(response)
    elif request.method == 'POST':
        # Place new order
        data = request.json
        
        response = send_command('PLACE_ORDER', data)
        
        return jsonify(response)
    elif request.method == 'DELETE':
        # Cancel order
        data = request.json
        
        response = send_command('CANCEL_ORDER', data)
        
        return jsonify(response)

@app.route('/rates', methods=['GET'])
@require_api_key
def get_rates():
    """Get historical rates"""
    account = request.args.get('account', '')
    symbol = request.args.get('symbol', '')
    timeframe = request.args.get('timeframe', '15')
    count = request.args.get('count', '100')
    
    response = send_command('GET_RATES', {
        'account': account,
        'symbol': symbol,
        'timeframe': timeframe,
        'count': count
    })
    
    return jsonify(response)

@app.route('/tick', methods=['GET'])
@require_api_key
def get_tick():
    """Get current tick data"""
    account = request.args.get('account', '')
    symbol = request.args.get('symbol', '')
    
    response = send_command('GET_TICK', {
        'account': account,
        'symbol': symbol
    })
    
    return jsonify(response)

@app.route('/symbols', methods=['GET'])
@require_api_key
def get_symbols():
    """Get available symbols"""
    account = request.args.get('account', '')
    
    response = send_command('GET_SYMBOLS', {'account': account})
    
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Send a simple command to check if MetaTrader is responsive
        response = send_command('PING')
        
        if 'error' in response:
            return jsonify({
                'status': 'error',
                'message': response['error']
            }), 500
        
        return jsonify({
            'status': 'ok',
            'message': 'MetaTrader API bridge is running',
            'mt_connected': response.get('connected', False)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting MetaTrader API Bridge...")
    
    # Check if MetaTrader is responsive
    response = send_command('PING')
    if 'error' in response:
        logger.warning(f"MetaTrader is not responsive: {response['error']}")
        logger.warning("Make sure MetaTrader is running with the ZeroMQ EA installed")
        logger.warning("The API bridge will continue to run, but commands may fail until MetaTrader is available")
    else:
        logger.info("MetaTrader is responsive")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=6789, debug=False) 