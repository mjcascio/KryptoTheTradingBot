"""
Deployment Safety Module

This module implements safety measures for deploying changes to the trading bot,
including version control, testing, and rollback capabilities.
"""

import logging
import subprocess
import datetime
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class DeploymentSafety:
    """Manages safe deployments and changes to the trading bot."""
    
    def __init__(self, project_root: str):
        """
        Initialize the deployment safety manager.
        
        Args:
            project_root: Root directory of the trading bot project
        """
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / 'backups'
        self.test_results_dir = self.project_root / 'test_results'
        self.logs_dir = self.project_root / 'logs' / 'deployment'
        
        # Create necessary directories
        for directory in [self.backup_dir, self.test_results_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging for deployment operations."""
        log_file = self.logs_dir / f'deployment_{datetime.datetime.now():%Y%m%d_%H%M%S}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    
    def create_backup(self) -> str:
        """
        Create a backup of the current codebase state.
        
        Returns:
            str: Name of the backup branch created
        """
        try:
            # Create a new backup branch with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_branch = f'backup/{timestamp}'
            
            # Create and switch to backup branch
            subprocess.run(['git', 'checkout', '-b', backup_branch], check=True)
            
            # Add all changes and commit
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(
                ['git', 'commit', '-m', f'Backup: Creating safety snapshot at {timestamp}'],
                check=True
            )
            
            logger.info(f'Successfully created backup branch: {backup_branch}')
            return backup_branch
            
        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to create backup: {str(e)}')
            raise RuntimeError('Backup creation failed') from e
    
    def run_tests(self) -> bool:
        """
        Run all available tests and static analysis.
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        try:
            # Run pytest with coverage
            test_result = subprocess.run(
                ['pytest', '--cov=src', '--cov-report=html:test_results/coverage'],
                capture_output=True,
                text=True
            )
            
            # Run static type checking with mypy
            mypy_result = subprocess.run(
                ['mypy', 'src'],
                capture_output=True,
                text=True
            )
            
            # Run linting with flake8
            flake8_result = subprocess.run(
                ['flake8', 'src'],
                capture_output=True,
                text=True
            )
            
            # Save test results
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = self.test_results_dir / f'test_results_{timestamp}.txt'
            
            with open(results_file, 'w') as f:
                f.write('=== Pytest Results ===\n')
                f.write(test_result.stdout)
                f.write('\n\n=== MyPy Results ===\n')
                f.write(mypy_result.stdout)
                f.write('\n\n=== Flake8 Results ===\n')
                f.write(flake8_result.stdout)
            
            tests_passed = all(
                result.returncode == 0 
                for result in [test_result, mypy_result, flake8_result]
            )
            
            if tests_passed:
                logger.info('All tests passed successfully')
            else:
                logger.error('Some tests failed. Check test results for details')
            
            return tests_passed
            
        except subprocess.CalledProcessError as e:
            logger.error(f'Test execution failed: {str(e)}')
            return False
    
    def rollback_changes(self, backup_branch: str) -> bool:
        """
        Rollback to a previous backup state.
        
        Args:
            backup_branch: Name of the backup branch to restore
            
        Returns:
            bool: True if rollback successful, False otherwise
        """
        try:
            # Stash any current changes
            subprocess.run(['git', 'stash'], check=True)
            
            # Switch to the backup branch
            subprocess.run(['git', 'checkout', backup_branch], check=True)
            
            logger.info(f'Successfully rolled back to backup: {backup_branch}')
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to rollback changes: {str(e)}')
            return False
    
    def update_documentation(self, changes: List[str]) -> None:
        """
        Update project documentation with new changes.
        
        Args:
            changes: List of changes to document
        """
        try:
            docs_dir = self.project_root / 'docs'
            changelog_file = docs_dir / 'CHANGELOG.md'
            
            # Create docs directory if it doesn't exist
            docs_dir.mkdir(exist_ok=True)
            
            # Update changelog
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(changelog_file, 'a') as f:
                f.write(f'\n## [{timestamp}]\n')
                for change in changes:
                    f.write(f'- {change}\n')
            
            # Add and commit documentation changes
            subprocess.run(['git', 'add', str(changelog_file)], check=True)
            subprocess.run(
                ['git', 'commit', '-m', f'docs: Update changelog with changes at {timestamp}'],
                check=True
            )
            
            logger.info('Successfully updated documentation')
            
        except Exception as e:
            logger.error(f'Failed to update documentation: {str(e)}')
    
    def verify_system_health(self) -> Dict[str, bool]:
        """
        Verify the health of all trading bot systems.
        
        Returns:
            Dict[str, bool]: Status of each system component
        """
        health_checks = {
            'trading_engine': self._check_trading_engine(),
            'monitoring': self._check_monitoring_system(),
            'remote_control': self._check_remote_control(),
            'data_feeds': self._check_data_feeds()
        }
        
        all_healthy = all(health_checks.values())
        if all_healthy:
            logger.info('All systems operational')
        else:
            failed_systems = [
                system for system, status in health_checks.items() 
                if not status
            ]
            logger.error(f'System health check failed for: {", ".join(failed_systems)}')
        
        return health_checks
    
    def _check_trading_engine(self) -> bool:
        """Check if the trading engine is operational."""
        try:
            # Check if trading engine process is running
            result = subprocess.run(
                ['pgrep', '-f', 'trading_bot.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("Trading engine process not found")
                return False
                
            # Check if trading engine is responsive by checking log file
            log_file = self.project_root / 'logs' / 'trading_bot.out'
            if not log_file.exists():
                logger.warning("Trading engine log file not found")
                return False
                
            # Check for recent activity in log file (last 5 minutes)
            last_modified = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
            if (datetime.datetime.now() - last_modified).total_seconds() > 300:
                logger.warning("Trading engine log file not recently updated")
                return False
                
            logger.info("Trading engine check passed")
            return True
            
        except Exception as e:
            logger.error(f"Error checking trading engine: {str(e)}")
            return False
    
    def _check_monitoring_system(self) -> bool:
        """Check if the monitoring system is operational."""
        try:
            # Check if monitoring process is running
            result = subprocess.run(
                ['pgrep', '-f', 'system_monitor.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("Monitoring system process not found")
                return False
                
            # Check if monitoring system is logging data
            monitor_log = self.project_root / 'logs' / 'system_monitor.out'
            if not monitor_log.exists():
                logger.warning("Monitoring system log file not found")
                return False
                
            # Check for recent activity in log file (last 10 minutes)
            last_modified = datetime.datetime.fromtimestamp(monitor_log.stat().st_mtime)
            if (datetime.datetime.now() - last_modified).total_seconds() > 600:
                logger.warning("Monitoring system log file not recently updated")
                return False
                
            # Check if metrics database exists and is accessible
            metrics_db = self.project_root / 'data' / 'metrics.db'
            if not metrics_db.exists():
                logger.warning("Metrics database not found")
                return False
                
            logger.info("Monitoring system check passed")
            return True
            
        except Exception as e:
            logger.error(f"Error checking monitoring system: {str(e)}")
            return False
    
    def _check_remote_control(self) -> bool:
        """Check if remote control functionality is operational."""
        try:
            # Check if Telegram notification service is running
            result = subprocess.run(
                ['pgrep', '-f', 'telegram.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("Telegram notification service not found")
                return False
                
            # Check Telegram log file
            telegram_log = self.project_root / 'logs' / 'telegram.log'
            if not telegram_log.exists():
                logger.warning("Telegram log file not found")
                return False
                
            # Check for recent activity (last hour)
            last_modified = datetime.datetime.fromtimestamp(telegram_log.stat().st_mtime)
            if (datetime.datetime.now() - last_modified).total_seconds() > 3600:
                logger.warning("Telegram log file not recently updated")
                return False
                
            logger.info("Remote control check passed")
            return True
            
        except Exception as e:
            logger.error(f"Error checking remote control: {str(e)}")
            return False
    
    def _check_data_feeds(self) -> bool:
        """Check if all data feeds are operational."""
        try:
            # Check if data feed processes are running
            data_feed_processes = [
                'alpaca_sync.py',
                'market_data.py',
                'options_service.py'
            ]
            
            all_running = True
            for process in data_feed_processes:
                result = subprocess.run(
                    ['pgrep', '-f', process],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.warning(f"Data feed process {process} not found")
                    all_running = False
            
            # Check data feed log files
            data_feed_logs = [
                'alpaca_sync.out',
                'options_service.log',
                'data_validator.log'
            ]
            
            all_logs_exist = True
            for log_file in data_feed_logs:
                log_path = self.project_root / 'logs' / log_file
                if not log_path.exists():
                    logger.warning(f"Data feed log file {log_file} not found")
                    all_logs_exist = False
                    
                # Check for recent activity (last 15 minutes)
                if log_path.exists():
                    last_modified = datetime.datetime.fromtimestamp(log_path.stat().st_mtime)
                    if (datetime.datetime.now() - last_modified).total_seconds() > 900:
                        logger.warning(f"Data feed log file {log_file} not recently updated")
                        all_logs_exist = False
            
            result = all_running and all_logs_exist
            if result:
                logger.info("Data feeds check passed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking data feeds: {str(e)}")
            return False 