#!/usr/bin/env python3
"""
System Monitoring Module

This module provides system monitoring capabilities for tracking
CPU, memory, disk usage, and other system metrics.
"""

import os
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MetricsConfig:
    """Configuration for system metrics collection."""
    collection_interval: int = 60  # seconds
    retention_days: int = 7
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        """Set default alert thresholds if none provided."""
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_usage": 80.0,      # 80% CPU usage
                "memory_usage": 80.0,    # 80% memory usage
                "disk_usage": 80.0,      # 80% disk usage
                "network_errors": 100,    # 100 errors per interval
                "process_count": 500      # Maximum number of processes
            }


class SystemMonitor:
    """System monitoring and metrics collection."""
    
    def __init__(self, config: MetricsConfig):
        """Initialize the system monitor."""
        self.config = config
        self.metrics_history: List[Dict] = []
        self.last_collection: Optional[datetime] = None
        self.error_log: List[str] = []
        
        # Initialize system metrics
        self.update_metrics()
    
    def update_metrics(self) -> Dict:
        """Update system metrics."""
        try:
            metrics = {
                "timestamp": datetime.now(),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "network_stats": self._get_network_stats(),
                "process_count": len(psutil.pids()),
                "load_average": os.getloadavg()
            }
            
            # Check thresholds and log alerts
            self._check_thresholds(metrics)
            
            # Update history
            self.metrics_history.append(metrics)
            self.last_collection = metrics["timestamp"]
            
            # Cleanup old metrics
            self._cleanup_old_metrics()
            
            return metrics
            
        except Exception as e:
            error_msg = f"Error updating system metrics: {e}"
            logger.error(error_msg)
            self.error_log.append(error_msg)
            return {}
    
    def get_current_metrics(self) -> Dict:
        """Get the most recent metrics."""
        if not self.metrics_history:
            return self.update_metrics()
        
        # Check if we need to update
        if (datetime.now() - self.last_collection >
                timedelta(seconds=self.config.collection_interval)):
            return self.update_metrics()
        
        return self.metrics_history[-1]
    
    def get_metrics_history(self) -> List[Dict]:
        """Get historical metrics."""
        return self.metrics_history
    
    def get_recent_errors(self) -> List[str]:
        """Get recent error messages."""
        # Return last 10 errors
        return self.error_log[-10:]
    
    def _get_network_stats(self) -> Dict:
        """Get network statistics."""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout
            }
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return {}
    
    def _check_thresholds(self, metrics: Dict):
        """Check metrics against thresholds and log alerts."""
        for metric, value in metrics.items():
            if metric in self.config.alert_thresholds:
                threshold = self.config.alert_thresholds[metric]
                if isinstance(value, (int, float)) and value > threshold:
                    alert_msg = (
                        f"Alert: {metric} is {value}, "
                        f"exceeding threshold of {threshold}"
                    )
                    logger.warning(alert_msg)
                    self.error_log.append(alert_msg)
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        if not self.metrics_history:
            return
        
        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        self.metrics_history = [
            m for m in self.metrics_history
            if m["timestamp"] > cutoff
        ]
        
        # Also cleanup old error logs (keep last 100)
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:] 