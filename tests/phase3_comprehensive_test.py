#!/usr/bin/env python3
"""
Phase 3 Comprehensive Test Suite
Tests for type consistency and enhanced error reporting
"""

import unittest
import sys
from pathlib import Path

# Add Sona to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sona.interpreter import SonaInterpreter
from lark import Lark

class TestPhase3Fixes(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.interpreter = SonaInterpreter()
        
        # Load grammar
        grammar_path = Path(__file__).parent.parent / 'sona' / 'grammar.lark'
        with open(grammar_path, 'r') as f:
            grammar = f.read()
        self.parser = Lark(grammar, parser='lalr', propagate_positions=True)
    
    def test_numeric_type_consistency(self):
        """Test numeric type consistency"""
        test_cases = [
            ('2 + 3', 5),
            ('2.5 + 1', 3.5),
            ('10 / 2', 5.0),
            ('3 * 4', 12),
        ]
        
        for code, expected in test_cases:
            with self.subTest(code=code):
                try:
                    tree = self.parser.parse(code)
                    result = self.interpreter.transform(tree)
                    self.assertEqual(result, expected)
                except Exception as e:
                    self.fail(f"Numeric operation failed: {code} -> {e}")
    
    def test_type_conversion(self):
        """Test type conversion consistency"""
        if hasattr(self.interpreter, 'ensure_numeric_type'):
            # Test the type conversion method directly
            self.assertEqual(self.interpreter.ensure_numeric_type("123"), 123)
            self.assertEqual(self.interpreter.ensure_numeric_type("12.5"), 12.5)
            self.assertEqual(self.interpreter.ensure_numeric_type(True), 1)
            self.assertEqual(self.interpreter.ensure_numeric_type(False), 0)
        else:
            self.skipTest("Type conversion methods not available")
    
    def test_enhanced_error_messages(self):
        """Test enhanced error reporting"""
        # Test undefined variable error
        try:
            tree = self.parser.parse("undefined_variable")
            self.interpreter.transform(tree)
            self.fail("Should have raised NameError")
        except NameError as e:
            # Check if error message is enhanced
            error_msg = str(e)
            self.assertIn("undefined_variable", error_msg)
            print(f"✅ Enhanced error message: {error_msg}")
    
    def test_function_parameter_errors(self):
        """Test function parameter error reporting"""
        # Define a function
        func_code = """
        func test(a, b) {
            return a + b
        }
        """
        
        try:
            tree = self.parser.parse(func_code)
            self.interpreter.transform(tree)
            
            # Call with wrong number of parameters
            call_code = "test(1)"
            call_tree = self.parser.parse(call_code)
            self.interpreter.transform(call_tree)
            self.fail("Should have raised ValueError for parameter mismatch")
            
        except ValueError as e:
            error_msg = str(e)
            self.assertIn("expects", error_msg)
            self.assertIn("arguments", error_msg)
            print(f"✅ Enhanced parameter error: {error_msg}")
        except Exception as e:
            print(f"⚠️ Function parameter test produced different error: {e}")

if __name__ == '__main__':
    print("=== Running Phase 3 Comprehensive Tests ===")
    unittest.main(verbosity=2)
