"""Sona standard library: string utilities"""


def upper(s):
    return str(s).upper()


def lower(s):
    return str(s).lower()


def split(s, delim=" "):
    return s.split(delim)


def join(lst, delim=" "):
    return delim.join(lst)


def replace(s, old, new):
    return s.replace(old, new)


def trim(s):
    return s.strip()


def startswith(s, prefix):
    return s.startswith(prefix)


def endswith(s, suffix):
    return s.endswith(suffix)


def capitalize(s):
    return str(s).capitalize()


def title(s):
    return s.title()


def find(s, sub):
    return s.find(sub)  # -1 if not found


def index(s, sub):
    return s.index(sub)  # error if not found


def format(s, *args, **kwargs):
    return s.format(*args, **kwargs)


def length(s):
    return len(s)
