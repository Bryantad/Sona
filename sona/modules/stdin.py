import sys
import time
import select

class StdinModule:
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        if self.is_windows:
            import msvcrt
        else:
            import termios
            import tty
            self.original_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

    def read_key(self, timeout_ms: int) -> str:
        if self.is_windows:
            import msvcrt
            start = time.time()
            while (time.time() - start) * 1000 < timeout_ms:
                if msvcrt.kbhit():
                    return msvcrt.getwch()
                time.sleep(0.01)
            return ""
        else:
            if select.select([sys.stdin], [], [], timeout_ms/1000.0)[0]:
                return sys.stdin.read(1)
            return ""

    def cleanup(self):
        if not self.is_windows:
            import termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)