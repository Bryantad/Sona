"""
bitwise - Bitwise operations for Sona stdlib

Provides bitwise utilities:
- and/or/xor: Bitwise operations
- shift_left/shift_right: Bit shifting
- count_bits: Count set bits
"""


def bitwise_and(a, b):
    """
    Bitwise AND operation.
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Result of a & b
    
    Example:
        result = bitwise.and(12, 10)  # 8
    """
    return a & b


def bitwise_or(a, b):
    """
    Bitwise OR operation.
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Result of a | b
    
    Example:
        result = bitwise.or(12, 10)  # 14
    """
    return a | b


def bitwise_xor(a, b):
    """
    Bitwise XOR operation.
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Result of a ^ b
    
    Example:
        result = bitwise.xor(12, 10)  # 6
    """
    return a ^ b


def bitwise_not(a):
    """
    Bitwise NOT operation.
    
    Args:
        a: Integer
    
    Returns:
        Result of ~a
    
    Example:
        result = bitwise.not(12)
    """
    return ~a


def shift_left(a, n):
    """
    Left shift operation.
    
    Args:
        a: Integer
        n: Number of positions
    
    Returns:
        Result of a << n
    
    Example:
        result = bitwise.shift_left(5, 2)  # 20
    """
    return a << n


def shift_right(a, n):
    """
    Right shift operation.
    
    Args:
        a: Integer
        n: Number of positions
    
    Returns:
        Result of a >> n
    
    Example:
        result = bitwise.shift_right(20, 2)  # 5
    """
    return a >> n


def count_bits(n):
    """
    Count set bits (1s) in integer.
    
    Args:
        n: Integer
    
    Returns:
        Number of 1 bits
    
    Example:
        count = bitwise.count_bits(15)  # 4 (binary: 1111)
    """
    count = 0
    while n:
        count += n & 1
        n >>= 1
    return count


def is_power_of_two(n):
    """
    Check if number is power of two.
    
    Args:
        n: Integer
    
    Returns:
        True if power of two
    
    Example:
        bitwise.is_power_of_two(16)  # True
        bitwise.is_power_of_two(15)  # False
    """
    return n > 0 and (n & (n - 1)) == 0


def to_binary(n, width=None):
    """
    Convert integer to binary string.
    
    Args:
        n: Integer
        width: Minimum width (zero-padded)
    
    Returns:
        Binary string
    
    Example:
        bitwise.to_binary(10)  # "1010"
        bitwise.to_binary(10, 8)  # "00001010"
    """
    if width:
        return format(n, f'0{width}b')
    return bin(n)[2:]


def from_binary(binary_str):
    """
    Convert binary string to integer.
    
    Args:
        binary_str: Binary string
    
    Returns:
        Integer value
    
    Example:
        bitwise.from_binary("1010")  # 10
    """
    return int(binary_str, 2)


def rotate_left(n, shift, width=32):
    """
    Rotate bits left.
    
    Args:
        n: Integer
        shift: Number of positions to rotate
        width: Bit width (default 32)
    
    Returns:
        Rotated value
    
    Example:
        bitwise.rotate_left(1, 2, 8)  # 4
    """
    shift %= width
    mask = (1 << width) - 1
    n &= mask
    return ((n << shift) | (n >> (width - shift))) & mask


def rotate_right(n, shift, width=32):
    """
    Rotate bits right.
    
    Args:
        n: Integer
        shift: Number of positions to rotate
        width: Bit width (default 32)
    
    Returns:
        Rotated value
    
    Example:
        bitwise.rotate_right(4, 2, 8)  # 1
    """
    shift %= width
    mask = (1 << width) - 1
    n &= mask
    return ((n >> shift) | (n << (width - shift))) & mask


def get_bit(n, pos):
    """
    Get bit at position.
    
    Args:
        n: Integer
        pos: Bit position (0-indexed)
    
    Returns:
        0 or 1
    
    Example:
        bitwise.get_bit(12, 2)  # 1 (binary: 1100)
    """
    return (n >> pos) & 1


def set_bit(n, pos):
    """
    Set bit at position to 1.
    
    Args:
        n: Integer
        pos: Bit position (0-indexed)
    
    Returns:
        Modified integer
    
    Example:
        bitwise.set_bit(8, 0)  # 9 (binary: 1000 -> 1001)
    """
    return n | (1 << pos)


def clear_bit(n, pos):
    """
    Clear bit at position (set to 0).
    
    Args:
        n: Integer
        pos: Bit position (0-indexed)
    
    Returns:
        Modified integer
    
    Example:
        bitwise.clear_bit(9, 0)  # 8 (binary: 1001 -> 1000)
    """
    return n & ~(1 << pos)


__all__ = [
    'bitwise_and',
    'bitwise_or',
    'bitwise_xor',
    'bitwise_not',
    'shift_left',
    'shift_right',
    'count_bits',
    'is_power_of_two',
    'to_binary',
    'from_binary',
    'rotate_left',
    'rotate_right',
    'get_bit',
    'set_bit',
    'clear_bit',
]
