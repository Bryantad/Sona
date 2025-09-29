"""Sona standard library: date & time"""

import datetime
from datetime import date, datetime


def today(): """YYYY‑MM‑DD"""
    return datetime.date.today().isoformat()


def now(): """YYYY‑MM‑DDTHH:MM:SS"""
    return datetime.datetime.now().isoformat()


def sleep(seconds): """Pause execution"""
    import time

    time.sleep(seconds)


def utcnow(): return datetime.utcnow().isoformat()


def fromtimestamp(ts): return datetime.fromtimestamp(ts).isoformat()


def strftime(fmt): return datetime.now().strftime(fmt)
