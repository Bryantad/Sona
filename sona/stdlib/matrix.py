"""
matrix - Matrix operations for Sona stdlib

Provides matrix utilities:
- Matrix: 2D matrix class
- add/multiply: Matrix operations
- transpose: Matrix transpose
"""


class Matrix:
    """2D matrix."""
    
    def __init__(self, data):
        """
        Initialize matrix.
        
        Args:
            data: 2D list of numbers
        
        Example:
            m = matrix.Matrix([[1, 2], [3, 4]])
        """
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0
    
    def get(self, row, col):
        """Get element at position."""
        return self.data[row][col]
    
    def set(self, row, col, value):
        """Set element at position."""
        self.data[row][col] = value
    
    def add(self, other):
        """
        Add matrices.
        
        Args:
            other: Matrix to add
        
        Returns:
            New matrix
        
        Example:
            result = m1.add(m2)
        """
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrix dimensions must match")
        
        result = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                row.append(self.data[i][j] + other.data[i][j])
            result.append(row)
        
        return Matrix(result)
    
    def multiply(self, other):
        """
        Multiply matrices.
        
        Args:
            other: Matrix to multiply
        
        Returns:
            New matrix
        
        Example:
            result = m1.multiply(m2)
        """
        if self.cols != other.rows:
            raise ValueError("Invalid dimensions for multiplication")
        
        result = []
        for i in range(self.rows):
            row = []
            for j in range(other.cols):
                total = sum(self.data[i][k] * other.data[k][j] for k in range(self.cols))
                row.append(total)
            result.append(row)
        
        return Matrix(result)
    
    def transpose(self):
        """
        Transpose matrix.
        
        Returns:
            Transposed matrix
        
        Example:
            transposed = m.transpose()
        """
        result = [[self.data[i][j] for i in range(self.rows)] for j in range(self.cols)]
        return Matrix(result)
    
    def scalar_multiply(self, scalar):
        """
        Multiply by scalar.
        
        Args:
            scalar: Number to multiply by
        
        Returns:
            New matrix
        
        Example:
            result = m.scalar_multiply(2)
        """
        result = [[self.data[i][j] * scalar for j in range(self.cols)] for i in range(self.rows)]
        return Matrix(result)
    
    def to_list(self):
        """Convert to 2D list."""
        return [row[:] for row in self.data]
    
    def __str__(self):
        """String representation."""
        return '\n'.join([' '.join(map(str, row)) for row in self.data])


def create(data):
    """
    Create matrix from 2D list.
    
    Args:
        data: 2D list
    
    Returns:
        Matrix object
    
    Example:
        m = matrix.create([[1, 2], [3, 4]])
    """
    return Matrix(data)


def identity(size):
    """
    Create identity matrix.
    
    Args:
        size: Matrix size
    
    Returns:
        Identity matrix
    
    Example:
        I = matrix.identity(3)
        # [[1, 0, 0],
        #  [0, 1, 0],
        #  [0, 0, 1]]
    """
    data = [[1 if i == j else 0 for j in range(size)] for i in range(size)]
    return Matrix(data)


def zeros(rows, cols):
    """
    Create zero matrix.
    
    Args:
        rows: Number of rows
        cols: Number of columns
    
    Returns:
        Zero matrix
    
    Example:
        Z = matrix.zeros(2, 3)
    """
    data = [[0 for _ in range(cols)] for _ in range(rows)]
    return Matrix(data)


def ones(rows, cols):
    """
    Create matrix of ones.
    
    Args:
        rows: Number of rows
        cols: Number of columns
    
    Returns:
        Matrix of ones
    
    Example:
        O = matrix.ones(2, 3)
    """
    data = [[1 for _ in range(cols)] for _ in range(rows)]
    return Matrix(data)


def diagonal(values):
    """
    Create diagonal matrix.
    
    Args:
        values: List of diagonal values
    
    Returns:
        Diagonal matrix
    
    Example:
        D = matrix.diagonal([1, 2, 3])
    """
    size = len(values)
    data = [[0 for _ in range(size)] for _ in range(size)]
    
    for i in range(size):
        data[i][i] = values[i]
    
    return Matrix(data)


