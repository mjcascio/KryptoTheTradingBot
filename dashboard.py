#!/usr/bin/env python3
"""
KryptoBot Trading Dashboard - Alpaca Integration
"""

import os
import sys
import json
import logging
import threading
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit

# Add utils directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))

# Import validation utilities if available
try:
    from utils.data_validator import validate_api_response, validate_dashboard_data
    VALIDATION_ENABLED = True
except ImportError:
    VALIDATION_ENABLED = False
    print("Warning: Data validation utilities not found. Data validation is disabled.")

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
DASHBOARD_DATA = {
    'account': {
        'equity': 100000.00,
        'buying_power': 100000.00,
        'cash': 100000.00,
        'platform': 'Alpaca',
        'platform_type': 'stocks'
    },
    'positions': {},
    'trades': [],
    'bot_activity': [],
    'market_status': {
        'is_open': False,
        'next_open': None,
        'next_close': None
    },
    'sleep_status': {
        'is_sleeping': False,
        'reason': None,
        'next_wake_time': None
    },
    'equity_history': [],
    'daily_stats': {
        'total_trades': 0,
        'win_rate': 0.0,
        'total_pl': 0.0
    },
    'ml_insights': {
        'model_performance': {
            'accuracy': 0.75,
            'precision': 0.78,
            'recall': 0.72,
            'f1_score': 0.75,
            'auc': 0.82
        },
        'recent_predictions': [],
        'feature_importance': {
            'price_momentum': 0.25,
            'volume': 0.18,
            'volatility': 0.15,
            'rsi': 0.12,
            'macd': 0.10,
            'moving_averages': 0.08,
            'sentiment': 0.07,
            'sector_performance': 0.05
        }
    },
    'market_predictions': {
        'next_day': [],
        'prediction_date': datetime.now().strftime('%Y-%m-%d'),
        'model_confidence': 0.78,
        'market_sentiment': 'bullish',
        'top_picks': []
    }
}

# Performance metrics
PERFORMANCE_METRICS = {
    'start_time': datetime.now().isoformat(),
    'api_calls': {
        'total': 0,
        'success': 0,
        'error': 0,
        'by_endpoint': {}
    },
    'response_times': {
        'avg': 0,
        'max': 0,
        'min': float('inf'),
        'by_endpoint': {}
    },
    'validation': {
        'total': 0,
        'success': 0,
        'error': 0,
        'by_endpoint': {}
    },
    'errors': [],
    'request_times': [],
    'total_requests': 0,
    'avg_request_time': 0
}

