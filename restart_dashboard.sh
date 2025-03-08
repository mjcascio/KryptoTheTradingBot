#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "Restarting KryptoBot Dashboard..."

# Stop the dashboard
./stop_dashboard.sh

# Wait a moment to ensure ports are freed
sleep 2

# Start the dashboard
./start_dashboard.sh

echo "Dashboard restart complete." 