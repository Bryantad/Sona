"""
query - Enhanced SQL query builder for Sona stdlib

Comprehensive SQL query building:
- SELECT with joins, subqueries, unions
- INSERT, UPDATE, DELETE
- Aggregation functions
- GROUP BY, HAVING
- Complex WHERE conditions
- Raw SQL support
"""


class QueryBuilder:
    """SQL query builder."""
    
    def __init__(self, table=None):
        """Initialize builder."""
        self._table = table
        self._select_fields = []
        self._where_clauses = []
        self._where_params = []
        self._order_by = []
        self._limit_val = None
        self._offset_val = None
        self._joins = []
    
    def table(self, name):
        """Set table name."""
        self._table = name
        return self
    
    def select(self, *fields):
        """Set fields to select."""
        self._select_fields = fields if fields else ['*']
        return self
    
    def where(self, condition, *params):
        """Add WHERE clause."""
        self._where_clauses.append(condition)
        self._where_params.extend(params)
        return self
    
    def order_by(self, field, direction='ASC'):
        """Add ORDER BY clause."""
        self._order_by.append(f"{field} {direction}")
        return self
    
    def limit(self, count):
        """Set LIMIT."""
        self._limit_val = count
        return self
    
    def offset(self, count):
        """Set OFFSET."""
        self._offset_val = count
        return self
    
    def join(self, table, on, join_type='INNER'):
        """Add JOIN clause."""
        self._joins.append(f"{join_type} JOIN {table} ON {on}")
        return self
    
    def inner_join(self, table, on):
        """Add INNER JOIN."""
        return self.join(table, on, 'INNER')
    
    def left_join(self, table, on):
        """Add LEFT JOIN."""
        return self.join(table, on, 'LEFT')
    
    def right_join(self, table, on):
        """Add RIGHT JOIN."""
        return self.join(table, on, 'RIGHT')
    
    def group_by(self, *fields):
        """Add GROUP BY clause."""
        if not hasattr(self, '_group_by'):
            self._group_by = []
        self._group_by.extend(fields)
        return self
    
    def having(self, condition, *params):
        """Add HAVING clause."""
        if not hasattr(self, '_having_clauses'):
            self._having_clauses = []
            self._having_params = []
        self._having_clauses.append(condition)
        self._having_params.extend(params)
        return self
    
    def or_where(self, condition, *params):
        """Add OR WHERE condition."""
        if self._where_clauses:
            # Wrap previous conditions in parentheses and add OR
            last = self._where_clauses.pop()
            self._where_clauses.append(f"({last} OR {condition})")
        else:
            self._where_clauses.append(condition)
        self._where_params.extend(params)
        return self
    
    def where_in(self, field, values):
        """Add WHERE IN clause."""
        placeholders = ', '.join(['?' for _ in values])
        self._where_clauses.append(f"{field} IN ({placeholders})")
        self._where_params.extend(values)
        return self
    
    def where_between(self, field, start, end):
        """Add WHERE BETWEEN clause."""
        self._where_clauses.append(f"{field} BETWEEN ? AND ?")
        self._where_params.extend([start, end])
        return self
    
    def where_like(self, field, pattern):
        """Add WHERE LIKE clause."""
        self._where_clauses.append(f"{field} LIKE ?")
        self._where_params.append(pattern)
        return self
    
    def where_null(self, field):
        """Add WHERE field IS NULL."""
        self._where_clauses.append(f"{field} IS NULL")
        return self
    
    def where_not_null(self, field):
        """Add WHERE field IS NOT NULL."""
        self._where_clauses.append(f"{field} IS NOT NULL")
        return self
    
    def distinct(self):
        """Add DISTINCT modifier."""
        self._distinct = True
        return self
    
    def count(self, field='*', alias='count'):
        """Add COUNT aggregate."""
        self._select_fields = [f"COUNT({field}) as {alias}"]
        return self
    
    def sum(self, field, alias='total'):
        """Add SUM aggregate."""
        self._select_fields = [f"SUM({field}) as {alias}"]
        return self
    
    def avg(self, field, alias='average'):
        """Add AVG aggregate."""
        self._select_fields = [f"AVG({field}) as {alias}"]
        return self
    
    def min(self, field, alias='minimum'):
        """Add MIN aggregate."""
        self._select_fields = [f"MIN({field}) as {alias}"]
        return self
    
    def max(self, field, alias='maximum'):
        """Add MAX aggregate."""
        self._select_fields = [f"MAX({field}) as {alias}"]
        return self
    
    def build(self):
        """
        Build SELECT query.
        
        Returns:
            Tuple of (sql, params)
        
        Example:
            query = query.QueryBuilder('users')
            query.select('name', 'email').where('age > ?', 18).order_by('name')
            sql, params = query.build()
        """
        if not self._select_fields:
            self._select_fields = ['*']
        
        # SELECT clause
        distinct = 'DISTINCT ' if hasattr(self, '_distinct') and self._distinct else ''
        sql = f"SELECT {distinct}{', '.join(self._select_fields)} FROM {self._table}"
        
        # Add JOINs
        if self._joins:
            sql += ' ' + ' '.join(self._joins)
        
        # Add WHERE
        if self._where_clauses:
            sql += ' WHERE ' + ' AND '.join(self._where_clauses)
        
        # Add GROUP BY
        if hasattr(self, '_group_by') and self._group_by:
            sql += ' GROUP BY ' + ', '.join(self._group_by)
        
        # Add HAVING
        if hasattr(self, '_having_clauses') and self._having_clauses:
            sql += ' HAVING ' + ' AND '.join(self._having_clauses)
            all_params = self._where_params + self._having_params
        else:
            all_params = self._where_params
        
        # Add ORDER BY
        if self._order_by:
            sql += ' ORDER BY ' + ', '.join(self._order_by)
        
        # Add LIMIT/OFFSET
        if self._limit_val:
            sql += f' LIMIT {self._limit_val}'
        if self._offset_val:
            sql += f' OFFSET {self._offset_val}'
        
        return sql, all_params
    
    def union(self, other_builder, union_all=False):
        """
        Create UNION with another query.
        
        Args:
            other_builder: Another QueryBuilder
            union_all: Use UNION ALL instead of UNION
        
        Returns:
            New QueryBuilder with UNION
        """
        sql1, params1 = self.build()
        sql2, params2 = other_builder.build()
        
        union_type = 'UNION ALL' if union_all else 'UNION'
        combined_sql = f"{sql1} {union_type} {sql2}"
        
        # Create a new builder with the combined query
        builder = QueryBuilder()
        builder._raw_sql = combined_sql
        builder._where_params = params1 + params2
        return builder
    
    def raw(self, sql, params=None):
        """
        Set raw SQL query.
        
        Args:
            sql: Raw SQL string
            params: Query parameters
        
        Returns:
            Self for chaining
        """
        self._raw_sql = sql
        self._where_params = params or []
        return self
    
    def get_sql(self):
        """Get the generated SQL (alias for build)."""
        return self.build()


