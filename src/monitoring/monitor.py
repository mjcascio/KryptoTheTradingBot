import psutil
import json
import argparse
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self):
        self.pid_file = "bot.pid"
        
    def get_bot_pid(self):
        try:
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        except FileNotFoundError:
            return None
            
    def is_bot_running(self):
        pid = self.get_bot_pid()
        if pid is None:
            return False
        try:
            process = psutil.Process(pid)
            return process.is_running() and "python" in process.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
            
    def get_system_metrics(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "error": "Failed to get system metrics",
                "timestamp": datetime.now().isoformat()
            }
        
    def get_bot_metrics(self):
        pid = self.get_bot_pid()
        if not pid:
            return {"status": "not_running"}
            
        try:
            process = psutil.Process(pid)
            return {
                "status": "running",
                "cpu_percent": process.cpu_percent(interval=1),
                "memory_percent": process.memory_percent(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error getting bot metrics: {e}")
            return {"status": "not_running"}
            
    def get_full_status(self):
        return {
            "system": self.get_system_metrics(),
            "bot": self.get_bot_metrics()
        }

def main():
    parser = argparse.ArgumentParser(description='KryptoBot System Monitor')
    parser.add_argument('--status', action='store_true', help='Get current system status')
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    if args.status:
        status = monitor.get_full_status()
        print(json.dumps(status, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 