# Initialize Flask app
app = Flask(__name__, 
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'templates')
)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Performance tracking
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request_performance(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        PERFORMANCE_METRICS['request_times'].append(elapsed)
        PERFORMANCE_METRICS['total_requests'] += 1
        
        # Keep only the last 1000 request times
        if len(PERFORMANCE_METRICS['request_times']) > 1000:
            PERFORMANCE_METRICS['request_times'] = PERFORMANCE_METRICS['request_times'][-1000:]
        
        # Update average request time
        PERFORMANCE_METRICS['avg_request_time'] = sum(PERFORMANCE_METRICS['request_times']) / len(PERFORMANCE_METRICS['request_times'])
        
        # Track API calls
        if request.endpoint:
            endpoint = request.endpoint
            PERFORMANCE_METRICS['api_calls'][endpoint] = PERFORMANCE_METRICS['api_calls'].get(endpoint, 0) + 1
    
    return response

# Routes
@app.route('/')
def index():
    """Render dashboard homepage."""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/logs')
def logs():
    """Render logs page."""
    try:
        return render_template('logs.html')
    except Exception as e:
        logger.error(f"Error rendering logs page: {e}")
        return f"Error loading logs page: {str(e)}", 500

@app.route('/accounts')
def accounts():
    """Render accounts page."""
    try:
        return render_template('accounts.html')
    except Exception as e:
        logger.error(f"Error rendering accounts page: {e}")
        return f"Error loading accounts page: {str(e)}", 500

@app.route('/api/data')
def get_data():
    """API endpoint for dashboard data."""
    try:
        # Validate data if validation is enabled
        if VALIDATION_ENABLED:
            validation_result = validate_dashboard_data(DASHBOARD_DATA)
            
            # Update validation metrics
            PERFORMANCE_METRICS['validation']['total'] += 1
            endpoint = request.path
            if endpoint not in PERFORMANCE_METRICS['validation']['by_endpoint']:
                PERFORMANCE_METRICS['validation']['by_endpoint'][endpoint] = {
                    'total': 0,
                    'success': 0,
                    'error': 0
                }
            
            PERFORMANCE_METRICS['validation']['by_endpoint'][endpoint]['total'] += 1
            
            if validation_result:
                # Validation failed
                PERFORMANCE_METRICS['validation']['error'] += 1
                PERFORMANCE_METRICS['validation']['by_endpoint'][endpoint]['error'] += 1
                logger.warning(f"Data validation failed for /api/data: {len(validation_result)} errors")
                for error in validation_result[:10]:  # Log first 10 errors
                    logger.warning(f"  - {error}")
            else:
                # Validation passed
                PERFORMANCE_METRICS['validation']['success'] += 1
                PERFORMANCE_METRICS['validation']['by_endpoint'][endpoint]['success'] += 1
        
        return jsonify(DASHBOARD_DATA)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """API endpoint for bot activity logs."""
    try:
        return jsonify({
            'bot_activity': DASHBOARD_DATA['bot_activity']
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/platforms')
def get_platforms():
    """Get available trading platforms"""
    try:
        # Only return Alpaca as the available platform
        platforms = [
            {
                'id': 'alpaca',
                'name': 'Alpaca',
                'type': 'stocks',
                'description': 'Alpaca Markets for stocks and crypto trading',
                'enabled': True,
                'connected': True
            }
        ]
        
        return jsonify({
            'platforms': platforms,
            'active_platform': 'Alpaca'
        })
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts')
def get_accounts():
    """Get trading accounts"""
    try:
        # Only return Alpaca account
        accounts = {
            'alpaca': {
                'id': 'alpaca_main',
                'name': 'Alpaca Trading',
                'type': 'stocks',
                'platform': 'Alpaca',
                'equity': DASHBOARD_DATA['account']['equity'],
                'buying_power': DASHBOARD_DATA['account']['buying_power'],
                'cash': DASHBOARD_DATA['account']['cash'],
                'connected': True
            }
        }
        
        return jsonify({
            'accounts': accounts,
            'active_account': 'alpaca_main'
        })
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/predictions')
def get_ml_predictions():
    """API endpoint for ML predictions."""
    try:
        return jsonify({
            'predictions': DASHBOARD_DATA['market_predictions'],
            'insights': DASHBOARD_DATA['ml_insights']
        })
    except Exception as e:
        logger.error(f"Error getting ML predictions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/performance')
def get_performance():
    """API endpoint for dashboard performance metrics."""
    try:
        # Calculate uptime
        start_time = datetime.fromisoformat(PERFORMANCE_METRICS['start_time'])
        uptime = datetime.now() - start_time
        
        # Prepare summary
        metrics = {
            'uptime': {
                'seconds': uptime.total_seconds(),
                'formatted': str(uptime).split('.')[0]  # Remove microseconds
            },
            'api_calls': {
                'total': PERFORMANCE_METRICS['api_calls']['total'],
                'success': PERFORMANCE_METRICS['api_calls']['success'],
                'error': PERFORMANCE_METRICS['api_calls']['error'],
                'success_rate': (PERFORMANCE_METRICS['api_calls']['success'] / max(1, PERFORMANCE_METRICS['api_calls']['total'])) * 100
            },
            'response_times': {
                'avg': PERFORMANCE_METRICS['response_times']['avg'],
                'max': PERFORMANCE_METRICS['response_times']['max'],
                'min': PERFORMANCE_METRICS['response_times']['min']
            },
            'validation': {
                'total': PERFORMANCE_METRICS['validation']['total'],
                'success': PERFORMANCE_METRICS['validation']['success'],
                'error': PERFORMANCE_METRICS['validation']['error'],
                'success_rate': (PERFORMANCE_METRICS['validation']['success'] / max(1, PERFORMANCE_METRICS['validation']['total'])) * 100
            },
            'recent_errors': PERFORMANCE_METRICS['errors'][-10:] if PERFORMANCE_METRICS['errors'] else [],
            'request_times': PERFORMANCE_METRICS['request_times'][-1000:],
            'total_requests': PERFORMANCE_METRICS['total_requests'],
            'avg_request_time': PERFORMANCE_METRICS['avg_request_time']
        }
        
        return jsonify({
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {e}")
        return f"Error loading file: {str(e)}", 404

@app.route('/debug')
def debug_page():
    """Render the debug page for testing and troubleshooting."""
    return render_template('debug.html')

# Dashboard API functions
def update_account(account_info):
    """Update account information."""
    global DASHBOARD_DATA
    DASHBOARD_DATA['account'] = account_info
    socketio.emit('account_update', account_info)

def update_position(symbol, position_info, suppress_notifications=True):
    """Update position information for a symbol.
    
    Args:
        symbol: Trading symbol
        position_info: Position information
        suppress_notifications: Whether to suppress notifications (default True for dashboard updates)
    """
    global DASHBOARD_DATA
    
    # Check if position actually changed before emitting update
    current_position = DASHBOARD_DATA['positions'].get(symbol, {})
    position_changed = (
        current_position.get('qty') != position_info.get('qty') or
        current_position.get('avg_entry_price') != position_info.get('avg_entry_price') or
        abs(float(current_position.get('unrealized_pl', 0)) - float(position_info.get('unrealized_pl', 0))) > 0.01
    )
    
    # Update the position in dashboard data
    DASHBOARD_DATA['positions'][symbol] = position_info
    
    # Only emit socket event if position changed and notifications aren't suppressed
    if position_changed and not suppress_notifications:
        socketio.emit('position_update', {
            'symbol': symbol,
            'data': position_info,
            'suppress_notifications': False
        })
    else:
        # Silent update for UI only
        socketio.emit('position_update_silent', {
            'symbol': symbol,
            'data': position_info
        })

def update_market_status(is_open, next_open=None, next_close=None):
    """Update market status."""
    global DASHBOARD_DATA
    DASHBOARD_DATA['market_status'] = {
        'is_open': is_open,
        'next_open': next_open,
        'next_close': next_close
    }
    socketio.emit('market_status_update', DASHBOARD_DATA['market_status'])

def update_sleep_status(sleep_status):
    """Update sleep status."""
    global DASHBOARD_DATA
    DASHBOARD_DATA['sleep_status'] = sleep_status
    socketio.emit('sleep_status_update', sleep_status)

def update_equity(equity):
    """Update equity history."""
    global DASHBOARD_DATA
    timestamp = datetime.now().isoformat()
    
    # Add to equity history
    DASHBOARD_DATA['equity_history'].append({
        'timestamp': timestamp,
        'equity': equity
    })
    
    # Keep only the last 100 data points
    if len(DASHBOARD_DATA['equity_history']) > 100:
        DASHBOARD_DATA['equity_history'] = DASHBOARD_DATA['equity_history'][-100:]
    
    # Update current equity
    DASHBOARD_DATA['account']['equity'] = equity
    
    socketio.emit('equity_update', {
        'timestamp': timestamp,
        'equity': equity,
        'history': DASHBOARD_DATA['equity_history']
    })

def update_daily_stats(total_trades, win_rate, total_pl):
    """Update daily trading statistics."""
    global DASHBOARD_DATA
    DASHBOARD_DATA['daily_stats'] = {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pl': total_pl
    }
    socketio.emit('daily_stats_update', DASHBOARD_DATA['daily_stats'])

def add_trade(trade_info):
    """Add a trade to the history."""
    global DASHBOARD_DATA
    # Add timestamp if not present
    if 'timestamp' not in trade_info:
        trade_info['timestamp'] = datetime.now().isoformat()
    
    DASHBOARD_DATA['trades'].append(trade_info)
    socketio.emit('trade_update', trade_info)
    
    # Keep only the last 100 trades
    if len(DASHBOARD_DATA['trades']) > 100:
        DASHBOARD_DATA['trades'] = DASHBOARD_DATA['trades'][-100:]

def add_bot_activity(activity):
    """Add a bot activity log."""
    global DASHBOARD_DATA
    # Add timestamp if not present
    if 'timestamp' not in activity:
        activity['timestamp'] = datetime.now().isoformat()
    
    DASHBOARD_DATA['bot_activity'].append(activity)
    
    # Keep only the last 100 activities
    if len(DASHBOARD_DATA['bot_activity']) > 100:
        DASHBOARD_DATA['bot_activity'] = DASHBOARD_DATA['bot_activity'][-100:]
    
    socketio.emit('bot_activity_update', activity)

def update_ml_insights(insights):
    """Update machine learning insights."""
    global DASHBOARD_DATA
    DASHBOARD_DATA['ml_insights'] = insights
    socketio.emit('ml_insights_update', insights)

def add_ml_prediction(prediction):
    """Add a machine learning prediction."""
    global DASHBOARD_DATA
    # Add timestamp if not present
    if 'timestamp' not in prediction:
        prediction['timestamp'] = datetime.now().isoformat()
    
    DASHBOARD_DATA['ml_insights']['recent_predictions'].append(prediction)
    
    # Keep only the last 20 predictions
    if len(DASHBOARD_DATA['ml_insights']['recent_predictions']) > 20:
        DASHBOARD_DATA['ml_insights']['recent_predictions'] = DASHBOARD_DATA['ml_insights']['recent_predictions'][-20:]
    
    socketio.emit('ml_prediction_update', prediction)

def update_market_predictions(predictions):
    """Update market predictions."""
    global DASHBOARD_DATA
    DASHBOARD_DATA['market_predictions'] = predictions
    socketio.emit('market_predictions_update', predictions)

def load_dashboard_data():
    """Load dashboard data from file or initialize with defaults"""
    global DASHBOARD_DATA
    
    try:
        if os.path.exists('data/dashboard_data.json'):
            with open('data/dashboard_data.json', 'r') as f:
                data = json.load(f)
                
                # Validate data if validation is enabled
                if VALIDATION_ENABLED:
                    valid, errors = validate_dashboard_data(data)
                    if not valid:
                        logger.warning(f"Dashboard data validation failed: {errors}")
                        logger.warning("Using default dashboard data")
                        return
                
                # Update dashboard data
                DASHBOARD_DATA = data
                
                # Ensure platform is set to Alpaca
                DASHBOARD_DATA['account']['platform'] = 'Alpaca'
                DASHBOARD_DATA['account']['platform_type'] = 'stocks'
                
                logger.info("Dashboard data loaded from file")
        else:
            # Initialize with sample data
            current_time = datetime.now()
            
            # Generate sample equity history
            equity_history = []
            base_equity = 100000.0
            for i in range(30):
                date = (current_time - timedelta(days=29-i)).strftime('%Y-%m-%d')
                # Add some random variation to equity
                daily_change = np.random.normal(0, 0.01)  # 1% standard deviation
                base_equity *= (1 + daily_change)
                equity_history.append({
                    'date': date,
                    'equity': round(base_equity, 2)
                })
            
            DASHBOARD_DATA['equity_history'] = equity_history
            DASHBOARD_DATA['account']['equity'] = round(base_equity, 2)
            DASHBOARD_DATA['account']['buying_power'] = round(base_equity, 2)
            DASHBOARD_DATA['account']['cash'] = round(base_equity * 0.8, 2)
            DASHBOARD_DATA['account']['platform'] = 'Alpaca'
            DASHBOARD_DATA['account']['platform_type'] = 'stocks'
            
            # Generate sample positions
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            for symbol in symbols:
                quantity = round(np.random.uniform(5, 20), 2)
                entry_price = round(np.random.uniform(100, 500), 2)
                current_price = round(entry_price * (1 + np.random.normal(0, 0.05)), 2)
                profit_loss = round((current_price - entry_price) * quantity, 2)
                profit_loss_pct = round((current_price - entry_price) / entry_price * 100, 2)
                
                DASHBOARD_DATA['positions'][symbol] = {
                    'symbol': symbol,
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'market_value': round(current_price * quantity, 2),
                    'platform': 'Alpaca'
                }
            
            # Generate sample trades
            for i in range(10):
                symbol = symbols[np.random.randint(0, len(symbols))]
                side = 'buy' if np.random.random() > 0.5 else 'sell'
                quantity = round(np.random.uniform(5, 20), 2)
                price = round(np.random.uniform(100, 500), 2)
                timestamp = (current_time - timedelta(days=np.random.randint(0, 10))).isoformat()
                
                DASHBOARD_DATA['trades'].append({
                    'id': f'trade_{i}',
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'timestamp': timestamp,
                    'status': 'filled',
                    'platform': 'Alpaca'
                })
            
            # Generate sample bot activity
            activities = [
                'Bot started',
                'Connected to Alpaca',
                'Market scan completed',
                'Analyzing technical indicators',
                'Detected breakout pattern',
                'Placed buy order',
                'Order filled',
                'Taking profit',
                'Adjusting stop loss',
                'Daily analysis completed'
            ]
            
            for i in range(10):
                activity = activities[i]
                timestamp = (current_time - timedelta(minutes=i*30)).isoformat()
                
                DASHBOARD_DATA['bot_activity'].append({
                    'message': activity,
                    'timestamp': timestamp,
                    'level': 'info',
                    'platform': 'Alpaca'
                })
            
            # Generate sample market predictions
            DASHBOARD_DATA['market_predictions']['next_day'] = generate_sample_predictions()
            
            logger.info("Dashboard initialized with sample data")
    except Exception as e:
        logger.error(f"Error loading dashboard data: {e}")

def save_dashboard_data():
    """Save dashboard data to a file."""
    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        data_file = os.path.join(data_dir, 'dashboard_data.json')
        
        # Create a copy of the data to avoid modifying during serialization
        data_to_save = json.loads(json.dumps(DASHBOARD_DATA))
        
        # Convert datetime objects to strings
        for item in data_to_save['equity_history']:
            if isinstance(item['timestamp'], datetime):
                item['timestamp'] = item['timestamp'].isoformat()
        
        for item in data_to_save['trades']:
            if isinstance(item['timestamp'], datetime):
                item['timestamp'] = item['timestamp'].isoformat()
        
        for item in data_to_save['bot_activity']:
            if isinstance(item['timestamp'], datetime):
                item['timestamp'] = item['timestamp'].isoformat()
        
        with open(data_file, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
        logger.debug("Dashboard data saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving dashboard data: {e}")
        return False

def generate_sample_predictions():
    """Generate sample market predictions for demonstration."""
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'INTC', 'IBM']
    predictions = []
    
    for symbol in symbols:
        # Generate random prediction data
        direction = np.random.choice(['up', 'down'], p=[0.6, 0.4])
        confidence = round(np.random.uniform(0.6, 0.95), 2)
        price_change = round(np.random.uniform(0.5, 3.0) * (1 if direction == 'up' else -1), 2)
        
        predictions.append({
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'price_change': price_change,
            'target_price': None,  # Will be calculated later
            'key_factors': np.random.choice([
                'Strong earnings', 'Technical breakout', 'Sector momentum',
                'Oversold conditions', 'News catalyst', 'Analyst upgrade'
            ], 2).tolist()
        })
    
    # Sort by confidence
    predictions.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Get top 3 picks
    top_picks = [p['symbol'] for p in predictions[:3]]
    
    # Update market predictions
    DASHBOARD_DATA['market_predictions'] = {
        'next_day': predictions,
        'prediction_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'model_confidence': round(np.random.uniform(0.7, 0.9), 2),
        'market_sentiment': np.random.choice(['bullish', 'neutral', 'bearish'], p=[0.6, 0.3, 0.1]),
        'top_picks': top_picks
    }
    
    # Generate some recent predictions with outcomes
    recent_predictions = []
    for i in range(10):
        symbol = np.random.choice(symbols)
        direction = np.random.choice(['up', 'down'])
        confidence = round(np.random.uniform(0.6, 0.95), 2)
        correct = np.random.choice([True, False], p=[0.75, 0.25])
        
        recent_predictions.append({
            'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
            'symbol': symbol,
            'prediction': direction,
            'confidence': confidence,
            'actual': direction if correct else ('down' if direction == 'up' else 'up')
        })
    
    # Update ML insights with recent predictions
    DASHBOARD_DATA['ml_insights']['recent_predictions'] = recent_predictions

def run_dashboard():
    """Run the dashboard server."""
    try:
        # Load existing data if available
        load_dashboard_data()
        
        # Generate sample data if needed
        if not DASHBOARD_DATA['market_predictions']['top_picks']:
            generate_sample_predictions()
        
        # Log startup
        logger.info("Starting KryptoBot Dashboard")
        add_bot_activity({
            'timestamp': datetime.now().isoformat(),
            'message': "Dashboard started with sample data (not connected to real Alpaca account)",
            'level': 'warning'
        })
        
        # Start data saving thread
        def save_data_periodically():
            while True:
                try:
                    time.sleep(5)  # Save every 5 seconds to match dashboard update interval
                    save_dashboard_data()
                except Exception as e:
                    logger.error(f"Error in data saving thread: {e}")
        
        save_thread = threading.Thread(target=save_data_periodically, daemon=True)
        save_thread.start()
        
        # Start real-time update thread
        def broadcast_updates_periodically():
            while True:
                try:
                    time.sleep(1)  # Broadcast updates every second
                    broadcast_update()
                except Exception as e:
                    logger.error(f"Error in broadcast thread: {e}")
        
        broadcast_thread = threading.Thread(target=broadcast_updates_periodically, daemon=True)
        broadcast_thread.start()
        
        # Start the Flask server with SocketIO
        socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
        
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        raise

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected to dashboard WebSocket")
    # Send initial data to the client
    emit('initial_data', DASHBOARD_DATA)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected from dashboard WebSocket")

@socketio.on('request_update')
def handle_update_request(data):
    """Handle client request for data update."""
    logger.debug(f"Client requested update: {data}")
    # Send the requested data
    if data.get('type') == 'all':
        emit('initial_data', DASHBOARD_DATA)
    elif data.get('type') == 'account':
        emit('account_update', DASHBOARD_DATA['account'])
    elif data.get('type') == 'positions':
        emit('positions_update', DASHBOARD_DATA['positions'])
    elif data.get('type') == 'trades':
        emit('trades_update', DASHBOARD_DATA['trades'])
    elif data.get('type') == 'activity':
        emit('activity_update', DASHBOARD_DATA['bot_activity'])

# Function to broadcast updates to all clients
def broadcast_update():
    """Broadcast updates to all connected clients."""
    socketio.emit('data_update', DASHBOARD_DATA)

if __name__ == '__main__':
    run_dashboard() 