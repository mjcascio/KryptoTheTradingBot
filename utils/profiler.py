"""Performance monitoring utilities for the KryptoBot Trading System."""

import time
import cProfile
import pstats
import asyncio
import functools
from typing import Any, Callable, Dict, Optional, TypeVar
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

from utils.logging import setup_logging

logger = setup_logging(__name__)

# Type variables for generic function decorators
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    execution_time: float
    memory_usage: int
    call_count: int
    avg_latency: float
    last_call: datetime
    peak_memory: int

class PerformanceMonitor:
    """Monitors and tracks performance metrics."""

    def __init__(self) -> None:
        """Initialize the performance monitor."""
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.profiler = cProfile.Profile()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._function_metrics = defaultdict(list)
        self._start_time = time.time()

    def profile(self, func: F) -> F:
        """Decorator to profile a function's performance.
        
        Args:
            func: Function to profile
            
        Returns:
            Wrapped function with profiling
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            self.profiler.enable()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                self.profiler.disable()
                execution_time = time.time() - start_time
                
                # Update metrics
                self._update_metrics(
                    func.__name__,
                    execution_time,
                    self.profiler.getstats()
                )
                
                # Log if execution time is high
                if execution_time > 1.0:  # Threshold of 1 second
                    logger.warning(
                        f"Slow execution in {func.__name__}: {execution_time:.2f}s"
                    )
        
        return wrapper  # type: ignore

    async def profile_async(self, func: AsyncF) -> AsyncF:
        """Decorator to profile an async function's performance.
        
        Args:
            func: Async function to profile
            
        Returns:
            Wrapped async function with profiling
        """
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            self.profiler.enable()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                self.profiler.disable()
                execution_time = time.time() - start_time
                
                # Update metrics asynchronously
                asyncio.create_task(
                    self._async_update_metrics(
                        func.__name__,
                        execution_time,
                        self.profiler.getstats()
                    )
                )
                
                # Log if execution time is high
                if execution_time > 1.0:
                    logger.warning(
                        f"Slow async execution in {func.__name__}: {execution_time:.2f}s"
                    )
        
        return wrapper  # type: ignore

    def _update_metrics(
        self,
        function_name: str,
        execution_time: float,
        stats: Any
    ) -> None:
        """Update performance metrics for a function.
        
        Args:
            function_name: Name of the function
            execution_time: Execution time in seconds
            stats: Profiler statistics
        """
        # Calculate memory usage from stats
        memory_usage = sum(stat.size for stat in stats if hasattr(stat, 'size'))
        
        # Get or create metrics
        if function_name not in self.metrics:
            self.metrics[function_name] = PerformanceMetrics(
                execution_time=execution_time,
                memory_usage=memory_usage,
                call_count=1,
                avg_latency=execution_time,
                last_call=datetime.now(),
                peak_memory=memory_usage
            )
        else:
            metrics = self.metrics[function_name]
            
            # Update metrics
            metrics.call_count += 1
            metrics.avg_latency = (
                (metrics.avg_latency * (metrics.call_count - 1) + execution_time)
                / metrics.call_count
            )
            metrics.last_call = datetime.now()
            metrics.peak_memory = max(metrics.peak_memory, memory_usage)
            metrics.memory_usage = memory_usage
            metrics.execution_time = execution_time

    async def _async_update_metrics(
        self,
        function_name: str,
        execution_time: float,
        stats: Any
    ) -> None:
        """Update performance metrics asynchronously.
        
        Args:
            function_name: Name of the function
            execution_time: Execution time in seconds
            stats: Profiler statistics
        """
        await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._update_metrics,
            function_name,
            execution_time,
            stats
        )

    def get_metrics(self, function_name: Optional[str] = None) -> Dict[str, PerformanceMetrics]:
        """Get performance metrics.
        
        Args:
            function_name: Optional function name to get specific metrics
            
        Returns:
            Dictionary of performance metrics
        """
        if function_name:
            return {function_name: self.metrics.get(function_name)}
        return self.metrics.copy()

    def get_performance_report(self) -> str:
        """Generate a performance report.
        
        Returns:
            Formatted performance report
        """
        report = ["Performance Report", "=================", ""]
        
        for func_name, metrics in self.metrics.items():
            report.extend([
                f"Function: {func_name}",
                f"  Calls: {metrics.call_count}",
                f"  Average Latency: {metrics.avg_latency:.3f}s",
                f"  Last Execution Time: {metrics.execution_time:.3f}s",
                f"  Memory Usage: {metrics.memory_usage / 1024:.2f}KB",
                f"  Peak Memory: {metrics.peak_memory / 1024:.2f}KB",
                f"  Last Call: {metrics.last_call.isoformat()}",
                ""
            ])
        
        return "\n".join(report)

    def export_stats(self, output_file: str = 'profile_stats.txt') -> None:
        """Export profiler statistics to a file.
        
        Args:
            output_file: Path to output file
        """
        stats = pstats.Stats(self.profiler)
        stats.sort_stats('cumulative')
        stats.dump_stats(output_file)

# Create global instance
performance_monitor = PerformanceMonitor() 