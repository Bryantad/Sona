# Sona Enhanced Time Module - Advanced timing and scheduling
# Provides comprehensive time handling capabilities for Sona applications

import time
import threading
from datetime import datetime, timedelta
import calendar

class SonaTimeModule:
    """Enhanced time module for Sona applications"""
    
    def __init__(self):
        self.timers = {}
        self.timer_counter = 0
        self.intervals = {}
        self.interval_counter = 0
    
    # Basic time functions
    def now(self):
        """Get current timestamp as ISO string"""
        return datetime.now().isoformat()
    
    def timestamp(self):
        """Get current Unix timestamp"""
        return time.time()
    
    def sleep(self, seconds):
        """Sleep for specified seconds"""
        time.sleep(float(seconds))
    
    def milliseconds(self):
        """Get current time in milliseconds"""
        return int(time.time() * 1000)
    
    # Date/time formatting
    def format_time(self, timestamp=None, format_str="%Y-%m-%d %H:%M:%S"):
        """Format timestamp using custom format string"""
        try:
            if timestamp is None:
                dt = datetime.now()
            elif isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromtimestamp(float(timestamp))
            
            return dt.strftime(format_str)
        except Exception as e:
            print(f"Error formatting time: {e}")
            return ""
    
    def parse_time(self, time_string, format_str="%Y-%m-%d %H:%M:%S"):
        """Parse time string using format"""
        try:
            dt = datetime.strptime(time_string, format_str)
            return dt.timestamp()
        except Exception as e:
            print(f"Error parsing time: {e}")
            return None

# Create the module instance
time_sona = SonaTimeModule()

# Export for compatibility
__all__ = ['time_sona']
