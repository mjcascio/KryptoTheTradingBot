#!/usr/bin/env python3
"""
GitHub Backup Trigger Script

This script triggers the Automated Backup workflow on GitHub using the GitHub API.
It requires a GitHub Personal Access Token with appropriate permissions.
"""

import os
import sys
import requests
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def trigger_backup(token, owner, repo):
    """
    Trigger the Automated Backup workflow on GitHub.
    
    Args:
        token: GitHub Personal Access Token
        owner: Repository owner (username or organization)
        repo: Repository name
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/backup.yml/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main"  # The branch to run the workflow on
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"Successfully triggered backup workflow for {owner}/{repo}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to trigger backup workflow: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Trigger GitHub Automated Backup workflow")
    parser.add_argument("--token", help="GitHub Personal Access Token")
    parser.add_argument("--owner", help="Repository owner (username or organization)")
    parser.add_argument("--repo", help="Repository name")
    
    args = parser.parse_args()
    
    # Get token from environment if not provided
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GitHub token not provided. Use --token or set GITHUB_TOKEN "
                     "environment variable.")
        sys.exit(1)
    
    # Get owner and repo from environment if not provided
    owner = args.owner or os.environ.get("GITHUB_OWNER") or "mjcascio"
    repo = args.repo or os.environ.get("GITHUB_REPO") or "KryptoTheTradingBot"
    
    if not owner or not repo:
        logger.error("Repository owner and name are required.")
        sys.exit(1)
    
    success = trigger_backup(token, owner, repo)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 