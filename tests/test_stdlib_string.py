import unittest
import stdlib.string as s

class TestString(unittest.TestCase):
    def test_upper(self):
        self.assertEqual(s.upper("hi"), "HI")

    def test_split(self):
        self.assertEqual(s.split("a b c"), ["a","b","c"])

if __name__ == '__main__':
    unittest.main()
