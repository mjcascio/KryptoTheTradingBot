#!/usr/bin/env python3
"""System monitoring and diagnostics module for KryptoBot."""

import os
import sys
import psutil
import logging
import platform
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
import pytz
from telegram_notifications import send_telegram_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """System monitoring and diagnostics for KryptoBot."""
    
    def __init__(self, trading_bot=None):
        """Initialize the system monitor."""
        self.trading_bot = trading_bot
        self.start_time = datetime.now(pytz.UTC)
        self.last_diagnostic_run = None
        self.error_count = 0
        self.warning_count = 0
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs/diagnostics', exist_ok=True)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report."""
        try:
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate uptime
            uptime = datetime.now(pytz.UTC) - self.start_time
            
            # Get trading bot status
            bot_status = self._get_bot_status()
            
            # Compile health report
            health_report = {
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'system': {
                    'uptime': str(uptime),
                    'cpu_usage': f"{cpu_usage}%",
                    'memory_usage': f"{memory.percent}%",
                    'disk_usage': f"{disk.percent}%",
                    'platform': platform.platform(),
                    'python_version': sys.version.split()[0]
                },
                'trading_bot': bot_status,
                'error_metrics': {
                    'error_count': self.error_count,
                    'warning_count': self.warning_count,
                    'last_diagnostic_run': self.last_diagnostic_run.isoformat() if self.last_diagnostic_run else None
                }
            }
            
            return health_report
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            self._send_error_notification("System Health Check Failed", str(e))
            return {'error': str(e)}
    
    def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        try:
            diagnostic_results = {
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'tests': [],
                'issues_found': 0,
                'critical_issues': 0
            }
            
            # Run connection tests
            self._run_connection_tests(diagnostic_results)
            
            # Run data integrity tests
            self._run_data_integrity_tests(diagnostic_results)
            
            # Run performance tests
            self._run_performance_tests(diagnostic_results)
            
            # Run security tests
            self._run_security_tests(diagnostic_results)
            
            # Save diagnostic results
            self._save_diagnostic_results(diagnostic_results)
            
            self.last_diagnostic_run = datetime.now(pytz.UTC)
            
            return diagnostic_results
            
        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            self._send_error_notification("System Diagnostics Failed", str(e))
            return {'error': str(e)}
    
    def _get_bot_status(self) -> Dict[str, Any]:
        """Get trading bot status and metrics."""
        if not self.trading_bot:
            return {'error': 'Trading bot not initialized'}
        
        try:
            # Get basic bot status
            status = self.trading_bot.get_status()
            
            # Get options trading status
            options_status = self.trading_bot.get_options_trading_status()
            
            # Get active broker info
            active_broker = self.trading_bot.broker_factory.get_active_broker()
            broker_info = {
                'name': active_broker.get_platform_name() if active_broker else None,
                'connected': active_broker.connected if active_broker else False
            }
            
            # Compile complete status
            return {
                'is_running': status['is_running'],
                'market_open': status['market_open'],
                'active_broker': broker_info,
                'positions': {
                    'stocks': len(self.trading_bot.positions['stocks']),
                    'options': len(self.trading_bot.positions['options'])
                },
                'daily_metrics': {
                    'trades': self.trading_bot.daily_trades,
                    'pl': self.trading_bot.daily_pl
                },
                'risk_parameters': self.trading_bot.risk_params
            }
            
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {'error': str(e)}
    
    def _run_connection_tests(self, results: Dict[str, Any]):
        """Run connection tests for all components."""
        test_results = []
        
        # Test broker connections
        if self.trading_bot:
            active_broker = self.trading_bot.broker_factory.get_active_broker()
            if active_broker:
                test_results.append({
                    'name': 'Broker Connection',
                    'component': active_broker.get_platform_name(),
                    'status': 'PASS' if active_broker.connected else 'FAIL',
                    'details': 'Connected to broker' if active_broker.connected else 'Failed to connect to broker'
                })
        
        # Test market data connection
        if hasattr(self.trading_bot, 'market_data'):
            try:
                # Try to fetch some test data
                test_symbol = 'AAPL'  # Use a reliable test symbol
                data = self.trading_bot.market_data.get_market_data(test_symbol)
                status = 'PASS' if data is not None else 'FAIL'
                details = 'Market data available' if data is not None else 'Failed to fetch market data'
            except Exception as e:
                status = 'FAIL'
                details = f"Market data error: {str(e)}"
            
            test_results.append({
                'name': 'Market Data Connection',
                'component': 'Market Data Service',
                'status': status,
                'details': details
            })
        
        results['tests'].extend(test_results)
        results['issues_found'] += sum(1 for test in test_results if test['status'] == 'FAIL')
    
    def _run_data_integrity_tests(self, results: Dict[str, Any]):
        """Run data integrity tests."""
        test_results = []
        
        # Check position tracking integrity
        if self.trading_bot:
            try:
                # Compare local position tracking with broker positions
                broker_positions = self.trading_bot.broker_factory.get_active_broker().get_positions()
                local_positions = self.trading_bot.positions['stocks']
                
                positions_match = set(broker_positions.keys()) == set(local_positions.keys())
                test_results.append({
                    'name': 'Position Tracking Integrity',
                    'component': 'Position Management',
                    'status': 'PASS' if positions_match else 'FAIL',
                    'details': 'Position tracking matches broker' if positions_match else 'Position tracking mismatch'
                })
            except Exception as e:
                test_results.append({
                    'name': 'Position Tracking Integrity',
                    'component': 'Position Management',
                    'status': 'FAIL',
                    'details': f"Error checking positions: {str(e)}"
                })
        
        results['tests'].extend(test_results)
        results['issues_found'] += sum(1 for test in test_results if test['status'] == 'FAIL')
    
    def _run_performance_tests(self, results: Dict[str, Any]):
        """Run performance tests."""
        test_results = []
        
        # Check system resource usage
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # CPU usage test
        test_results.append({
            'name': 'CPU Usage',
            'component': 'System Resources',
            'status': 'PASS' if cpu_usage < 80 else 'WARN' if cpu_usage < 90 else 'FAIL',
            'details': f"CPU Usage: {cpu_usage}%"
        })
        
        # Memory usage test
        test_results.append({
            'name': 'Memory Usage',
            'component': 'System Resources',
            'status': 'PASS' if memory.percent < 80 else 'WARN' if memory.percent < 90 else 'FAIL',
            'details': f"Memory Usage: {memory.percent}%"
        })
        
        results['tests'].extend(test_results)
        results['issues_found'] += sum(1 for test in test_results if test['status'] == 'FAIL')
        results['critical_issues'] += sum(1 for test in test_results if test['status'] == 'FAIL')
    
    def _run_security_tests(self, results: Dict[str, Any]):
        """Run security tests."""
        test_results = []
        
        # Check API key security
        env_vars = ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'TELEGRAM_BOT_TOKEN']
        for var in env_vars:
            test_results.append({
                'name': f"{var} Security",
                'component': 'API Security',
                'status': 'PASS' if os.getenv(var) else 'FAIL',
                'details': f"{var} is properly set" if os.getenv(var) else f"Missing {var}"
            })
        
        results['tests'].extend(test_results)
        results['issues_found'] += sum(1 for test in test_results if test['status'] == 'FAIL')
        results['critical_issues'] += sum(1 for test in test_results if test['status'] == 'FAIL')
    
    def _save_diagnostic_results(self, results: Dict[str, Any]):
        """Save diagnostic results to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs/diagnostics/diagnostic_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Diagnostic results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving diagnostic results: {e}")
    
    def _send_error_notification(self, title: str, error: str):
        """Send error notification via Telegram."""
        try:
            message = f"🚨 *{title}*\n\n"
            message += f"Error: {error}\n\n"
            message += f"Time: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            message += f"Check logs for more details."
            
            send_telegram_message(message)
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}") 