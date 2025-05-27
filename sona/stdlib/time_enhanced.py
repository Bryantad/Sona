# Sona Enhanced Time Module - Extended timing capabilities
# Provides comprehensive time handling for Sona applications

import time
import datetime
import threading
from typing import Dict, Any, Optional, Callable

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
        return datetime.datetime.now().isoformat()
    
    def now_unix(self):
        """Get current Unix timestamp"""
        return time.time()
    
    def sleep(self, seconds):
        """Sleep for specified seconds"""
        time.sleep(float(seconds))
        return None
    
    def get_year(self):
        """Get current year"""
        return datetime.datetime.now().year
    
    def get_month(self):
        """Get current month (1-12)"""
        return datetime.datetime.now().month
    
    def get_day(self):
        """Get current day of month"""
        return datetime.datetime.now().day
    
    def get_hour(self):
        """Get current hour (0-23)"""
        return datetime.datetime.now().hour
    
    def get_minute(self):
        """Get current minute (0-59)"""
        return datetime.datetime.now().minute
    
    def get_second(self):
        """Get current second (0-59)"""
        return datetime.datetime.now().second
    
    def get_weekday(self):
        """Get current weekday (0=Monday, 6=Sunday)"""
        return datetime.datetime.now().weekday()
    
    def get_day_of_year(self):
        """Get current day of year (1-366)"""
        return datetime.datetime.now().timetuple().tm_yday
    
    # Date/time formatting
    def format_time(self, format_string="%Y-%m-%d %H:%M:%S"):
        """Format current time using format string"""
        return datetime.datetime.now().strftime(format_string)
    
    def format_timestamp(self, timestamp, format_string="%Y-%m-%d %H:%M:%S"):
        """Format Unix timestamp using format string"""
        try:
            dt = datetime.datetime.fromtimestamp(float(timestamp))
            return dt.strftime(format_string)
        except Exception as e:
            print(f"Error formatting timestamp: {e}")
            return None
    
    def parse_time(self, time_string, format_string="%Y-%m-%d %H:%M:%S"):
        """Parse time string and return Unix timestamp"""
        try:
            dt = datetime.datetime.strptime(time_string, format_string)
            return dt.timestamp()
        except Exception as e:
            print(f"Error parsing time: {e}")
            return None
    
    # Date arithmetic
    def add_days(self, days, timestamp=None):
        """Add days to timestamp (or current time)"""
        try:
            if timestamp is None:
                dt = datetime.datetime.now()
            else:
                dt = datetime.datetime.fromtimestamp(float(timestamp))
            
            new_dt = dt + datetime.timedelta(days=float(days))
            return new_dt.timestamp()
        except Exception as e:
            print(f"Error adding days: {e}")
            return None
    
    def add_hours(self, hours, timestamp=None):
        """Add hours to timestamp (or current time)"""
        try:
            if timestamp is None:
                dt = datetime.datetime.now()
            else:
                dt = datetime.datetime.fromtimestamp(float(timestamp))
            
            new_dt = dt + datetime.timedelta(hours=float(hours))
            return new_dt.timestamp()
        except Exception as e:
            print(f"Error adding hours: {e}")
            return None
    
    def add_minutes(self, minutes, timestamp=None):
        """Add minutes to timestamp (or current time)"""
        try:
            if timestamp is None:
                dt = datetime.datetime.now()
            else:
                dt = datetime.datetime.fromtimestamp(float(timestamp))
            
            new_dt = dt + datetime.timedelta(minutes=float(minutes))
            return new_dt.timestamp()
        except Exception as e:
            print(f"Error adding minutes: {e}")
            return None
    
    def diff_seconds(self, timestamp1, timestamp2):
        """Get difference in seconds between two timestamps"""
        try:
            return float(timestamp2) - float(timestamp1)
        except Exception as e:
            print(f"Error calculating time difference: {e}")
            return None
    
    def diff_days(self, timestamp1, timestamp2):
        """Get difference in days between two timestamps"""
        try:
            diff_sec = float(timestamp2) - float(timestamp1)
            return diff_sec / (24 * 60 * 60)
        except Exception as e:
            print(f"Error calculating day difference: {e}")
            return None
    
    # Performance timing
    def start_timer(self):
        """Start a performance timer and return timer ID"""
        timer_id = f"timer_{self.timer_counter}"
        self.timer_counter += 1
        self.timers[timer_id] = time.perf_counter()
        return timer_id
    
    def end_timer(self, timer_id):
        """End timer and return elapsed seconds"""
        if timer_id in self.timers:
            elapsed = time.perf_counter() - self.timers[timer_id]
            del self.timers[timer_id]
            return elapsed
        return None
    
    def get_timer_elapsed(self, timer_id):
        """Get elapsed time without stopping timer"""
        if timer_id in self.timers:
            return time.perf_counter() - self.timers[timer_id]
        return None
    
    # Interval functions (for repeated callbacks)
    def set_interval(self, callback, interval_seconds):
        """Set up repeated callback every interval_seconds"""
        interval_id = f"interval_{self.interval_counter}"
        self.interval_counter += 1
        
        def interval_worker():
            while interval_id in self.intervals:
                callback()
                time.sleep(float(interval_seconds))
        
        thread = threading.Thread(target=interval_worker, daemon=True)
        self.intervals[interval_id] = {
            'thread': thread,
            'callback': callback,
            'interval': interval_seconds
        }
        thread.start()
        
        return interval_id
    
    def clear_interval(self, interval_id):
        """Stop an interval"""
        if interval_id in self.intervals:
            del self.intervals[interval_id]
            return True
        return False
    
    def set_timeout(self, callback, delay_seconds):
        """Call callback after delay_seconds"""
        def timeout_worker():
            time.sleep(float(delay_seconds))
            callback()
        
        thread = threading.Thread(target=timeout_worker, daemon=True)
        thread.start()
        return True
    
    # Timezone functions
    def get_timezone_name(self):
        """Get current timezone name"""
        try:
            import time
            return time.tzname[0]
        except Exception as e:
            print(f"Error getting timezone: {e}")
            return "Unknown"
    
    def get_utc_now(self):
        """Get current UTC time as ISO string"""
        return datetime.datetime.utcnow().isoformat()
    
    def get_utc_timestamp(self):
        """Get current UTC timestamp"""
        return datetime.datetime.utcnow().timestamp()
    
    def to_utc(self, timestamp):
        """Convert local timestamp to UTC"""
        try:
            local_dt = datetime.datetime.fromtimestamp(float(timestamp))
            utc_dt = local_dt.utctimetuple()
            return time.mktime(utc_dt)
        except Exception as e:
            print(f"Error converting to UTC: {e}")
            return None
    
    # Stopwatch functionality
    def create_stopwatch(self):
        """Create a new stopwatch and return its ID"""
        stopwatch_id = f"stopwatch_{self.timer_counter}"
        self.timer_counter += 1
        self.timers[stopwatch_id] = {
            'start_time': None,
            'total_time': 0.0,
            'running': False
        }
        return stopwatch_id
    
    def start_stopwatch(self, stopwatch_id):
        """Start stopwatch"""
        if stopwatch_id in self.timers and not self.timers[stopwatch_id]['running']:
            self.timers[stopwatch_id]['start_time'] = time.perf_counter()
            self.timers[stopwatch_id]['running'] = True
            return True
        return False
    
    def stop_stopwatch(self, stopwatch_id):
        """Stop stopwatch"""
        if stopwatch_id in self.timers and self.timers[stopwatch_id]['running']:
            elapsed = time.perf_counter() - self.timers[stopwatch_id]['start_time']
            self.timers[stopwatch_id]['total_time'] += elapsed
            self.timers[stopwatch_id]['running'] = False
            return True
        return False
    
    def reset_stopwatch(self, stopwatch_id):
        """Reset stopwatch"""
        if stopwatch_id in self.timers:
            self.timers[stopwatch_id]['total_time'] = 0.0
            self.timers[stopwatch_id]['running'] = False
            self.timers[stopwatch_id]['start_time'] = None
            return True
        return False
    
    def get_stopwatch_time(self, stopwatch_id):
        """Get current stopwatch time"""
        if stopwatch_id in self.timers:
            total = self.timers[stopwatch_id]['total_time']
            if self.timers[stopwatch_id]['running']:
                total += time.perf_counter() - self.timers[stopwatch_id]['start_time']
            return total
        return None
    
    # Utility functions
    def benchmark(self, callback, iterations=1):
        """Benchmark a callback function"""
        try:
            start_time = time.perf_counter()
            for _ in range(int(iterations)):
                callback()
            end_time = time.perf_counter()
            
            total_time = end_time - start_time
            avg_time = total_time / int(iterations)
            
            return {
                'total_time': total_time,
                'average_time': avg_time,
                'iterations': iterations
            }
        except Exception as e:
            print(f"Error benchmarking: {e}")
            return None
    
    def time_function(self, callback):
        """Time a single function call and return result + timing"""
        try:
            start_time = time.perf_counter()
            result = callback()
            end_time = time.perf_counter()
            
            return {
                'result': result,
                'execution_time': end_time - start_time
            }
        except Exception as e:
            print(f"Error timing function: {e}")
            return None
    
    def is_leap_year(self, year=None):
        """Check if year is a leap year"""
        if year is None:
            year = datetime.datetime.now().year
        try:
            year = int(year)
            return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        except Exception as e:
            print(f"Error checking leap year: {e}")
            return False
    
    def days_in_month(self, month=None, year=None):
        """Get number of days in month"""
        if month is None:
            month = datetime.datetime.now().month
        if year is None:
            year = datetime.datetime.now().year
        
        try:
            import calendar
            return calendar.monthrange(int(year), int(month))[1]
        except Exception as e:
            print(f"Error getting days in month: {e}")
            return None

# Create the module instance
time_enhanced = SonaTimeModule()

# Export for compatibility
__all__ = ['time_enhanced']
