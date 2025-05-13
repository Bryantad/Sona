# sona/stdlib/native_stdin.py
# This file is part of the Sona programming language.
class NativeStdin:
    @staticmethod
    def input(prompt=""):
        return input(prompt)

native_stdin = NativeStdin()

native_stdin = NativeStdin()
def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(content))

def append(path, content):
    with open(path, "a", encoding="utf-8") as f:
        f.write(str(content))
