#!/usr/bin/env python3
"""
Deployment script for the trading bot.

This script manages safe deployments of changes to the trading bot,
following best practices for version control, testing, and integration.
"""

import sys
import logging
import argparse
from pathlib import Path

from src.utils.deployment_safety import DeploymentSafety

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Safely deploy changes to the trading bot.'
    )
    parser.add_argument(
        '--changes',
        nargs='+',
        help='List of changes being deployed (for documentation)',
        required=True
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip running tests (not recommended)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force deployment even if tests fail (not recommended)'
    )
    return parser.parse_args()


def main() -> int:
    """
    Main deployment function.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        args = parse_args()
        project_root = Path(__file__).parent
        
        # Initialize deployment safety manager
        safety = DeploymentSafety(str(project_root))
        
        # Create backup
        logger.info('Creating backup...')
        backup_branch = safety.create_backup()
        logger.info(f'Backup created: {backup_branch}')
        
        if not args.skip_tests:
            # Run tests
            logger.info('Running tests...')
            tests_passed = safety.run_tests()
            
            if not tests_passed and not args.force:
                logger.error('Tests failed. Rolling back changes...')
                safety.rollback_changes(backup_branch)
                return 1
            elif not tests_passed:
                logger.warning(
                    'Tests failed but --force flag is set. '
                    'Proceeding with deployment...'
                )
        else:
            logger.warning(
                'Skipping tests due to --skip-tests flag. '
                'This is not recommended!'
            )
        
        # Verify system health
        logger.info('Verifying system health...')
        health_status = safety.verify_system_health()
        
        if not all(health_status.values()):
            logger.error('System health check failed. Rolling back changes...')
            safety.rollback_changes(backup_branch)
            return 1
        
        # Update documentation
        logger.info('Updating documentation...')
        safety.update_documentation(args.changes)
        
        logger.info('Deployment completed successfully!')
        return 0
        
    except Exception as e:
        logger.error(f'Deployment failed: {str(e)}')
        return 1


if __name__ == '__main__':
    sys.exit(main()) 