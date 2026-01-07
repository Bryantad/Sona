"""
assert - Rich assertions for Sona stdlib

Provides assertion functions:
- equal: Assert equality
- not_equal: Assert inequality
- true/false: Assert boolean
- raises: Assert exception
"""


class AssertionError(Exception):
    """Assertion failure exception."""
    pass


def equal(actual, expected, message=None):
    """
    Assert values are equal.
    
    Args:
        actual: Actual value
        expected: Expected value
        message: Optional error message
    
    Raises:
        AssertionError if not equal
    
    Example:
        assert.equal(result, 42)
    """
    if actual != expected:
        msg = message or f"Expected {expected}, got {actual}"
        raise AssertionError(msg)


def not_equal(actual, expected, message=None):
    """
    Assert values are not equal.
    
    Args:
        actual: Actual value
        expected: Value that should differ
        message: Optional error message
    
    Raises:
        AssertionError if equal
    
    Example:
        assert.not_equal(result, 0)
    """
    if actual == expected:
        msg = message or f"Expected value different from {expected}"
        raise AssertionError(msg)


def true(value, message=None):
    """
    Assert value is true.
    
    Args:
        value: Value to check
        message: Optional error message
    
    Raises:
        AssertionError if not true
    
    Example:
        assert.true(is_valid)
    """
    if not value:
        msg = message or f"Expected true, got {value}"
        raise AssertionError(msg)


def false(value, message=None):
    """
    Assert value is false.
    
    Args:
        value: Value to check
        message: Optional error message
    
    Raises:
        AssertionError if not false
    
    Example:
        assert.false(has_error)
    """
    if value:
        msg = message or f"Expected false, got {value}"
        raise AssertionError(msg)


def none(value, message=None):
    """
    Assert value is None.
    
    Args:
        value: Value to check
        message: Optional error message
    
    Raises:
        AssertionError if not None
    
    Example:
        assert.none(optional_value)
    """
    if value is not None:
        msg = message or f"Expected None, got {value}"
        raise AssertionError(msg)


def not_none(value, message=None):
    """
    Assert value is not None.
    
    Args:
        value: Value to check
        message: Optional error message
    
    Raises:
        AssertionError if None
    
    Example:
        assert.not_none(result)
    """
    if value is None:
        msg = message or "Expected non-None value"
        raise AssertionError(msg)


def contains(collection, item, message=None):
    """
    Assert collection contains item.
    
    Args:
        collection: Collection to check
        item: Item to find
        message: Optional error message
    
    Raises:
        AssertionError if not found
    
    Example:
        assert.contains(results, expected_item)
    """
    if item not in collection:
        msg = message or f"Expected {item} in {collection}"
        raise AssertionError(msg)


def not_contains(collection, item, message=None):
    """
    Assert collection does not contain item.
    
    Args:
        collection: Collection to check
        item: Item that should not be present
        message: Optional error message
    
    Raises:
        AssertionError if found
    
    Example:
        assert.not_contains(errors, "critical")
    """
    if item in collection:
        msg = message or f"Expected {item} not in {collection}"
        raise AssertionError(msg)


def raises(func, exception_type=Exception, message=None):
    """
    Assert function raises exception.
    
    Args:
        func: Function to call
        exception_type: Expected exception type
        message: Optional error message
    
    Raises:
        AssertionError if exception not raised
    
    Example:
        assert.raises(lambda: divide(1, 0), ZeroDivisionError)
    """
    try:
        func()
        msg = message or f"Expected {exception_type.__name__} to be raised"
        raise AssertionError(msg)
    except exception_type:
        pass  # Expected
    except Exception as e:
        msg = message or f"Expected {exception_type.__name__}, got {type(e).__name__}"
        raise AssertionError(msg)


def greater(actual, threshold, message=None):
    """
    Assert value is greater than threshold.
    
    Args:
        actual: Actual value
        threshold: Minimum value (exclusive)
        message: Optional error message
    
    Raises:
        AssertionError if not greater
    
    Example:
        assert.greater(score, 50)
    """
    if actual <= threshold:
        msg = message or f"Expected {actual} > {threshold}"
        raise AssertionError(msg)