def determinant(mat):
    """
    Calculate matrix determinant.
    
    Args:
        mat: Square Matrix object
    
    Returns:
        Determinant value
    
    Example:
        det = matrix.determinant(m)
    """
    if mat.rows != mat.cols:
        raise ValueError("Determinant requires square matrix")
    
    if mat.rows == 1:
        return mat.data[0][0]
    
    if mat.rows == 2:
        return mat.data[0][0] * mat.data[1][1] - mat.data[0][1] * mat.data[1][0]
    
    det = 0
    for j in range(mat.cols):
        minor = _get_minor(mat.data, 0, j)
        cofactor = ((-1) ** j) * mat.data[0][j] * _det_recursive(minor)
        det += cofactor
    
    return det


def _get_minor(data, row, col):
    """Get minor matrix by removing row and col."""
    return [row[:col] + row[col+1:] for i, row in enumerate(data) if i != row]


def _det_recursive(data):
    """Calculate determinant recursively."""
    if len(data) == 1:
        return data[0][0]
    
    if len(data) == 2:
        return data[0][0] * data[1][1] - data[0][1] * data[1][0]
    
    det = 0
    for j in range(len(data[0])):
        minor = _get_minor(data, 0, j)
        cofactor = ((-1) ** j) * data[0][j] * _det_recursive(minor)
        det += cofactor
    
    return det


def trace(mat):
    """
    Calculate matrix trace (sum of diagonal).
    
    Args:
        mat: Square Matrix object
    
    Returns:
        Trace value
    
    Example:
        tr = matrix.trace(m)
    """
    if mat.rows != mat.cols:
        raise ValueError("Trace requires square matrix")
    
    return sum(mat.data[i][i] for i in range(mat.rows))


def dot(vec1, vec2):
    """
    Calculate dot product of vectors.
    
    Args:
        vec1: First vector (list)
        vec2: Second vector (list)
    
    Returns:
        Dot product
    
    Example:
        result = matrix.dot([1, 2, 3], [4, 5, 6])
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same length")
    
    return sum(a * b for a, b in zip(vec1, vec2))


def norm(vec):
    """
    Calculate vector norm (magnitude).
    
    Args:
        vec: Vector (list)
    
    Returns:
        Norm value
    
    Example:
        magnitude = matrix.norm([3, 4])  # 5.0
    """
    return sum(x ** 2 for x in vec) ** 0.5


def reshape(mat, new_rows, new_cols):
    """
    Reshape matrix.
    
    Args:
        mat: Matrix object
        new_rows: New number of rows
        new_cols: New number of columns
    
    Returns:
        Reshaped matrix
    
    Example:
        reshaped = matrix.reshape(m, 3, 2)
    """
    if mat.rows * mat.cols != new_rows * new_cols:
        raise ValueError("Total elements must remain same")
    
    flat = [mat.data[i][j] for i in range(mat.rows) for j in range(mat.cols)]
    
    data = []
    idx = 0
    for i in range(new_rows):
        row = []
        for j in range(new_cols):
            row.append(flat[idx])
            idx += 1
        data.append(row)
    
    return Matrix(data)


def flatten(mat):
    """
    Flatten matrix to 1D list.
    
    Args:
        mat: Matrix object
    
    Returns:
        Flattened list
    
    Example:
        vec = matrix.flatten(m)
    """
    return [mat.data[i][j] for i in range(mat.rows) for j in range(mat.cols)]


def from_list(flat_list, rows, cols):
    """
    Create matrix from flat list.
    
    Args:
        flat_list: 1D list
        rows: Number of rows
        cols: Number of columns
    
    Returns:
        Matrix object
    
    Example:
        m = matrix.from_list([1, 2, 3, 4], 2, 2)
    """
    if len(flat_list) != rows * cols:
        raise ValueError("List size must equal rows * cols")
    
    data = []
    idx = 0
    for i in range(rows):
        row = []
        for j in range(cols):
            row.append(flat_list[idx])
            idx += 1
        data.append(row)
    
    return Matrix(data)


__all__ = [
    'Matrix', 'create', 'identity', 'zeros', 'ones', 'diagonal',
    'determinant', 'trace', 'dot', 'norm', 'reshape', 'flatten', 'from_list'
]
