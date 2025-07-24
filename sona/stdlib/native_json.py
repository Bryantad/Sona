import json


def json_loads(s): try: return json.loads(s)
    except Exception as e: return f"[json error] {e}"


def json_dumps(obj): try: return json.dumps(obj)
    except Exception as e: return f"[json error] {e}"
