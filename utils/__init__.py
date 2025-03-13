"""
Utilities module for KryptoBot Trading System.

This module provides shared helper functions and utilities used throughout
the application. It includes logging configuration, system monitoring,
and common helper functions that support the core functionality.

Key Components:
    - Logging: Configurable logging setup with rotation and formatting
    - System Monitoring: Resource usage and uptime tracking
    - Helper Functions: Common utilities shared across modules

Example:
    from utils.logging import setup_logging
    from utils.system import get_uptime, get_system_metrics

    # Set up module logging
    logger = setup_logging(__name__)
    logger.info("Module initialized")

    # Monitor system resources
    metrics = get_system_metrics()
    logger.info(
        f"CPU: {metrics['cpu_usage']}%, "
        f"Memory: {metrics['memory_usage']}%, "
        f"Disk: {metrics['disk_usage']}%"
    )

    # Track uptime
    uptime = get_uptime(start_time)
    logger.info(f"System uptime: {uptime}")
"""

from .logging import setup_logging
from .system import get_uptime, get_system_metrics 