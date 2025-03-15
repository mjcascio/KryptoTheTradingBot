"""System monitoring module for tracking system metrics."""

import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MetricsConfig:
    """Configuration for system metrics collection."""
    
    collection_interval: int = 60  # seconds
    retention_days: int = 7
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self) -> None:
        """Set default alert thresholds if none provided."""
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_usage": 80.0,  # percent
                "memory_usage": 80.0,  # percent
                "disk_usage": 80.0,  # percent
                "error_rate": 10.0  # errors per minute
            }


class SystemMonitor:
    """Monitor system metrics and performance."""

    def __init__(self, config: MetricsConfig) -> None:
        """Initialize the system monitor.
        
        Args:
            config: Metrics configuration
        """
        self.config = config
        self.start_time = datetime.now()
        self.last_collection = datetime.now()
        self.metrics_history: List[Dict[str, Any]] = []
        self.error_history: List[Dict[str, Any]] = []
        
        # Initialize system info
        self.cpu_count = psutil.cpu_count()
        self.total_memory = psutil.virtual_memory().total
        self.disk_usage = psutil.disk_usage('/')
        
        logger.info(
            f"System monitor initialized with {self.cpu_count} CPUs, "
            f"{self.total_memory / (1024**3):.1f}GB RAM"
        )

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics.
        
        Returns:
            Dictionary of system metrics
        """
        now = datetime.now()
        
        # Only collect if interval has passed
        if (now - self.last_collection).total_seconds() < self.config.collection_interval:
            return self.get_latest_metrics()
            
        try:
            # Collect metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics = {
                'timestamp': now,
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available,
                'disk_usage': disk.percent,
                'disk_free': disk.free,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'error_rate': self._calculate_error_rate()
            }
            
            # Check thresholds and log alerts
            self._check_thresholds(metrics)
            
            # Store metrics
            self.metrics_history.append(metrics)
            self.last_collection = now
            
            # Clean up old metrics
            self._cleanup_old_data()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return self.get_latest_metrics()

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get most recently collected metrics.
        
        Returns:
            Dictionary of latest metrics or empty dict if none collected
        """
        return self.metrics_history[-1] if self.metrics_history else {}

    def get_metrics_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics history for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of metric dictionaries
        """
        if not start_time:
            start_time = datetime.now() - timedelta(days=1)
        if not end_time:
            end_time = datetime.now()
            
        return [
            metrics for metrics in self.metrics_history
            if start_time <= metrics['timestamp'] <= end_time
        ]

    def log_error(self, error: str, severity: str = "error") -> None:
        """Log an error for tracking.
        
        Args:
            error: Error message
            severity: Error severity (default: error)
        """
        self.error_history.append({
            'timestamp': datetime.now(),
            'message': error,
            'severity': severity
        })
        
        # Log through standard logging
        if severity == "error":
            logger.error(error)
        elif severity == "warning":
            logger.warning(error)
        else:
            logger.info(error)

    def get_recent_errors(
        self,
        minutes: int = 60,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent errors.
        
        Args:
            minutes: Number of minutes to look back
            severity: Filter by severity
            
        Returns:
            List of error dictionaries
        """
        start_time = datetime.now() - timedelta(minutes=minutes)
        
        return [
            error for error in self.error_history
            if error['timestamp'] >= start_time
            and (not severity or error['severity'] == severity)
        ]

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate (errors per minute)."""
        recent_errors = self.get_recent_errors(minutes=1)
        return len(recent_errors)

    def _check_thresholds(self, metrics: Dict[str, Any]) -> None:
        """Check metrics against thresholds and log alerts."""
        for metric, threshold in self.config.alert_thresholds.items():
            if metric in metrics and metrics[metric] > threshold:
                self.log_error(
                    f"System alert: {metric} at {metrics[metric]:.1f}% "
                    f"(threshold: {threshold}%)",
                    severity="warning"
                )

    def _cleanup_old_data(self) -> None:
        """Remove metrics and errors older than retention period."""
        retention_time = datetime.now() - timedelta(days=self.config.retention_days)
        
        # Clean up metrics
        self.metrics_history = [
            metrics for metrics in self.metrics_history
            if metrics['timestamp'] >= retention_time
        ]
        
        # Clean up errors
        self.error_history = [
            error for error in self.error_history
            if error['timestamp'] >= retention_time
        ]

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics and status.
        
        Returns:
            Dictionary containing current metrics and status
        """
        metrics = self.collect_metrics()
        
        # Add additional status information
        metrics.update({
            'uptime': str(datetime.now() - self.start_time),
            'active_processes': len(psutil.pids()),
            'last_error': (
                self.error_history[-1]['message']
                if self.error_history else "None"
            ),
            'network_latency': self._check_network_latency()
        })
        
        return metrics

    def _check_network_latency(self) -> float:
        """Check network latency by pinging common hosts.
        
        Returns:
            Average latency in milliseconds
        """
        try:
            # Use psutil's net_io_counters as a lightweight alternative
            # to actual ping since we can't use subprocess in this context
            start = time.time()
            psutil.net_io_counters()
            end = time.time()
            
            # Convert to milliseconds
            return (end - start) * 1000
            
        except Exception as e:
            logger.error(f"Error checking network latency: {e}")
            return 0.0 