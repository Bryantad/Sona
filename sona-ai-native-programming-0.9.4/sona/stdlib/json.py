from . import native_json


def dumps(obj):
    return native_json.json_dumps(obj)


def loads(text):
    return native_json.json_loads(text)
