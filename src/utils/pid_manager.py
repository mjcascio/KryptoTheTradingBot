"""
PID Manager utility for handling process ID files.
Provides centralized PID file management functionality for the trading bot.
"""

import os
import logging
import psutil
import time
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class PIDManager:
    """Manages PID file operations for the trading bot."""
    
    def __init__(self, pid_file: str = "bot.pid", process_name: str = "main.py"):
        """
        Initialize PID manager.
        
        Args:
            pid_file (str): Path to the PID file
            process_name (str): Name of the process to verify
        """
        self.pid_file = pid_file
        self.process_name = process_name
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the directory for the PID file exists."""
        pid_dir = os.path.dirname(self.pid_file)
        if pid_dir:
            Path(pid_dir).mkdir(parents=True, exist_ok=True)
    
    def _verify_process(self, pid: int) -> bool:
        """
        Verify that a process is our bot process.
        
        Args:
            pid (int): Process ID to verify
            
        Returns:
            bool: True if process is verified as our bot
        """
        try:
            process = psutil.Process(pid)
            if not process.is_running():
                return False
            
            # Check if it's a Python process running our bot
            cmdline = process.cmdline()
            return any(self.process_name in cmd for cmd in cmdline)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
    
    def check_pid(self) -> Tuple[bool, Optional[int]]:
        """
        Check if a process with the PID from the PID file is running.
        
        Returns:
            Tuple[bool, Optional[int]]: (is_running, pid)
                - is_running: True if process is running and verified
                - pid: Process ID if file exists, None otherwise
        """
        if not os.path.exists(self.pid_file):
            logger.debug("PID file does not exist")
            return False, None
            
        try:
            with open(self.pid_file, 'r') as f:
                content = f.read().strip()
                
            try:
                pid = int(content)
            except ValueError:
                logger.warning(f"Invalid PID file content: {content}")
                self.remove_pid()
                return False, None
                
            # Verify it's our process
            if self._verify_process(pid):
                logger.debug(f"Found running bot process (PID: {pid})")
                return True, pid
            
            logger.warning(f"Process {pid} exists but is not our bot")
            return False, pid
                
        except (OSError, IOError) as e:
            logger.error(f"Error reading PID file: {e}")
            return False, None
    
    def create_pid(self, pid: int, timeout: int = 5) -> bool:
        """
        Create a PID file with the given process ID.
        
        Args:
            pid (int): Process ID to write
            timeout (int): Timeout in seconds to verify process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First verify the process exists
            if not psutil.pid_exists(pid):
                logger.error(f"Process {pid} does not exist")
                return False
            
            # Write PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(pid))
            
            # Verify file was written correctly
            start_time = time.time()
            while time.time() - start_time < timeout:
                if os.path.exists(self.pid_file):
                    with open(self.pid_file, 'r') as f:
                        if f.read().strip() == str(pid):
                            logger.info(f"Created PID file for process {pid}")
                            return True
                time.sleep(0.1)
            
            logger.error("Failed to verify PID file creation")
            return False
            
        except Exception as e:
            logger.error(f"Failed to create PID file: {e}")
            return False
    
    def remove_pid(self) -> bool:
        """
        Remove the PID file if it exists.
        
        Returns:
            bool: True if successful or file didn't exist, False on error
        """
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                logger.info("Removed PID file")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove PID file: {e}")
            return False
    
    def cleanup_stale(self) -> bool:
        """
        Remove the PID file if it's stale (process not running or not our bot).
        
        Returns:
            bool: True if cleanup successful or not needed, False on error
        """
        is_running, pid = self.check_pid()
        if not is_running and pid is not None:
            logger.info(f"Cleaning up stale PID file (PID: {pid})")
            return self.remove_pid()
        return True
    
    def wait_for_pid_file_removal(self, timeout: int = 5) -> bool:
        """
        Wait for PID file to be removed.
        
        Args:
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            bool: True if file was removed, False if timeout occurred
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not os.path.exists(self.pid_file):
                return True
            time.sleep(0.1)
        return False 