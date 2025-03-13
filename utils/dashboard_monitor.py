#!/usr/bin/env python3
"""
Dashboard Monitoring Utility

This module provides tools for monitoring the performance and stability
of the KryptoBot Trading Dashboard. It tracks metrics such as response times,
error rates, and resource usage, and provides alerts for potential issues.
"""

import os
import time
import json
import logging
import threading
import datetime
import psutil
import requests
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DashboardMonitor:
    """
    Monitor for tracking dashboard performance and stability
    """
    
    def __init__(self, dashboard_url: str = "http://localhost:5001", 
                 check_interval: int = 60, alert_threshold: int = 3):
        """
        Initialize the dashboard monitor
        
        Args:
            dashboard_url: URL of the dashboard
            check_interval: Interval between checks in seconds
            alert_threshold: Number of consecutive failures before alerting
        """
        self.dashboard_url = dashboard_url
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.metrics_file = os.path.join('data', 'dashboard_metrics.json')
        self.metrics: Dict[str, Any] = {
            'start_time': datetime.datetime.now().isoformat(),
            'checks': [],
            'alerts': [],
            'stats': {
                'total_checks': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'avg_response_time': 0,
                'max_response_time': 0,
                'min_response_time': float('inf'),
                'last_check_time': None
            }
        }
        self.consecutive_failures = 0
        self.running = False
        self.monitor_thread = None
        
        # Create necessary directories
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Load existing metrics if available
        self._load_metrics()
    
    def start(self):
        """Start the monitoring thread"""
        if self.running:
            logger.warning("Monitor is already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Dashboard monitor started, checking {self.dashboard_url} every {self.check_interval} seconds")
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Dashboard monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_dashboard()
                self._save_metrics()
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            # Sleep until next check
            time.sleep(self.check_interval)
    
    def _check_dashboard(self):
        """Check dashboard health and performance"""
        check_time = datetime.datetime.now()
        check_result = {
            'timestamp': check_time.isoformat(),
            'success': False,
            'response_time': 0,
            'status_code': None,
            'error': None,
            'system_metrics': self._get_system_metrics()
        }
        
        try:
            # Check main dashboard page
            start_time = time.time()
            response = requests.get(f"{self.dashboard_url}/", timeout=10)
            response_time = time.time() - start_time
            
            check_result['response_time'] = response_time
            check_result['status_code'] = response.status_code
            check_result['success'] = 200 <= response.status_code < 300
            
            # Check API endpoint
            api_start_time = time.time()
            api_response = requests.get(f"{self.dashboard_url}/api/data", timeout=10)
            api_response_time = time.time() - api_start_time
            
            check_result['api_response_time'] = api_response_time
            check_result['api_status_code'] = api_response.status_code
            check_result['api_success'] = 200 <= api_response.status_code < 300
            
            # Update consecutive failures counter
            if check_result['success'] and check_result['api_success']:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.alert_threshold:
                    self._trigger_alert(check_result)
            
            # Update stats
            self.metrics['stats']['total_checks'] += 1
            if check_result['success']:
                self.metrics['stats']['successful_checks'] += 1
            else:
                self.metrics['stats']['failed_checks'] += 1
            
            # Update response time stats
            current_avg = self.metrics['stats']['avg_response_time']
            total_checks = self.metrics['stats']['total_checks']
            self.metrics['stats']['avg_response_time'] = (current_avg * (total_checks - 1) + response_time) / total_checks
            self.metrics['stats']['max_response_time'] = max(self.metrics['stats']['max_response_time'], response_time)
            self.metrics['stats']['min_response_time'] = min(self.metrics['stats']['min_response_time'], response_time)
            self.metrics['stats']['last_check_time'] = check_time.isoformat()
            
        except Exception as e:
            check_result['error'] = str(e)
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.alert_threshold:
                self._trigger_alert(check_result)
            
            self.metrics['stats']['total_checks'] += 1
            self.metrics['stats']['failed_checks'] += 1
            logger.error(f"Dashboard check failed: {e}")
        
        # Add check result to metrics
        self.metrics['checks'].append(check_result)
        
        # Keep only the last 1000 checks to prevent the file from growing too large
        if len(self.metrics['checks']) > 1000:
            self.metrics['checks'] = self.metrics['checks'][-1000:]
        
        return check_result
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            process = psutil.Process(os.getpid())
            
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'process_cpu_percent': process.cpu_percent(),
                'process_memory_percent': process.memory_percent(),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def _trigger_alert(self, check_result: Dict[str, Any]):
        """Trigger an alert for dashboard issues"""
        alert = {
            'timestamp': datetime.datetime.now().isoformat(),
            'consecutive_failures': self.consecutive_failures,
            'check_result': check_result,
            'message': f"Dashboard alert: {self.consecutive_failures} consecutive failures"
        }
        
        self.metrics['alerts'].append(alert)
        
        # Keep only the last 100 alerts
        if len(self.metrics['alerts']) > 100:
            self.metrics['alerts'] = self.metrics['alerts'][-100:]
        
        logger.warning(f"Dashboard alert triggered: {self.consecutive_failures} consecutive failures")
        
        # Here you could add additional alert mechanisms like email or SMS
        # For example:
        # self._send_email_alert(alert)
    
    def _load_metrics(self):
        """Load metrics from file"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    loaded_metrics = json.load(f)
                    
                    # Update metrics with loaded data, preserving current start time
                    start_time = self.metrics['start_time']
                    self.metrics = loaded_metrics
                    self.metrics['start_time'] = start_time
                    
                    logger.info(f"Loaded metrics from {self.metrics_file}")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of the current metrics"""
        uptime = datetime.datetime.now() - datetime.datetime.fromisoformat(self.metrics['start_time'])
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0],  # Remove microseconds
            'total_checks': self.metrics['stats']['total_checks'],
            'successful_checks': self.metrics['stats']['successful_checks'],
            'failed_checks': self.metrics['stats']['failed_checks'],
            'success_rate': (self.metrics['stats']['successful_checks'] / max(1, self.metrics['stats']['total_checks'])) * 100,
            'avg_response_time': self.metrics['stats']['avg_response_time'],
            'max_response_time': self.metrics['stats']['max_response_time'],
            'min_response_time': self.metrics['stats']['min_response_time'],
            'last_check_time': self.metrics['stats']['last_check_time'],
            'alert_count': len(self.metrics['alerts']),
            'recent_alerts': self.metrics['alerts'][-5:] if self.metrics['alerts'] else []
        }

def run_dashboard_monitor():
    """Run the dashboard monitor as a standalone process"""
    monitor = DashboardMonitor()
    monitor.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(60)
            summary = monitor.get_metrics_summary()
            logger.info(f"Dashboard monitor summary: "
                       f"Uptime: {summary['uptime_formatted']}, "
                       f"Success rate: {summary['success_rate']:.2f}%, "
                       f"Avg response time: {summary['avg_response_time']:.3f}s")
    except KeyboardInterrupt:
        logger.info("Dashboard monitor stopping due to keyboard interrupt")
    finally:
        monitor.stop()

if __name__ == "__main__":
    run_dashboard_monitor() 