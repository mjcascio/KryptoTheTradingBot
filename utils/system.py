"""System utilities for the KryptoBot Trading System."""

import os
import psutil
from datetime import datetime
from typing import Dict

def get_uptime(start_time: datetime) -> str:
    """Calculate system uptime from start time
    
    Args:
        start_time: The datetime when the system started
        
    Returns:
        Formatted uptime string (e.g., "2d 5h 30m 15s")
    """
    uptime = datetime.now() - start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_system_metrics() -> Dict[str, float]:
    """Get system performance metrics
    
    Returns:
        Dictionary containing CPU, memory, and disk usage percentages
    """
    return {
        'cpu_usage': psutil.cpu_percent(interval=0.1),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }

def is_process_running(process_name: str) -> bool:
    """Check if a process is running
    
    Args:
        process_name: Name of the process to check
        
    Returns:
        True if the process is running, False otherwise
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == process_name or (
                proc.info['cmdline'] and 
                any(process_name in cmd for cmd in proc.info['cmdline'])
            ):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def write_pid_file(pid_file: str):
    """Write process ID to a file
    
    Args:
        pid_file: Path to the PID file
    """
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid())) 