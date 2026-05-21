"""
test - Test framework for Sona stdlib

Provides testing utilities:
- suite: Create test suite
- run: Run tests
- describe/it: BDD-style testing
"""

import sys
import traceback
import time


__all__ = [
    'TestResult',
    'TestSuite',
    'suite',
    'run',
    'describe',
    'it',
    'run_all',
    'skip',
    'expect_error',
    'parametrize',
    'before_each',
    'after_each'
]


class TestResult:
    """Test result container."""
    
    def __init__(self, name, passed, error=None, duration=0):
        self.name = name
        self.passed = passed
        self.error = error
        self.duration = duration


class TestSuite:
    """Test suite container."""
    
    def __init__(self, name):
        self.name = name
        self.tests = []
        self.results = []
        self.setup_func = None
        self.teardown_func = None
    
    def add_test(self, name, func):
        """Add test to suite."""
        self.tests.append((name, func))
    
    def setup(self, func):
        """Set setup function."""
        self.setup_func = func
    
    def teardown(self, func):
        """Set teardown function."""
        self.teardown_func = func
    
    def run(self):
        """Run all tests in suite."""
        self.results = []
        
        for name, func in self.tests:
            start = time.time()
            
            try:
                # Run setup
                if self.setup_func:
                    self.setup_func()
                
                # Run test
                func()
                
                # Run teardown
                if self.teardown_func:
                    self.teardown_func()
                
                duration = time.time() - start
                self.results.append(TestResult(name, True, duration=duration))
            
            except Exception as e:
                duration = time.time() - start
                error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                self.results.append(TestResult(name, False, error=error, duration=duration))
        
        return self.results
    
    def report(self):
        """Generate test report."""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total_time = sum(r.duration for r in self.results)
        
        report = {
            'suite': self.name,
            'total': len(self.results),
            'passed': passed,
            'failed': failed,
            'duration': total_time,
            'tests': []
        }
        
        for result in self.results:
            report['tests'].append({
                'name': result.name,
                'passed': result.passed,
                'error': result.error,
                'duration': result.duration
            })
        
        return report


def suite(name):
    """
    Create test suite.
    
    Args:
        name: Suite name
    
    Returns:
        TestSuite object
    
    Example:
        s = test.suite("Math Tests")
        s.add_test("addition", test_add)
        results = s.run()
    """
    return TestSuite(name)


def run(suites):
    """
    Run test suites and report results.
    
    Args:
        suites: List of TestSuite objects
    
    Returns:
        Summary report
    
    Example:
        summary = test.run([suite1, suite2])
    """
    all_results = []
    
    for s in suites:
        s.run()
        all_results.append(s.report())
    
    # Generate summary
    total = sum(r['total'] for r in all_results)
    passed = sum(r['passed'] for r in all_results)
    failed = sum(r['failed'] for r in all_results)
    duration = sum(r['duration'] for r in all_results)
    
    return {
        'suites': all_results,
        'summary': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'duration': duration
        }
    }


# Global test registry for BDD-style testing
_current_suite = None
_all_suites = []


def describe(name):
    """
    Create test suite (BDD-style).
    
    Args:
        name: Suite description
    
    Returns:
        TestSuite object
    
    Example:
        suite = test.describe("Calculator")
        # Add tests with it()
    """
    global _current_suite
    _current_suite = TestSuite(name)
    _all_suites.append(_current_suite)
    return _current_suite


def it(description, func):
    """
    Add test case (BDD-style).
    
    Args:
        description: Test description
        func: Test function
    
    Example:
        test.it("should add numbers", test_addition)
    """
    if _current_suite is None:
        raise RuntimeError("Call describe() before it()")
    
    _current_suite.add_test(description, func)


def run_all():
    """
    Run all registered test suites.
    
    Returns:
        Summary report
    
    Example:
        results = test.run_all()
    """
    return run(_all_suites)


def skip(reason=""):
    """
    Skip a test with optional reason.
    
    Args:
        reason: Why test is skipped
    
    Returns:
        Exception to raise
    
    Example:
        raise test.skip("Not implemented yet")
    """
    class SkipTest(Exception):
        pass
    
    exc = SkipTest(reason)
    exc.skip_reason = reason
    return exc


def expect_error(error_type=Exception):
    """
    Context manager to expect an error.
    
    Args:
        error_type: Expected exception type
    
    Returns:
        Context manager
    
    Example:
        with test.expect_error(ValueError):
            int("not a number")
    """
    class ErrorContext:
        def __init__(self):
            self.caught = False
            self.error = None
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(
                    f"Expected {error_type.__name__} but no error raised"
                )
            if not issubclass(exc_type, error_type):
                return False
            self.caught = True
            self.error = exc_val
            return True
    
    return ErrorContext()


def parametrize(params):
    """
    Run test with multiple parameter sets.
    
    Args:
        params: List of parameter tuples
    
    Returns:
        Decorator function
    
    Example:
        @test.parametrize([(1, 2, 3), (2, 3, 5)])
        def test_add(a, b, expected):
            assert a + b == expected
    """
    def decorator(func):
        def wrapper():
            for i, args in enumerate(params):
                try:
                    if isinstance(args, (list, tuple)):
                        func(*args)
                    else:
                        func(args)
                except Exception as e:
                    raise AssertionError(
                        f"Failed on param set {i}: {args}"
                    ) from e
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


def before_each(func):
    """
    Mark function to run before each test.
    
    Args:
        func: Setup function
    
    Returns:
        Same function
    
    Example:
        @test.before_each
        def setup():
            # Setup code
            pass
    """
    if _current_suite:
        _current_suite.setup(func)
    return func


def after_each(func):
    """
    Mark function to run after each test.
    
    Args:
        func: Teardown function
    
    Returns:
        Same function
    
    Example:
        @test.after_each
        def cleanup():
            # Cleanup code
            pass
    """
    if _current_suite:
        _current_suite.teardown(func)
    return func
