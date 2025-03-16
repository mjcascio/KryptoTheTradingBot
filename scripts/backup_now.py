#!/usr/bin/env python3
"""
Simple GitHub Backup Trigger

This script triggers the Automated Backup workflow on GitHub.
"""

import sys
import requests

def trigger_backup(token, owner="mjcascio", repo="KryptoTheTradingBot"):
    """Trigger the backup workflow."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/backup.yml/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"✅ Successfully triggered backup workflow for {owner}/{repo}")
        return True
    except Exception as e:
        print(f"❌ Failed to trigger backup workflow: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backup_now.py <github_token>")
        sys.exit(1)
    
    token = sys.argv[1]
    success = trigger_backup(token)
    sys.exit(0 if success else 1) 