import time
from datetime import datetime


def time_now(): return datetime.now().isoformat()


def time_sleep(seconds): time.sleep(float(seconds))
    return None
