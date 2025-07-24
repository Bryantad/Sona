# filepath: /Volumes/project usb/WayCore Inc/sona_core/sona/stdlib/native_file.py


def read(path): try: with open(path, 'r') as file: return file.read()
    except Exception as e: return f"[file error] {e}"
