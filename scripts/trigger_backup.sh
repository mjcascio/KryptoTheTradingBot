#!/bin/bash
# Script to trigger GitHub backup workflow

# Default values
OWNER="mjcascio"
REPO="KryptoTheTradingBot"
WORKFLOW="backup.yml"

# Check if token is provided
if [ -z "$1" ]; then
  echo "Error: GitHub token is required"
  echo "Usage: $0 <github_token>"
  exit 1
fi

TOKEN="$1"

# API URL
URL="https://api.github.com/repos/$OWNER/$REPO/actions/workflows/$WORKFLOW/dispatches"

# Trigger the workflow
echo "Triggering backup workflow..."
curl -s -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $TOKEN" \
  -d '{"ref":"main"}' \
  "$URL"

# Check if the request was successful
if [ $? -eq 0 ]; then
  echo "✅ Backup workflow triggered successfully!"
  echo "Check GitHub Actions at: https://github.com/$OWNER/$REPO/actions"
else
  echo "❌ Failed to trigger backup workflow"
  exit 1
fi 