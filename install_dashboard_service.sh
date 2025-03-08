#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs

# Get the absolute path to the current directory
CURRENT_DIR=$(pwd)

# Create LaunchAgents directory if it doesn't exist
mkdir -p ~/Library/LaunchAgents

# Copy the plist file to LaunchAgents directory
cp com.krypto.dashboard.plist ~/Library/LaunchAgents/

# Update the WorkingDirectory in the plist file to use the absolute path
sed -i '' "s|/Users/mjcascio/Documents/KryptoTheTradingBot|$CURRENT_DIR|g" ~/Library/LaunchAgents/com.krypto.dashboard.plist

echo "Dashboard service installed to ~/Library/LaunchAgents/com.krypto.dashboard.plist"

# Load the LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.krypto.dashboard.plist 2>/dev/null
launchctl load -w ~/Library/LaunchAgents/com.krypto.dashboard.plist

echo "Dashboard service loaded. It will start automatically when you log in."
echo "To start it now, run: launchctl start com.krypto.dashboard"
echo "To stop it, run: launchctl stop com.krypto.dashboard" 