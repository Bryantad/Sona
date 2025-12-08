"""
mock - Mocking utilities for testing in Sona stdlib

Provides test mocking:
- Mock: Mock object
- stub: Create stub function
- spy: Create spy function
"""


class Mock:
    """Mock object for testing."""
    
    def __init__(self, **kwargs):
        """Initialize mock with attributes."""
        self._calls = []
        self._return_value = None
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __call__(self, *args, **kwargs):
        """Record call."""
        self._calls.append({'args': args, 'kwargs': kwargs})
        return self._return_value
    
    def returns(self, value):
        """
        Set return value.
        
        Args:
            value: Value to return
        
        Returns:
            Self for chaining
        
        Example:
            m = mock.Mock()
            m.returns(42)
            result = m()  # Returns 42
        """
        self._return_value = value
        return self
    
    def called(self):
        """
        Check if mock was called.
        
        Returns:
            True if called
        
        Example:
            assert m.called()
        """
        return len(self._calls) > 0
    
    def call_count(self):
        """
        Get number of calls.
        
        Returns:
            Call count
        
        Example:
            assert m.call_count() == 3
        """
        return len(self._calls)
    
    def called_with(self, *args, **kwargs):
        """
        Check if called with specific arguments.
        
        Args:
            args: Expected args
            kwargs: Expected kwargs
        
        Returns:
            True if any call matches
        
        Example:
            m(1, 2, key="value")
            assert m.called_with(1, 2, key="value")
        """
        for call in self._calls:
            if call['args'] == args and call['kwargs'] == kwargs:
                return True
        return False
    
    def reset(self):
        """Reset mock state."""
        self._calls.clear()
    
    def calls(self):
        """
        Get all calls.
        
        Returns:
            List of call dictionaries
        
        Example:
            for call in m.calls():
                print(call['args'], call['kwargs'])
        """
        return self._calls.copy()


class Spy:
    """Spy wraps a function to record calls."""
    
    def __init__(self, func):
        """Initialize spy with function."""
        self._func = func
        self._calls = []
    
    def __call__(self, *args, **kwargs):
        """Call function and record."""
        self._calls.append({'args': args, 'kwargs': kwargs})
        return self._func(*args, **kwargs)
    
    def called(self):
        """Check if called."""
        return len(self._calls) > 0
    
    def call_count(self):
        """Get call count."""
        return len(self._calls)
    
    def called_with(self, *args, **kwargs):
        """Check if called with args."""
        for call in self._calls:
            if call['args'] == args and call['kwargs'] == kwargs:
                return True
        return False
    
    def calls(self):
        """Get all calls."""
        return self._calls.copy()
    
    def reset(self):
        """Reset spy state."""
        self._calls.clear()


def create(**kwargs):
    """
    Create mock object.
    
    Args:
        kwargs: Mock attributes
    
    Returns:
        Mock object
    
    Example:
        m = mock.create(name="John", age=30)
        print(m.name)  # "John"
    """
    return Mock(**kwargs)


def spy(func):
    """
    Create spy wrapping function.
    
    Args:
        func: Function to spy on
    
    Returns:
        Spy object
    
    Example:
        add_spy = mock.spy(add)
        result = add_spy(1, 2)
        assert add_spy.called()
    """
    return Spy(func)


def stub(return_value=None):
    """
    Create stub function.
    
    Args:
        return_value: Value to return
    
    Returns:
        Mock object configured as stub
    
    Example:
        get_user = mock.stub({"name": "John"})
        user = get_user()  # Returns {"name": "John"}
    """
    return Mock().returns(return_value)


def patch(obj, attr_name, mock_value):
    """
    Context manager to temporarily patch an attribute.
    
    Args:
        obj: Object to patch
        attr_name: Attribute name
        mock_value: Mock value
    
    Returns:
        Context manager
    
    Example:
        with mock.patch(config, 'debug', True):
            # config.debug is True here
            pass
        # config.debug restored
    """
    class PatchContext:
        def __init__(self):
            self.original = None
        
        def __enter__(self):
            self.original = getattr(obj, attr_name, None)
            setattr(obj, attr_name, mock_value)
            return mock_value
        
        def __exit__(self, *args):
            if self.original is not None:
                setattr(obj, attr_name, self.original)
            elif hasattr(obj, attr_name):
                delattr(obj, attr_name)
    
    return PatchContext()


def verify_called(mock_obj, times=None):
    """
    Verify mock was called expected number of times.
    
    Args:
        mock_obj: Mock or Spy object
        times: Expected call count (None = at least once)
    
    Raises:
        AssertionError if verification fails
    
    Example:
        mock.verify_called(m, times=3)
    """
    count = mock_obj.call_count()
    
    if times is None:
        if count == 0:
            raise AssertionError("Mock was not called")
    elif count != times:
        raise AssertionError(
            f"Expected {times} calls, got {count}"
        )


def verify_never_called(mock_obj):
    """
    Verify mock was never called.
    
    Args:
        mock_obj: Mock or Spy object
    
    Raises:
        AssertionError if was called
    
    Example:
        mock.verify_never_called(m)
    """
    count = mock_obj.call_count()
    if count > 0:
        raise AssertionError(f"Expected 0 calls, got {count}")


def fake_function(*return_values):
    """
    Create function that returns sequence of values.
    
    Args:
        return_values: Values to return on successive calls
    
    Returns:
        Function that cycles through return values
    
    Example:
        f = mock.fake_function(1, 2, 3)
        f()  # 1
        f()  # 2
        f()  # 3
        f()  # Repeats from 1
    """
    index = [0]
    values = list(return_values)
    
    def _fake(*args, **kwargs):
        result = values[index[0] % len(values)]
        index[0] += 1
        return result
    
    return _fake


__all__ = [
    'Mock',
    'Spy',
    'create',
    'spy',
    'stub',
    'patch',
    'verify_called',
    'verify_never_called',
    'fake_function'
]