def select(table):
    """
    Create SELECT query builder.
    
    Args:
        table: Table name
    
    Returns:
        QueryBuilder object
    
    Example:
        sql, params = query.select('users') \\
            .where('age > ?', 18) \\
            .order_by('name') \\
            .limit(10) \\
            .build()
    """
    return QueryBuilder(table)


def insert(table, data):
    """
    Build INSERT query.
    
    Args:
        table: Table name
        data: Dictionary of field->value
    
    Returns:
        Tuple of (sql, params)
    
    Example:
        sql, params = query.insert('users', {
            'name': 'John',
            'email': 'john@example.com'
        })
    """
    fields = list(data.keys())
    values = list(data.values())
    placeholders = ', '.join(['?' for _ in fields])
    
    sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
    return sql, values


def update(table, data, where=None, where_params=None):
    """
    Build UPDATE query.
    
    Args:
        table: Table name
        data: Dictionary of field->value
        where: WHERE clause
        where_params: WHERE parameters
    
    Returns:
        Tuple of (sql, params)
    
    Example:
        sql, params = query.update(
            'users',
            {'email': 'newemail@example.com'},
            'id = ?',
            [123]
        )
    """
    fields = list(data.keys())
    values = list(data.values())
    set_clause = ', '.join([f"{f} = ?" for f in fields])
    
    sql = f"UPDATE {table} SET {set_clause}"
    
    if where:
        sql += f" WHERE {where}"
        values.extend(where_params or [])
    
    return sql, values


def delete(table, where=None, where_params=None):
    """
    Build DELETE query.
    
    Args:
        table: Table name
        where: WHERE clause
        where_params: WHERE parameters
    
    Returns:
        Tuple of (sql, params)
    
    Example:
        sql, params = query.delete('users', 'id = ?', [123])
    """
    sql = f"DELETE FROM {table}"
    params = []
    
    if where:
        sql += f" WHERE {where}"
        params = where_params or []
    
    return sql, params


