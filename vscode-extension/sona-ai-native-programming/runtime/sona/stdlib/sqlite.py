"""
sqlite - SQLite database operations for Sona stdlib

Provides simple SQLite database access:
- connect: Open database connection
- query: Execute SQL queries
- execute: Execute SQL statements
- Database: Database connection wrapper
"""

import sqlite3
from typing import List, Dict, Any, Optional


class Database:
    """SQLite database connection wrapper."""
    
    def __init__(self, path=':memory:'):
        """
        Create database connection.
        
        Args:
            path: Database file path (default ':memory:' for in-memory)
        """
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
    
    def query(self, sql, params=None):
        """
        Execute SELECT query and return results.
        
        Args:
            sql: SQL query string
            params: Query parameters (tuple or dict)
        
        Returns:
            List of dictionaries (rows)
        
        Example:
            rows = db.query("SELECT * FROM users WHERE age > ?", (18,))
        """
        cursor = self.conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def execute(self, sql, params=None):
        """
        Execute SQL statement (INSERT, UPDATE, DELETE, etc.).
        
        Args:
            sql: SQL statement
            params: Statement parameters
        
        Returns:
            Number of affected rows
        
        Example:
            db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
            db.commit()
        """
        cursor = self.conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        return cursor.rowcount
    
    def commit(self):
        """Commit pending transactions."""
        self.conn.commit()
    
    def rollback(self):
        """Rollback pending transactions."""
        self.conn.rollback()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
    
    def execute_many(self, sql, params_list):
        """
        Execute SQL statement with multiple parameter sets.
        
        Args:
            sql: SQL statement
            params_list: List of parameter tuples
        
        Returns:
            Number of affected rows
        
        Example:
            db.execute_many("INSERT INTO users (name) VALUES (?)", 
                          [("Alice",), ("Bob",), ("Charlie",)])
        """
        cursor = self.conn.cursor()
        cursor.executemany(sql, params_list)
        return cursor.rowcount
    
    def query_one(self, sql, params=None):
        """
        Execute query and return first row.
        
        Args:
            sql: SQL query string
            params: Query parameters
        
        Returns:
            Dictionary (first row) or None
        
        Example:
            user = db.query_one("SELECT * FROM users WHERE id = ?", (1,))
        """
        cursor = self.conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def begin(self):
        """Begin transaction explicitly."""
        self.conn.execute("BEGIN")
    
    def transaction(self):
        """
        Context manager for transactions.
        
        Example:
            with db.transaction():
                db.insert("users", {"name": "Alice"})
                db.insert("users", {"name": "Bob"})
        """
        return _Transaction(self)
    
    def create_table(self, table_name, columns):
        """
        Create a table.
        
        Args:
            table_name: Name of table
            columns: Dictionary of column_name: column_type
        
        Example:
            db.create_table("users", {
                "id": "INTEGER PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "age": "INTEGER"
            })
        """
        cols = ', '.join([f"{name} {type_}" for name, type_ in columns.items()])
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})"
        self.execute(sql)
        self.commit()
    
    def insert(self, table, data):
        """
        Insert row into table.
        
        Args:
            table: Table name
            data: Dictionary of column: value
        
        Returns:
            Last inserted row ID
        
        Example:
            row_id = db.insert("users", {"name": "Bob", "age": 25})
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(data.values()))
        self.commit()
        
        return cursor.lastrowid
    
    def update(self, table, data, where):
        """
        Update rows in table.
        
        Args:
            table: Table name
            data: Dictionary of column: value to update
            where: WHERE clause (string and params tuple)
        
        Returns:
            Number of affected rows
        
        Example:
            count = db.update("users", 
                            {"age": 26}, 
                            ("name = ?", ("Bob",)))
        """
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        where_clause, where_params = where
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(data.values()) + where_params
        return self.execute(sql, params)
    
    def delete(self, table, where):
        """
        Delete rows from table.
        
        Args:
            table: Table name
            where: WHERE clause (string and params tuple)
        
        Returns:
            Number of deleted rows
        
        Example:
            count = db.delete("users", ("age < ?", (18,)))
        """
        where_clause, where_params = where
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        return self.execute(sql, where_params)


    def drop_table(self, table_name):
        """Drop a table if it exists."""
        sql = f"DROP TABLE IF EXISTS {table_name}"
        self.execute(sql)
        self.commit()
    
    def table_exists(self, table_name):
        """Check if table exists."""
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.query_one(sql, (table_name,))
        return result is not None
    
    def list_tables(self):
        """List all tables in database."""
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        rows = self.query(sql)
        return [row['name'] for row in rows]
    
    def table_info(self, table_name):
        """Get column information for table."""
        sql = f"PRAGMA table_info({table_name})"
        return self.query(sql)
    
    def vacuum(self):
        """Optimize database (rebuild, reclaim space)."""
        self.conn.execute("VACUUM")
        self.commit()
    
    def pragma(self, name, value=None):
        """
        Get or set PRAGMA value.
        
        Args:
            name: PRAGMA name
            value: Value to set (None to get)
        
        Returns:
            Current value if getting, None if setting
        """
        if value is None:
            cursor = self.conn.execute(f"PRAGMA {name}")
            return cursor.fetchone()[0]
        else:
            self.conn.execute(f"PRAGMA {name} = {value}")
    
    def backup(self, target_path):
        """
        Backup database to another file.
        
        Args:
            target_path: Path to backup file
        """
        import shutil
        self.commit()
        shutil.copy2(self.path, target_path)
    
    def last_insert_id(self):
        """Get ID of last inserted row."""
        cursor = self.conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]
    
    def row_count(self, table_name):
        """Get number of rows in table."""
        result = self.query_one(f"SELECT COUNT(*) as count FROM {table_name}")
        return result['count'] if result else 0
    
    def execute_script(self, script):
        """Execute multiple SQL statements."""
        self.conn.executescript(script)
        self.commit()


class _Transaction:
    """Transaction context manager."""
    
    def __init__(self, db):
        self.db = db
    
    def __enter__(self):
        self.db.begin()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.db.commit()
        else:
            self.db.rollback()


def connect(path=':memory:'):
    """
    Connect to SQLite database.
    
    Args:
        path: Database file path (default ':memory:')
    
    Returns:
        Database connection object
    
    Example:
        db = sqlite.connect("myapp.db")
        db.create_table("users", {"id": "INTEGER PRIMARY KEY", "name": "TEXT"})
        db.insert("users", {"name": "Alice"})
        rows = db.query("SELECT * FROM users")
        db.close()
    """
    return Database(path)


def query(db, sql, params=None):
    """Execute SELECT query."""
    return db.query(sql, params)


def query_one(db, sql, params=None):
    """Execute query and return first row."""
    return db.query_one(sql, params)


def execute(db, sql, params=None):
    """Execute SQL statement."""
    return db.execute(sql, params)


def execute_many(db, sql, params_list):
    """Execute SQL with multiple parameter sets."""
    return db.execute_many(sql, params_list)


def insert(db, table, data):
    """Insert row into table."""
    return db.insert(table, data)


def update(db, table, data, where):
    """Update rows in table."""
    return db.update(table, data, where)


def delete(db, table, where):
    """Delete rows from table."""
    return db.delete(table, where)


def create_table(db, table_name, columns):
    """Create a table."""
    db.create_table(table_name, columns)


def drop_table(db, table_name):
    """Drop a table."""
    db.drop_table(table_name)


def table_exists(db, table_name):
    """Check if table exists."""
    return db.table_exists(table_name)


def list_tables(db):
    """List all tables."""
    return db.list_tables()


def vacuum(db):
    """Optimize database."""
    db.vacuum()


def backup(db, target_path):
    """Backup database to file."""
    db.backup(target_path)
