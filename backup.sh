#!/bin/bash
# Simple script to run the automated backup

# Change to the project directory
cd "$(dirname "$0")"

# Run the backup script
python3 scripts/auto_backup.py

# Exit with the same status as the backup script
exit $? 