def union(query1, query2, union_all=False):
    """
    Create UNION of two queries.
    
    Args:
        query1: First QueryBuilder or (sql, params) tuple
        query2: Second QueryBuilder or (sql, params) tuple
        union_all: Use UNION ALL
    
    Returns:
        Tuple of (sql, params)
    """
    if isinstance(query1, QueryBuilder):
        sql1, params1 = query1.build()
    else:
        sql1, params1 = query1
    
    if isinstance(query2, QueryBuilder):
        sql2, params2 = query2.build()
    else:
        sql2, params2 = query2
    
    union_type = 'UNION ALL' if union_all else 'UNION'
    sql = f"{sql1} {union_type} {sql2}"
    params = params1 + params2
    
    return sql, params


def subquery(builder, alias):
    """
    Create subquery with alias.
    
    Args:
        builder: QueryBuilder instance
        alias: Alias name
    
    Returns:
        Subquery string
    """
    sql, _ = builder.build()
    return f"({sql}) AS {alias}"


def raw(sql, params=None):
    """
    Create raw SQL query.
    
    Args:
        sql: Raw SQL string
        params: Query parameters
    
    Returns:
        Tuple of (sql, params)
    """
    return sql, params or []


def count(table, where=None, where_params=None):
    """
    Build COUNT query.
    
    Args:
        table: Table name
        where: WHERE clause
        where_params: WHERE parameters
    
    Returns:
        Tuple of (sql, params)
    """
    return QueryBuilder(table).count().where(where, *where_params).build() if where else QueryBuilder(table).count().build()


def aggregate(table, func, field, where=None, where_params=None):
    """
    Build aggregate query.
    
    Args:
        table: Table name
        func: Aggregate function (SUM, AVG, MIN, MAX)
        field: Field name
        where: WHERE clause
        where_params: WHERE parameters
    
    Returns:
        Tuple of (sql, params)
    """
    builder = QueryBuilder(table).select(f"{func}({field}) as result")
    if where:
        builder.where(where, *(where_params or []))
    return builder.build()


def create_table(table, columns):
    """
    Build CREATE TABLE query.
    
    Args:
        table: Table name
        columns: Dict of column_name: column_definition
    
    Returns:
        SQL string
    
    Example:
        sql = query.create_table('users', {
            'id': 'INTEGER PRIMARY KEY',
            'name': 'TEXT NOT NULL',
            'email': 'TEXT UNIQUE'
        })
    """
    col_defs = [f"{name} {definition}" for name, definition in columns.items()]
    return f"CREATE TABLE {table} ({', '.join(col_defs)})"


def drop_table(table, if_exists=False):
    """
    Build DROP TABLE query.
    
    Args:
        table: Table name
        if_exists: Add IF EXISTS clause
    
    Returns:
        SQL string
    """
    if_exists_clause = 'IF EXISTS ' if if_exists else ''
    return f"DROP TABLE {if_exists_clause}{table}"


def alter_table_add_column(table, column, definition):
    """
    Build ALTER TABLE ADD COLUMN query.
    
    Args:
        table: Table name
        column: Column name
        definition: Column definition
    
    Returns:
        SQL string
    """
    return f"ALTER TABLE {table} ADD COLUMN {column} {definition}"


def create_index(index_name, table, columns, unique=False):
    """
    Build CREATE INDEX query.
    
    Args:
        index_name: Index name
        table: Table name
        columns: List of column names or single column
        unique: Create UNIQUE index
    
    Returns:
        SQL string
    """
    unique_clause = 'UNIQUE ' if unique else ''
    if isinstance(columns, str):
        columns = [columns]
    return f"CREATE {unique_clause}INDEX {index_name} ON {table} ({', '.join(columns)})"


def drop_index(index_name):
    """
    Build DROP INDEX query.
    
    Args:
        index_name: Index name
    
    Returns:
        SQL string
    """
    return f"DROP INDEX {index_name}"


__all__ = [
    'QueryBuilder',
    'select',
    'insert',
    'update',
    'delete',
    'union',
    'subquery',
    'raw',
    'count',
    'aggregate',
    'create_table',
    'drop_table',
    'alter_table_add_column',
    'create_index',
    'drop_index',
]
