from . import native_time

def now():
    return native_time.time_now()
    return str(datetime.now())

def sleep(seconds):
    return native_time.time_sleep(seconds)
