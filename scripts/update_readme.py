#!/usr/bin/env python3

"""
Script to automatically update the README.md command line documentation.
This script extracts commands from shell scripts and updates the Command Line Reference section.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

def extract_commands_from_script(script_path: str) -> List[str]:
    """Extract commands and their comments from shell scripts."""
    commands = []
    with open(script_path, 'r') as f:
        for line in f:
            # Skip empty lines and script-specific code
            if not line.strip() or line.startswith(('if', 'then', 'else', 'fi', 'function')):
                continue
            
            # Extract commands and their comments
            if line.strip().startswith('#'):
                commands.append(line.strip())
            elif 'python' in line or './' in line or any(cmd in line for cmd in ['tail', 'ps', 'rm', 'tar']):
                commands.append(line.strip())
    
    return commands

def get_command_sections() -> Dict[str, List[str]]:
    """Organize commands into sections based on their purpose."""
    sections = {
        'System Control': [],
        'Development': [],
        'Monitoring': [],
        'Configuration': [],
        'Troubleshooting': []
    }
    
    # Extract commands from shell scripts
    script_files = {
        'System Control': ['start_all.sh', 'stop_all.sh'],
        'Development': ['run_tests.sh', 'setup_dev.sh'],
    }
    
    for section, files in script_files.items():
        for script in files:
            if os.path.exists(script):
                sections[section].extend(extract_commands_from_script(script))
    
    # Add common monitoring commands
    sections['Monitoring'] = [
        '# Check component status',
        'ps aux | grep "python.*main.py"',
        'ps aux | grep "python.*mt_api_bridge.py"',
        'ps aux | grep "python.*dashboard.py"',
        '# View logs',
        'tail -f logs/trading_bot.out',
        'tail -f logs/mt_api_bridge.out',
        'tail -f logs/dashboard.out'
    ]
    
    # Add configuration commands
    sections['Configuration'] = [
        '# Edit main configuration',
        'nano config.py',
        '# Edit logging configuration',
        'nano logging.conf'
    ]
    
    # Add troubleshooting commands
    sections['Troubleshooting'] = [
        '# Force stop components',
        'pkill -9 -f "python.*main.py"',
        'pkill -9 -f "python.*mt_api_bridge.py"',
        'pkill -9 -f "python.*dashboard.py"',
        '# Clear process IDs',
        'rm -f *.pid',
        '# Check system resources',
        'top -u $USER'
    ]
    
    return sections

def update_readme_commands(readme_path: str = 'README.md'):
    """Update the Command Line Reference section in README.md"""
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Generate new command line reference section
    sections = get_command_sections()
    new_section = "\n## Command Line Reference\n\n"
    
    for section_name, commands in sections.items():
        if commands:
            new_section += f"### {section_name} Commands\n\n"
            new_section += "```bash\n"
            for cmd in commands:
                new_section += f"{cmd}\n"
            new_section += "```\n\n"
    
    new_section += "> **Note**: All commands should be run from the project root directory.\n"
    
    # Replace existing command line section or append to end
    cmd_section_pattern = r"## Command Line Reference.*?(?=##|\Z)"
    if re.search(cmd_section_pattern, content, re.DOTALL):
        content = re.sub(cmd_section_pattern, new_section, content, flags=re.DOTALL)
    else:
        content += "\n" + new_section
    
    # Write updated content back to README
    with open(readme_path, 'w') as f:
        f.write(content)

def main():
    """Main function to update README documentation."""
    # Ensure we're in the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Update README
    update_readme_commands()
    print("✅ README.md command line documentation has been updated successfully!")

if __name__ == '__main__':
    main() 