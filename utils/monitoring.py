"""System monitoring utilities for the KryptoBot Trading System."""

import logging
import time
import os
import psutil
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MetricsConfig:
    """Configuration for system metrics collection."""
    
    def __init__(self, 
                 collection_interval: int = 60, 
                 retention_days: int = 7,
                 alert_thresholds: Dict[str, float] = None):
        """Initialize metrics configuration.
        
        Args:
            collection_interval: Interval between metrics collections in seconds
            retention_days: Number of days to retain metrics
            alert_thresholds: Dictionary of metric thresholds for alerts
        """
        self.collection_interval = collection_interval
        self.retention_days = retention_days
        self.alert_thresholds = alert_thresholds or {
            "cpu_usage": 80.0,
            "memory_usage": 80.0,
            "disk_usage": 80.0
        }

class SystemMonitor:
    """System monitoring for the KryptoBot Trading System."""
    
    def __init__(self, config: MetricsConfig):
        """Initialize the system monitor.
        
        Args:
            config: Metrics configuration
        """
        self.config = config
        self.metrics = {}
        self.alerts = []
        self.process = psutil.Process(os.getpid())
        self.collection_task = None
        self.running = False
        logger.info("System monitor initialized")
        
    async def start(self):
        """Start the system monitor."""
        if self.running:
            logger.warning("System monitor already running")
            return
            
        self.running = True
        self.collection_task = asyncio.create_task(self._collect_metrics_loop())
        logger.info("System monitor started")
        
    async def stop(self):
        """Stop the system monitor."""
        if not self.running:
            return
            
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
                
        logger.info("System monitor stopped")
        
    async def _collect_metrics_loop(self):
        """Collect metrics in a loop."""
        try:
            while self.running:
                await self.collect_metrics()
                await asyncio.sleep(self.config.collection_interval)
        except asyncio.CancelledError:
            logger.info("Metrics collection task cancelled")
        except Exception as e:
            logger.error(f"Error in metrics collection loop: {e}")
            
    async def collect_metrics(self):
        """Collect system metrics."""
        try:
            timestamp = datetime.now()
            
            # Collect system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Collect process metrics
            process_cpu = self.process.cpu_percent(interval=1)
            process_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
            
            # Store metrics
            metrics = {
                "timestamp": timestamp,
                "system": {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory.percent,
                    "memory_available": memory.available / (1024 * 1024),  # MB
                    "disk_usage": disk.percent,
                    "disk_free": disk.free / (1024 * 1024 * 1024)  # GB
                },
                "process": {
                    "cpu_usage": process_cpu,
                    "memory_usage": process_memory,
                    "threads": self.process.num_threads()
                }
            }
            
            # Store metrics
            self.metrics[timestamp.isoformat()] = metrics
            
            # Check for alerts
            await self._check_alerts(metrics)
            
            # Clean up old metrics
            await self._cleanup_old_metrics()
            
            logger.debug("Collected system metrics")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            
    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alerts based on metrics.
        
        Args:
            metrics: Collected metrics
        """
        timestamp = metrics["timestamp"]
        
        # Check CPU usage
        if metrics["system"]["cpu_usage"] > self.config.alert_thresholds["cpu_usage"]:
            await self._create_alert(
                "high_cpu_usage",
                f"High CPU usage: {metrics['system']['cpu_usage']:.1f}%",
                timestamp
            )
            
        # Check memory usage
        if metrics["system"]["memory_usage"] > self.config.alert_thresholds["memory_usage"]:
            await self._create_alert(
                "high_memory_usage",
                f"High memory usage: {metrics['system']['memory_usage']:.1f}%",
                timestamp
            )
            
        # Check disk usage
        if metrics["system"]["disk_usage"] > self.config.alert_thresholds["disk_usage"]:
            await self._create_alert(
                "high_disk_usage",
                f"High disk usage: {metrics['system']['disk_usage']:.1f}%",
                timestamp
            )
            
    async def _create_alert(self, alert_type: str, message: str, timestamp: datetime):
        """Create a system alert.
        
        Args:
            alert_type: Type of alert
            message: Alert message
            timestamp: Alert timestamp
        """
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": timestamp.isoformat()
        }
        
        self.alerts.append(alert)
        logger.warning(f"System alert: {message}")
        
    async def _cleanup_old_metrics(self):
        """Clean up old metrics."""
        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        cutoff_str = cutoff.isoformat()
        
        # Remove old metrics
        old_keys = [k for k in self.metrics.keys() if k < cutoff_str]
        for k in old_keys:
            del self.metrics[k]
            
        # Remove old alerts
        self.alerts = [a for a in self.alerts if a["timestamp"] >= cutoff_str]
        
    async def record_error(self, error_type: str):
        """Record an error.
        
        Args:
            error_type: Type of error
        """
        timestamp = datetime.now()
        
        # Create error record
        error = {
            "type": error_type,
            "timestamp": timestamp.isoformat()
        }
        
        # Store error
        if "errors" not in self.metrics:
            self.metrics["errors"] = []
            
        self.metrics["errors"].append(error)
        logger.debug(f"Recorded error: {error_type}")
        
    async def record_trade(self, symbol: str, side: str):
        """Record a trade.
        
        Args:
            symbol: Trading symbol
            side: Trade side (buy/sell)
        """
        timestamp = datetime.now()
        
        # Create trade record
        trade = {
            "symbol": symbol,
            "side": side,
            "timestamp": timestamp.isoformat()
        }
        
        # Store trade
        if "trades" not in self.metrics:
            self.metrics["trades"] = []
            
        self.metrics["trades"].append(trade)
        logger.debug(f"Recorded trade: {symbol} {side}")
        
    async def record_metric(self, name: str, value: float):
        """Record a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
        """
        timestamp = datetime.now()
        
        # Store metric
        if "custom" not in self.metrics:
            self.metrics["custom"] = {}
            
        if name not in self.metrics["custom"]:
            self.metrics["custom"][name] = []
            
        self.metrics["custom"][name].append({
            "value": value,
            "timestamp": timestamp.isoformat()
        })
        
        logger.debug(f"Recorded metric: {name}={value}")
        
    def get_metrics(self, metric_type: Optional[str] = None) -> Dict[str, Any]:
        """Get collected metrics.
        
        Args:
            metric_type: Type of metrics to get (system, process, custom, etc.)
            
        Returns:
            Dictionary of metrics
        """
        if metric_type:
            result = {}
            for timestamp, metrics in self.metrics.items():
                if isinstance(metrics, dict) and metric_type in metrics:
                    result[timestamp] = metrics[metric_type]
            return result
        
        return self.metrics
        
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts.
        
        Returns:
            List of alerts
        """
        return self.alerts 