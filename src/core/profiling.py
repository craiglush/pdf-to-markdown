"""
Performance profiling utilities for document conversion.

Provides tools for measuring and optimizing conversion performance.
"""

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceTimer:
    """
    Simple context manager for timing operations.

    Usage:
        with PerformanceTimer("operation_name"):
            # ... code to time ...
    """

    def __init__(self, name: str, log_level: int = logging.INFO):
        """
        Initialize timer.

        Args:
            name: Name of the operation being timed
            log_level: Logging level for timing results
        """
        self.name = name
        self.log_level = log_level
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and log result."""
        self.end_time = time.perf_counter()
        elapsed = self.end_time - self.start_time

        if exc_type is None:
            logger.log(
                self.log_level, f"{self.name} completed in {elapsed:.3f}s"
            )
        else:
            logger.log(
                self.log_level, f"{self.name} failed after {elapsed:.3f}s"
            )

    @property
    def elapsed(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return None
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time


@contextmanager
def timer(name: str):
    """
    Simple context manager for timing code blocks.

    Args:
        name: Name of the operation

    Yields:
        PerformanceTimer instance

    Example:
        with timer("conversion"):
            result = convert_document()
    """
    t = PerformanceTimer(name)
    with t:
        yield t


def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile function execution time.

    Args:
        func: Function to profile

    Returns:
        Wrapped function with timing

    Example:
        @profile_function
        def my_function():
            pass
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.debug(f"{func.__name__} took {elapsed:.3f}s")
            return result
        except Exception:
            elapsed = time.perf_counter() - start_time
            logger.debug(f"{func.__name__} failed after {elapsed:.3f}s")
            raise

    return wrapper


class PerformanceMonitor:
    """
    Track performance metrics across multiple operations.

    Useful for batch processing and performance analysis.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, list] = {}

    def record(self, operation: str, duration: float, **kwargs):
        """
        Record a performance metric.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            **kwargs: Additional metadata
        """
        if operation not in self.metrics:
            self.metrics[operation] = []

        self.metrics[operation].append(
            {"duration": duration, "timestamp": time.time(), **kwargs}
        )

    @contextmanager
    def measure(self, operation: str, **kwargs):
        """
        Context manager to measure and record operation time.

        Args:
            operation: Name of the operation
            **kwargs: Additional metadata to record

        Example:
            monitor = PerformanceMonitor()
            with monitor.measure("conversion", file_size=1024):
                convert_document()
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.record(operation, duration, **kwargs)

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics.

        Args:
            operation: Specific operation to get stats for (None for all)

        Returns:
            Dictionary with performance statistics
        """
        if operation:
            if operation not in self.metrics:
                return {"operation": operation, "count": 0}

            durations = [m["duration"] for m in self.metrics[operation]]
            return {
                "operation": operation,
                "count": len(durations),
                "total": sum(durations),
                "avg": sum(durations) / len(durations) if durations else 0,
                "min": min(durations) if durations else 0,
                "max": max(durations) if durations else 0,
            }
        else:
            # Get stats for all operations
            return {
                op: self.get_stats(op) for op in self.metrics.keys()
            }

    def print_summary(self):
        """Print performance summary to logger."""
        if not self.metrics:
            logger.info("No performance metrics recorded")
            return

        logger.info("=== Performance Summary ===")
        for operation in self.metrics:
            stats = self.get_stats(operation)
            logger.info(
                f"{operation}: {stats['count']} ops, "
                f"avg: {stats['avg']:.3f}s, "
                f"min: {stats['min']:.3f}s, "
                f"max: {stats['max']:.3f}s, "
                f"total: {stats['total']:.3f}s"
            )

    def clear(self):
        """Clear all recorded metrics."""
        self.metrics.clear()


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def get_global_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.

    Returns:
        Global PerformanceMonitor
    """
    return _global_monitor