def less(actual, threshold, message=None):
    """
    Assert value is less than threshold.
    
    Args:
        actual: Actual value
        threshold: Maximum value (exclusive)
        message: Optional error message
    
    Raises:
        AssertionError if not less
    
    Example:
        assert.less(error_rate, 0.01)
    """
    if actual >= threshold:
        msg = message or f"Expected {actual} < {threshold}"
        raise AssertionError(msg)


def between(actual, min_val, max_val, message=None):
    """
    Assert value is between min and max (inclusive).
    
    Args:
        actual: Actual value
        min_val: Minimum value
        max_val: Maximum value
        message: Optional error message
    
    Raises:
        AssertionError if outside range
    
    Example:
        assert.between(temperature, 20, 30)
    """
    if not (min_val <= actual <= max_val):
        msg = message or f"Expected {actual} between {min_val} and {max_val}"
        raise AssertionError(msg)


def type_of(value, expected_type, message=None):
    """
    Assert value is of expected type.
    
    Args:
        value: Value to check
        expected_type: Expected type
        message: Optional error message
    
    Raises:
        AssertionError if wrong type
    
    Example:
        assert.type_of(result, dict)
    """
    if not isinstance(value, expected_type):
        msg = message or f"Expected {expected_type.__name__}, got {type(value).__name__}"
        raise AssertionError(msg)


def length(collection, expected_length, message=None):
    """
    Assert collection has expected length.
    
    Args:
        collection: Collection to check
        expected_length: Expected length
        message: Optional error message
    
    Raises:
        AssertionError if wrong length
    
    Example:
        assert.length(items, 5)
    """
    actual_length = len(collection)
    if actual_length != expected_length:
        msg = message or f"Expected length {expected_length}, got {actual_length}"
        raise AssertionError(msg)


def empty(collection, message=None):
    """
    Assert collection is empty.
    
    Args:
        collection: Collection to check
        message: Optional error message
    
    Raises:
        AssertionError if not empty
    
    Example:
        assert.empty(errors)
    """
    if collection:
        msg = message or f"Expected empty collection, got {len(collection)} items"
        raise AssertionError(msg)


def not_empty(collection, message=None):
    """
    Assert collection is not empty.
    
    Args:
        collection: Collection to check
        message: Optional error message
    
    Raises:
        AssertionError if empty
    
    Example:
        assert.not_empty(results)
    """
    if not collection:
        msg = message or "Expected non-empty collection"
        raise AssertionError(msg)


def matches(text, pattern, message=None):
    """
    Assert text matches regex pattern.
    
    Args:
        text: Text to check
        pattern: Regex pattern
        message: Optional error message
    
    Raises:
        AssertionError if no match
    
    Example:
        assert.matches(email, r"^[a-z]+@[a-z]+\\.[a-z]+$")
    """
    import re
    if not re.search(pattern, str(text)):
        msg = message or f"Text '{text}' does not match pattern '{pattern}'"
        raise AssertionError(msg)


def starts_with(text, prefix, message=None):
    """
    Assert text starts with prefix.
    
    Args:
        text: Text to check
        prefix: Expected prefix
        message: Optional error message
    
    Raises:
        AssertionError if not starts with
    
    Example:
        assert.starts_with(path, "/home/")
    """
    text_str = str(text)
    if not text_str.startswith(prefix):
        msg = message or f"'{text}' does not start with '{prefix}'"
        raise AssertionError(msg)


def ends_with(text, suffix, message=None):
    """
    Assert text ends with suffix.
    
    Args:
        text: Text to check
        suffix: Expected suffix
        message: Optional error message
    
    Raises:
        AssertionError if not ends with
    
    Example:
        assert.ends_with(filename, ".txt")
    """
    text_str = str(text)
    if not text_str.endswith(suffix):
        msg = message or f"'{text}' does not end with '{suffix}'"
        raise AssertionError(msg)


__all__ = [
    'AssertionError',
    'equal',
    'not_equal',
    'true',
    'false',
    'none',
    'not_none',
    'contains',
    'not_contains',
    'raises',
    'greater',
    'less',
    'between',
    'type_of',
    'length',
    'empty',
    'not_empty',
    'matches',
    'starts_with',
    'ends_with'
]
