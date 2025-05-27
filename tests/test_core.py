import unittest
from io import StringIO
from contextlib import redirect_stdout

from sona.interpreter import SonaInterpreter, capture

class TestCore(unittest.TestCase):
    def capture(self, code: str):
        """
        Helper to run a snippet and capture printed output.
        Returns (success, stdout, interpreter).
        """
        interp = SonaInterpreter()
        buf = StringIO()
        with redirect_stdout(buf):
            ok = capture(interp, code)
        return ok, buf.getvalue(), interp

    def test_variable_declaration(self):
        ok, out, interp = self.capture("let x = 42")
        self.assertTrue(ok)
        self.assertEqual(interp.get_var("x"), 42)

    def test_const_declaration(self):
        ok, out, interp = self.capture("const y = 3.14")
        self.assertTrue(ok)
        self.assertEqual(interp.get_var("y"), 3.14)
        # Test that reassignment should fail
        ok2, out2, interp2 = self.capture("const y = 3.14\ny = 2")
        self.assertFalse(ok2)  # Should fail on reassignment

    def test_arithmetic_and_print(self):
        ok, out, _ = self.capture('print(2 * (3 + 4))')
        self.assertTrue(ok)
        self.assertIn("14", out)

    def test_comparison_and_if(self):
        code = """
        let a = 5
        let b = 0
        if a > 3 { b = 99 } else { b = 0 }
        """
        ok, out, interp = self.capture(code)
        self.assertTrue(ok)
        self.assertEqual(interp.get_var("b"), 99)

    def test_while_loop(self):
        code = """
        let i = 0
        while i < 3 { i = i + 1 }
        """
        ok, out, interp = self.capture(code)
        self.assertTrue(ok)
        self.assertEqual(interp.get_var("i"), 3)

    def test_for_loop(self):
        code = """
        let sum = 0
        for n in 1..4 { sum = sum + n }
        """
        ok, out, interp = self.capture(code)
        self.assertTrue(ok)
        # 1 + 2 + 3 + 4 == 10
        self.assertEqual(interp.get_var("sum"), 10)

    def test_function_definition_and_call(self):
        code = """
        func square(x) { return x * x }
        let result = square(6)
        """
        ok, out, interp = self.capture(code)
        self.assertTrue(ok)
        self.assertEqual(interp.get_var("result"), 36)

if __name__ == "__main__":
    unittest.main()
