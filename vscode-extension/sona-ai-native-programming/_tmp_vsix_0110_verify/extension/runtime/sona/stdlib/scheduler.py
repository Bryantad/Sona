"""
scheduler - Task scheduling utilities for Sona stdlib

Provides utilities for scheduling and running periodic tasks:
- every: Schedule a function to run at regular intervals
- run_pending: Execute all pending scheduled tasks
- Supports cron-style specifications and delay-based scheduling
"""

import time
import datetime
import re
from typing import Callable, Optional, List


class Job:
    """Represents a scheduled job."""
    
    def __init__(self, fn: Callable, interval: Optional[int] = None, cron: Optional[str] = None):
        """
        Create a new scheduled job.
        
        Args:
            fn: Function to execute
            interval: Interval in seconds (for delay-based scheduling)
            cron: Cron expression (for cron-style scheduling)
        """
        self.fn = fn
        self.interval = interval
        self.cron = cron
        self.last_run = None
        self.next_run = None
        
        if cron:
            self._calculate_next_cron_run()
        elif interval:
            self.next_run = time.time() + interval
    
    def _calculate_next_cron_run(self):
        """Calculate next run time based on cron expression."""
        # Simple cron parser for basic patterns like "*/5 * * * *"
        # Format: minute hour day month weekday
        
        if not self.cron:
            return
        
        parts = self.cron.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {self.cron}")
        
        minute, hour, day, month, weekday = parts
        
        now = datetime.datetime.now()
        
        # Handle */N pattern for minutes
        if minute.startswith('*/'):
            interval_minutes = int(minute[2:])
            next_minute = ((now.minute // interval_minutes) + 1) * interval_minutes
            
            if next_minute >= 60:
                next_run = now.replace(minute=0, second=0, microsecond=0)
                next_run += datetime.timedelta(hours=1)
            else:
                next_run = now.replace(minute=next_minute, second=0, microsecond=0)
            
            self.next_run = next_run.timestamp()
        else:
            # For simplicity, treat other patterns as "every minute"
            next_run = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
            self.next_run = next_run.timestamp()
    
    def should_run(self, now: float) -> bool:
        """Check if job should run now."""
        if self.next_run is None:
            return False
        return now >= self.next_run
    
    def run(self):
        """Execute the job."""
        self.last_run = time.time()
        self.fn()
        
        # Schedule next run
        if self.cron:
            self._calculate_next_cron_run()
        elif self.interval:
            self.next_run = time.time() + self.interval


# Global job registry
_jobs: List[Job] = []


def every(spec: str, fn: Callable):
    """
    Schedule a function to run at regular intervals.
    
    Args:
        spec: Schedule specification:
            - Delay format: "10s", "5m", "1h", "2d"
            - Cron format: "@cron(*/5 * * * *)"
        fn: Function to execute
    
    Returns:
        Job instance
    
    Example:
        # Run every 10 seconds
        scheduler.every("10s", lambda: print("Hello"))
        
        # Run every 5 minutes (cron)
        scheduler.every("@cron(*/5 * * * *)", cleanup_task)
        
        # Run every hour
        scheduler.every("1h", backup_data)
    """
    # Parse spec
    if spec.startswith('@cron(') and spec.endswith(')'):
        # Cron-style scheduling
        cron_expr = spec[6:-1]  # Extract cron expression
        job = Job(fn, cron=cron_expr)
    else:
        # Delay-based scheduling
        interval = _parse_delay(spec)
        job = Job(fn, interval=interval)
    
    _jobs.append(job)
    return job


def _parse_delay(spec: str) -> int:
    """
    Parse delay specification into seconds.
    
    Args:
        spec: Delay spec like "10s", "5m", "1h", "2d"
    
    Returns:
        Interval in seconds
    """
    match = re.match(r'^(\d+)([smhd])$', spec)
    if not match:
        raise ValueError(f"Invalid delay spec: {spec}")
    
    value, unit = match.groups()
    value = int(value)
    
    units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    
    return value * units[unit]


def run_pending(now: Optional[float] = None):
    """
    Execute all pending scheduled tasks.
    
    Args:
        now: Current time (for testing; defaults to actual current time)
    
    Returns:
        Number of jobs executed
    
    Example:
        # Main loop
        while True:
            scheduler.run_pending()
            time.sleep(1)
    """
    if now is None:
        now = time.time()
    
    executed = 0
    
    for job in _jobs:
        if job.should_run(now):
            job.run()
            executed += 1
    
    return executed


def clear_jobs():
    """
    Clear all scheduled jobs.
    
    Example:
        scheduler.clear_jobs()
    """
    global _jobs
    _jobs = []


def get_jobs() -> List[Job]:
    """
    Get list of all scheduled jobs.
    
    Returns:
        List of Job instances
    
    Example:
        jobs = scheduler.get_jobs()
        print(f"Scheduled jobs: {len(jobs)}")
    """
    return list(_jobs)


def once(delay: str, fn: Callable):
    """
    Schedule a function to run once after delay.
    
    Args:
        delay: Delay string (e.g., "5s", "2m", "1h")
        fn: Function to execute
    
    Returns:
        Job instance
    
    Example:
        scheduler.once("10s", lambda: print("Delayed!"))
    """
    seconds = _parse_delay(delay)
    
    def run_once():
        fn()
        # Remove job after execution
        if job in _jobs:
            _jobs.remove(job)
    
    job = Job(run_once, interval=seconds)
    _jobs.append(job)
    return job


def cancel(job: Job):
    """
    Cancel a scheduled job.
    
    Args:
        job: Job instance to cancel
    
    Returns:
        True if cancelled
    
    Example:
        job = scheduler.every("1m", task)
        scheduler.cancel(job)
    """
    if job in _jobs:
        _jobs.remove(job)
        return True
    return False


def run_continuously(interval: float = 1.0):
    """
    Run scheduler continuously in background thread.
    
    Args:
        interval: Check interval in seconds
    
    Returns:
        Thread object
    
    Example:
        thread = scheduler.run_continuously()
        # Jobs will run automatically
        thread.join()
    """
    import threading
    
    def run_loop():
        while True:
            run_pending()
            time.sleep(interval)
    
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    return thread


def at_time(hour: int, minute: int, fn: Callable):
    """
    Schedule function to run daily at specific time.
    
    Args:
        hour: Hour (0-23)
        minute: Minute (0-59)
        fn: Function to execute
    
    Returns:
        Job instance
    
    Example:
        scheduler.at_time(14, 30, daily_report)  # 2:30 PM daily
    """
    cron = f"{minute} {hour} * * *"
    job = Job(fn, cron=cron)
    _jobs.append(job)
    return job


def next_run_time(job: Job) -> Optional[str]:
    """
    Get next run time for a job.
    
    Args:
        job: Job instance
    
    Returns:
        ISO datetime string or None
    
    Example:
        time = scheduler.next_run_time(job)
    """
    if job.next_run is None:
        return None
    dt = datetime.datetime.fromtimestamp(job.next_run)
    return dt.isoformat()


__all__ = [
    'Job',
    'every',
    'run_pending',
    'clear_jobs',
    'get_jobs',
    'once',
    'cancel',
    'run_continuously',
    'at_time',
    'next_run_time'
]
