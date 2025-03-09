#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime
import argparse

def run_command(command):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def list_backups():
    """List all available backups."""
    print("\nAvailable Backups:")
    print("-" * 50)
    
    # Fetch latest from remote
    run_command("git fetch origin")
    
    # Get all backup branches
    branches = run_command("git branch -r | grep 'origin/backup/' | sort -r")
    
    if not branches:
        print("No backups found.")
        return
    
    for branch in branches.split('\n'):
        branch = branch.strip()
        if branch:
            # Get the commit date
            date_str = run_command(f"git log -1 --format=%cd {branch}")
            print(f"{branch[7:]} - {date_str}")

def restore_backup(backup_name):
    """Restore a specific backup."""
    if not backup_name.startswith('backup/'):
        backup_name = f'backup/{backup_name}'
    
    print(f"\nRestoring backup: {backup_name}")
    
    # Create a backup of current state
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup = f"pre_restore_backup_{current_date}"
    
    print(f"Creating backup of current state: {current_backup}")
    run_command(f"git checkout -b {current_backup}")
    run_command("git add -A")
    run_command(f'git commit -m "Automatic backup before restore - {current_date}"')
    
    # Restore the backup
    print(f"Restoring {backup_name}...")
    run_command(f"git checkout origin/{backup_name}")
    
    print("\nBackup restored successfully!")
    print(f"Your previous state was saved in branch: {current_backup}")

def trigger_backup():
    """Trigger a manual backup."""
    print("\nTriggering manual backup...")
    run_command("gh workflow run backup.yml")
    print("Backup workflow triggered. Check GitHub Actions for progress.")

def main():
    parser = argparse.ArgumentParser(description='Manage trading bot backups')
    parser.add_argument('action', choices=['list', 'restore', 'backup'],
                      help='Action to perform (list, restore, or backup)')
    parser.add_argument('--name', help='Name of the backup to restore')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_backups()
    elif args.action == 'restore':
        if not args.name:
            print("Error: Please provide a backup name to restore")
            sys.exit(1)
        restore_backup(args.name)
    elif args.action == 'backup':
        trigger_backup()

if __name__ == "__main__":
    main() 