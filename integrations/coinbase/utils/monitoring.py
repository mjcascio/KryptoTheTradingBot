"""Performance monitoring system."""

import time
import psutil
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data."""
    
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    response_time: float
    request_count: int
    error_count: int
    cache_hits: int
    cache_misses: int

class PerformanceMonitor:
    """System performance monitoring."""
    
    def __init__(
        self,
        interval: float = 1.0,
        history_size: int = 3600  # 1 hour at 1s interval
    ) -> None:
        """Initialize monitor.
        
        Args:
            interval: Monitoring interval in seconds
            history_size: Number of historical metrics to keep
        """
        self.interval = interval
        self.history_size = history_size
        
        self._metrics: List[PerformanceMetrics] = []
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Performance counters
        self._request_count = 0
        self._error_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._response_times: List[float] = []
    
    async def start(self) -> None:
        """Start performance monitoring."""
        if not self._running:
            self._running = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self) -> None:
        """Stop performance monitoring."""
        if self._running:
            self._running = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                metrics = self._collect_metrics()
                self._metrics.append(metrics)
                
                # Trim history if needed
                if len(self._metrics) > self.history_size:
                    self._metrics = self._metrics[-self.history_size:]
                
                # Reset counters
                self._response_times = []
                self._request_count = 0
                self._error_count = 0
                self._cache_hits = 0
                self._cache_misses = 0
                
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {str(e)}")
                await asyncio.sleep(self.interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics.
        
        Returns:
            Performance metrics
        """
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.Process().memory_percent(),
            response_time=np.mean(self._response_times) if self._response_times else 0,
            request_count=self._request_count,
            error_count=self._error_count,
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses
        )
    
    def record_request(self, response_time: float) -> None:
        """Record API request metrics.
        
        Args:
            response_time: Request response time
        """
        self._request_count += 1
        self._response_times.append(response_time)
    
    def record_error(self) -> None:
        """Record API error."""
        self._error_count += 1
    
    def record_cache_hit(self) -> None:
        """Record cache hit."""
        self._cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record cache miss."""
        self._cache_misses += 1
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics.
        
        Returns:
            Current metrics
        """
        return self._collect_metrics()
    
    def get_historical_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PerformanceMetrics]:
        """Get historical performance metrics.
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List of metrics
        """
        metrics = self._metrics
        
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        return metrics
    
    def get_summary_metrics(
        self,
        window: timedelta = timedelta(minutes=5)
    ) -> Dict[str, Any]:
        """Get summary metrics for time window.
        
        Args:
            window: Time window
            
        Returns:
            Summary metrics
        """
        start_time = datetime.now() - window
        metrics = self.get_historical_metrics(start_time=start_time)
        
        if not metrics:
            return {}
        
        return {
            "avg_cpu_percent": np.mean([m.cpu_percent for m in metrics]),
            "max_cpu_percent": np.max([m.cpu_percent for m in metrics]),
            "avg_memory_percent": np.mean([m.memory_percent for m in metrics]),
            "max_memory_percent": np.max([m.memory_percent for m in metrics]),
            "avg_response_time": np.mean([m.response_time for m in metrics]),
            "p95_response_time": np.percentile([m.response_time for m in metrics], 95),
            "total_requests": sum(m.request_count for m in metrics),
            "total_errors": sum(m.error_count for m in metrics),
            "error_rate": sum(m.error_count for m in metrics) / sum(m.request_count for m in metrics) if sum(m.request_count for m in metrics) > 0 else 0,
            "cache_hit_rate": sum(m.cache_hits for m in metrics) / (sum(m.cache_hits for m in metrics) + sum(m.cache_misses for m in metrics)) if (sum(m.cache_hits for m in metrics) + sum(m.cache_misses for m in metrics)) > 0 else 0
        }

def monitor_performance(monitor: PerformanceMonitor):
    """Decorator for monitoring function performance.
    
    Args:
        monitor: Performance monitor instance
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                monitor.record_request(time.time() - start_time)
                return result
            except Exception as e:
                monitor.record_error()
                raise
        return wrapper
    return decorator 