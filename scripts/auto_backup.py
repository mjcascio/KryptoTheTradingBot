#!/usr/bin/env python3
"""
Automated GitHub Backup Script

This script automatically triggers the backup workflow on GitHub
using the token stored in the config file.
"""

import sys
import requests
import os
from pathlib import Path

# Add the scripts directory to the Python path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

try:
    # Import configuration
    from config import GITHUB_TOKEN, OWNER, REPO, BACKUP_WORKFLOW
except ImportError:
    print("❌ Error: Could not import configuration.")
    print("Make sure to set your GitHub token in scripts/config.py")
    sys.exit(1)

def trigger_backup():
    """Trigger the backup workflow using stored credentials."""
    # Check if token is configured
    if GITHUB_TOKEN == "YOUR_TOKEN_HERE":
        print("❌ Error: GitHub token not configured.")
        print("Please edit scripts/config.py and set your GitHub token.")
        return False
    
    # API URL
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{BACKUP_WORKFLOW}/dispatches"
    
    # Headers and data
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main"
    }
    
    # Trigger the workflow
    print(f"Triggering backup workflow for {OWNER}/{REPO}...")
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print("✅ Backup workflow triggered successfully!")
        print(f"Check GitHub Actions at: https://github.com/{OWNER}/{REPO}/actions")
        return True
    except Exception as e:
        print(f"❌ Failed to trigger backup workflow: {str(e)}")
        return False

if __name__ == "__main__":
    success = trigger_backup()
    sys.exit(0 if success else 1) 