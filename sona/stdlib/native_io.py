def input(prompt="Enter input: "):
    return __builtins__.input(prompt)

def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))
        return True
    except Exception as e:
        return f"[io error] {e}"

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[io error] {e}"

# stdin functions clearly separated
def stdin_input(prompt=""):
    return input(prompt)

def stdin_read():
    return input()

def stdin_write_file(path, content):    
    return write_file(path, content)

def stdin_read_file(path):
    return read_file(path)

def stdin_write(path, content):
    return write_file(path, content)

def stdin_append(path, content):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(content))
        return True
    except Exception as e:
        return f"[io error] {e}"
