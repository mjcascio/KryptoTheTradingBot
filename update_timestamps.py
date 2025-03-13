#!/usr/bin/env python3
"""
Update Timestamps Script

This script updates the timestamps in the trade history to today's date.
"""

import json
from datetime import datetime

# Get today's date
today = datetime.now().strftime('%Y-%m-%d')

# Load trade history
with open('data/trade_history.json', 'r') as f:
    data = json.load(f)

# Update timestamps for the last two trades
for i in range(5, len(data)):
    data[i]['timestamp'] = today + data[i]['timestamp'][10:]

# Save updated trade history
with open('data/trade_history.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Updated timestamps for {len(data) - 5} trades to {today}") 