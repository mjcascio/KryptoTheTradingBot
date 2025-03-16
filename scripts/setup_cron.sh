#!/bin/bash
# Script to set up a cron job for automated backups

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_SCRIPT="$PROJECT_DIR/backup.sh"
LOG_FILE="$PROJECT_DIR/logs/cron/backup_cron.log"

# Create the log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Check if the backup script exists and is executable
if [ ! -x "$BACKUP_SCRIPT" ]; then
    echo "Error: Backup script not found or not executable: $BACKUP_SCRIPT"
    exit 1
fi

# Create a temporary file for the crontab
TEMP_CRONTAB=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "" > "$TEMP_CRONTAB"

# Check if the cron job already exists
if grep -q "$BACKUP_SCRIPT" "$TEMP_CRONTAB"; then
    echo "Cron job for backup already exists. Updating..."
    # Remove the existing cron job
    grep -v "$BACKUP_SCRIPT" "$TEMP_CRONTAB" > "${TEMP_CRONTAB}.new"
    mv "${TEMP_CRONTAB}.new" "$TEMP_CRONTAB"
else
    echo "Adding new cron job for backup..."
fi

# Add the new cron job - runs daily at 2 AM
echo "0 2 * * * $BACKUP_SCRIPT >> $LOG_FILE 2>&1" >> "$TEMP_CRONTAB"

# Install the new crontab
crontab "$TEMP_CRONTAB"

# Clean up
rm "$TEMP_CRONTAB"

echo "Cron job set up successfully!"
echo "The backup will run daily at 2:00 AM and log to: $LOG_FILE"
echo ""
echo "To view your cron jobs, run: crontab -l"
echo "To edit your cron jobs, run: crontab -e" 