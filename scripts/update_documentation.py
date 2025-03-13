#!/usr/bin/env python3
"""
Documentation Update Script for KryptoBot Trading System

This script automatically updates the full_bot_overview.md file based on
the current state of the codebase. It extracts information from various
files and updates the documentation accordingly.

Usage:
    python scripts/update_documentation.py

The script will:
1. Scan the codebase for changes
2. Extract relevant information from key files
3. Update the full_bot_overview.md file with the latest information
4. Update the timestamp in the documentation
"""

import os
import re
import sys
import glob
import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Constants
OVERVIEW_FILE = 'full_bot_overview.md'
TIMESTAMP_PATTERN = r'\*This document was last updated on: \[.*?\]\*'
TIMESTAMP_REPLACEMENT = f'*This document was last updated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*'

def get_module_docstring(filepath):
    """Extract the module docstring from a Python file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract docstring using regex
    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if docstring_match:
        return docstring_match.group(1).strip()
    return None

def get_class_info(filepath, class_name):
    """Extract information about a specific class from a Python file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the class definition
    class_pattern = rf'class {class_name}\(.*?\):'
    class_match = re.search(class_pattern, content)
    if not class_match:
        return None
    
    # Find the class docstring
    class_start = class_match.end()
    docstring_match = re.search(r'"""(.*?)"""', content[class_start:], re.DOTALL)
    if docstring_match:
        return docstring_match.group(1).strip()
    
    return None

def get_function_info(filepath, function_name):
    """Extract information about a specific function from a Python file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the function definition
    function_pattern = rf'def {function_name}\(.*?\):'
    function_match = re.search(function_pattern, content)
    if not function_match:
        return None
    
    # Find the function docstring
    function_start = function_match.end()
    docstring_match = re.search(r'"""(.*?)"""', content[function_start:], re.DOTALL)
    if docstring_match:
        return docstring_match.group(1).strip()
    
    return None

def get_api_endpoints(filepath='dashboard.py'):
    """Extract API endpoints from the dashboard file."""
    endpoints = []
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find all route definitions
    route_matches = re.finditer(r'@app\.route\([\'"](.+?)[\'"](.*?)\)', content)
    for match in route_matches:
        route = match.group(1)
        methods = re.search(r'methods=\[(.*?)\]', match.group(2))
        if methods:
            methods_str = methods.group(1)
            methods_list = [m.strip("'\"") for m in methods_str.split(',')]
            endpoints.append((route, methods_list))
        else:
            endpoints.append((route, ['GET']))
    
    return endpoints

def get_config_params(filepath='config.py'):
    """Extract configuration parameters from the config file."""
    params = {}
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find parameter dictionaries
    param_matches = re.finditer(r'([A-Z_]+)_PARAMS\s*=\s*{(.*?)}', content, re.DOTALL)
    for match in param_matches:
        param_name = match.group(1)
        param_content = match.group(2)
        params[param_name] = param_content
    
    return params

def update_overview_file():
    """Update the full_bot_overview.md file with the latest information."""
    if not os.path.exists(OVERVIEW_FILE):
        print(f"Error: {OVERVIEW_FILE} not found.")
        return False
    
    with open(OVERVIEW_FILE, 'r') as f:
        content = f.read()
    
    # Update timestamp
    updated_content = re.sub(TIMESTAMP_PATTERN, TIMESTAMP_REPLACEMENT, content)
    
    # Write updated content back to the file
    with open(OVERVIEW_FILE, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated {OVERVIEW_FILE} with the latest timestamp.")
    return True

def main():
    """Main function to update the documentation."""
    print("Starting documentation update...")
    
    # Ensure we're in the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Update the overview file
    if update_overview_file():
        print("Documentation update completed successfully.")
    else:
        print("Documentation update failed.")

if __name__ == "__main__":
    main() 