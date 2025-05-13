import unittest, io, sys
from sona.interpreter import SonaInterpreter, capture

class TestCore(unittest.TestCase):
    def setUp(self):
        self.interp = SonaInterpreter()

    def capture(self, code):
        buf = io.StringIO()
        old = sys.stdout; sys.stdout = buf
        capture(self.interp, code)
        sys.stdout = old
        return buf.getvalue()

    def test_print_and_arith(self):
        out = self.capture('let x = 2 + 3\nprint(x)')
        self.assertIn("5.0", out)

    def test_if_else(self):
        out = self.run_code("if 1 < 2 { print(\"yes\") }")
        self.assertIn("yes", out)

if __name__ == "__main__":
    unittest.main()
