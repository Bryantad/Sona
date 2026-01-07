"""
orm - Enhanced ORM (Object-Relational Mapping) for Sona stdlib

Comprehensive ORM functionality:
- Model: Base model with lifecycle hooks
- Fields: String, Integer, Boolean, DateTime, ForeignKey
- Relationships: belongs_to, has_many, has_one
- Query building: where, order_by, limit, join
- Validation and hooks
- Serialization: to_dict, from_dict
- Aggregates: count, sum, avg, min, max
"""

from typing import Any, Dict, List, Optional, Callable


class Field:
    """Base field class."""
    
    def __init__(self, field_type, required=False, default=None):
        self.field_type = field_type
        self.required = required
        self.default = default


class StringField(Field):
    """String field."""
    def __init__(self, max_length=255, **kwargs):
        super().__init__('TEXT', **kwargs)
        self.max_length = max_length


class IntegerField(Field):
    """Integer field."""
    def __init__(self, **kwargs):
        super().__init__('INTEGER', **kwargs)


class BooleanField(Field):
    """Boolean field."""
    def __init__(self, **kwargs):
        super().__init__('INTEGER', **kwargs)


class DateTimeField(Field):
    """DateTime field."""
    def __init__(self, **kwargs):
        super().__init__('TEXT', **kwargs)


class ForeignKey(Field):
    """Foreign key field."""
    def __init__(self, model_class, **kwargs):
        super().__init__('INTEGER', **kwargs)
        self.model_class = model_class


class QueryBuilder:
    """Query builder for ORM models."""
    
    def __init__(self, model_class):
        self.model_class = model_class
        self._where_clauses = []
        self._where_params = []
        self._order_by = None
        self._limit_value = None
        self._offset_value = None
        self._joins = []
    
    def where(self, condition, params=None):
        """Add WHERE condition."""
        self._where_clauses.append(condition)
        if params:
            if isinstance(params, list):
                self._where_params.extend(params)
            else:
                self._where_params.append(params)
        return self
    
    def order_by(self, field, direction='ASC'):
        """Add ORDER BY clause."""
        self._order_by = f"{field} {direction}"
        return self
    
    def limit(self, count):
        """Add LIMIT clause."""
        self._limit_value = count
        return self
    
    def offset(self, count):
        """Add OFFSET clause."""
        self._offset_value = count
        return self
    
    def join(self, table, condition):
        """Add JOIN clause."""
        self._joins.append(f"JOIN {table} ON {condition}")
        return self
    
    def build_sql(self):
        """Build SQL query."""
        sql = f"SELECT * FROM {self.model_class._table_name}"
        
        if self._joins:
            sql += " " + " ".join(self._joins)
        
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        
        if self._limit_value:
            sql += f" LIMIT {self._limit_value}"
        
        if self._offset_value:
            sql += f" OFFSET {self._offset_value}"
        
        return sql, self._where_params
    
    def all(self):
        """Execute query and return all results."""
        sql, params = self.build_sql()
        results = self.model_class._db.query(sql, params)
        return [self.model_class(**row) for row in results]
    
    def first(self):
        """Execute query and return first result."""
        self.limit(1)
        results = self.all()
        return results[0] if results else None
    
    def count(self):
        """Count matching records."""
        sql = f"SELECT COUNT(*) as count FROM {self.model_class._table_name}"
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        result = self.model_class._db.query(sql, self._where_params)
        return result[0]['count'] if result else 0


class Model:
    """Base ORM model with relationships and hooks."""
    
    _table_name = None
    _fields = {}
    _db = None
    _relationships = {}
    _validators = []
    _hooks = {
        'before_save': [],
        'after_save': [],
        'before_delete': [],
        'after_delete': []
    }
    
    def __init__(self, **kwargs):
        """Initialize model with field values."""
        self.id = kwargs.get('id')
        self._data = {}
        self._errors = []
        
        for name, field in self._fields.items():
            value = kwargs.get(name, field.default)
            self._data[name] = value
    
    def __getattr__(self, name):
        """Get field value or relationship."""
        if name in self._data:
            return self._data[name]
        if name in self._relationships:
            return self._load_relationship(name)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
    
    @classmethod
    def set_database(cls, db):
        """Set database connection."""
        cls._db = db
    
    @classmethod
    def create_table(cls):
        """Create database table."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        fields = []
        fields.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
        
        for name, field in cls._fields.items():
            field_def = f"{name} {field.field_type}"
            if field.required:
                field_def += " NOT NULL"
            fields.append(field_def)
        
        sql = f"CREATE TABLE IF NOT EXISTS {cls._table_name} ({', '.join(fields)})"
        cls._db.execute(sql)
    
    def validate(self):
        """Validate model fields."""
        self._errors = []
        
        for name, field in self._fields.items():
            value = self._data.get(name)
            
            if field.required and value is None:
                self._errors.append(f"{name} is required")
        
        # Run custom validators
        for validator in self._validators:
            result = validator(self)
            if result:
                self._errors.append(result)
        
        return len(self._errors) == 0
    
    def _load_relationship(self, name):
        """Load relationship data."""
        rel = self._relationships.get(name)
        if not rel:
            return None
        
        rel_type = rel.get('type')
        model_class = rel.get('model')
        foreign_key = rel.get('foreign_key')
        
        if rel_type == 'belongs_to':
            fk_value = self._data.get(foreign_key)
            return model_class.find(fk_value) if fk_value else None
        
        elif rel_type == 'has_many':
            return model_class.where(f"{foreign_key}=?", [self.id]).all()
        
        elif rel_type == 'has_one':
            return model_class.where(f"{foreign_key}=?", [self.id]).first()
        
        return None
    
    def _run_hooks(self, hook_name):
        """Run lifecycle hooks."""
        for hook in self._hooks.get(hook_name, []):
            hook(self)
    
    def save(self):
        """Save model to database with validation and hooks."""
        if not self._db:
            raise RuntimeError("Database not set")
        
        # Validate
        if not self.validate():
            raise ValueError(f"Validation failed: {', '.join(self._errors)}")
        
        # Run before_save hooks
        self._run_hooks('before_save')
        
        if self.id is None:
            # Insert
            fields = list(self._data.keys())
            values = [self._data[f] for f in fields]
            placeholders = ','.join(['?' for _ in fields])
            field_list = ','.join(fields)
            sql = f"INSERT INTO {self._table_name} "
            sql += f"({field_list}) VALUES ({placeholders})"
            self._db.execute(sql, values)
            self.id = self._db.last_insert_id()
        else:
            # Update
            updates = [f"{f}=?" for f in self._data.keys()]
            values = list(self._data.values()) + [self.id]
            update_str = ','.join(updates)
            sql = f"UPDATE {self._table_name} SET {update_str} WHERE id=?"
            self._db.execute(sql, values)
        
        # Run after_save hooks
        self._run_hooks('after_save')
        
        return self
    
    def delete(self):
        """Delete model from database with hooks."""
        if not self._db:
            raise RuntimeError("Database not set")
        
        if self.id is not None:
            # Run before_delete hooks
            self._run_hooks('before_delete')
            
            sql = f"DELETE FROM {self._table_name} WHERE id=?"
            self._db.execute(sql, [self.id])
            self.id = None
            
            # Run after_delete hooks
            self._run_hooks('after_delete')
    
    @classmethod
    def find(cls, id):
        """Find model by ID."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        sql = f"SELECT * FROM {cls._table_name} WHERE id=?"
        result = cls._db.query(sql, [id])
        
        if result:
            return cls(**result[0])
        return None
    
    @classmethod
    def find_all(cls, where=None, params=None):
        """Find all models matching criteria."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        sql = f"SELECT * FROM {cls._table_name}"
        if where:
            sql += f" WHERE {where}"
        
        results = cls._db.query(sql, params or [])
        return [cls(**row) for row in results]
    
    @classmethod
    def where(cls, condition, params=None):
        """Start query builder with WHERE clause."""
        builder = QueryBuilder(cls)
        return builder.where(condition, params)
    
    @classmethod
    def order_by(cls, field, direction='ASC'):
        """Start query builder with ORDER BY."""
        builder = QueryBuilder(cls)
        return builder.order_by(field, direction)
    
    @classmethod
    def limit(cls, count):
        """Start query builder with LIMIT."""
        builder = QueryBuilder(cls)
        return builder.limit(count)
    
    @classmethod
    def all(cls):
        """Get all records."""
        return cls.find_all()
    
    @classmethod
    def first(cls):
        """Get first record."""
        builder = QueryBuilder(cls)
        return builder.first()
    
    @classmethod
    def count(cls, where=None, params=None):
        """Count records."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        sql = f"SELECT COUNT(*) as count FROM {cls._table_name}"
        if where:
            sql += f" WHERE {where}"
        
        result = cls._db.query(sql, params or [])
        return result[0]['count'] if result else 0
    
    @classmethod
    def sum(cls, field, where=None, params=None):
        """Sum field values."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        sql = f"SELECT SUM({field}) as total FROM {cls._table_name}"
        if where:
            sql += f" WHERE {where}"
        
        result = cls._db.query(sql, params or [])
        return result[0]['total'] if result and result[0]['total'] else 0
    
    @classmethod
    def avg(cls, field, where=None, params=None):
        """Average field values."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        sql = f"SELECT AVG({field}) as average FROM {cls._table_name}"
        if where:
            sql += f" WHERE {where}"
        
        result = cls._db.query(sql, params or [])
        return result[0]['average'] if result and result[0]['average'] else 0
    
    @classmethod
    def min(cls, field, where=None, params=None):
        """Minimum field value."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        sql = f"SELECT MIN({field}) as minimum FROM {cls._table_name}"
        if where:
            sql += f" WHERE {where}"
        
        result = cls._db.query(sql, params or [])
        return result[0]['minimum'] if result else None
    
    @classmethod
    def max(cls, field, where=None, params=None):
        """Maximum field value."""
        if not cls._db:
            raise RuntimeError("Database not set")
        
        sql = f"SELECT MAX({field}) as maximum FROM {cls._table_name}"
        if where:
            sql += f" WHERE {where}"
        
        result = cls._db.query(sql, params or [])
        return result[0]['maximum'] if result else None
    
    @classmethod
    def belongs_to(cls, name, model_class, foreign_key):
        """Define belongs_to relationship."""
        if not hasattr(cls, '_relationships'):
            cls._relationships = {}
        cls._relationships[name] = {
            'type': 'belongs_to',
            'model': model_class,
            'foreign_key': foreign_key
        }
    
    @classmethod
    def has_many(cls, name, model_class, foreign_key):
        """Define has_many relationship."""
        if not hasattr(cls, '_relationships'):
            cls._relationships = {}
        cls._relationships[name] = {
            'type': 'has_many',
            'model': model_class,
            'foreign_key': foreign_key
        }
    
    @classmethod
    def has_one(cls, name, model_class, foreign_key):
        """Define has_one relationship."""
        if not hasattr(cls, '_relationships'):
            cls._relationships = {}
        cls._relationships[name] = {
            'type': 'has_one',
            'model': model_class,
            'foreign_key': foreign_key
        }
    
    @classmethod
    def add_validator(cls, validator_func):
        """Add custom validator."""
        if not hasattr(cls, '_validators'):
            cls._validators = []
        cls._validators.append(validator_func)
    
    @classmethod
    def add_hook(cls, hook_name, func):
        """Add lifecycle hook."""
        if not hasattr(cls, '_hooks'):
            cls._hooks = {
                'before_save': [],
                'after_save': [],
                'before_delete': [],
                'after_delete': []
            }
        if hook_name in cls._hooks:
            cls._hooks[hook_name].append(func)
    
    def to_dict(self, include_relationships=False):
        """
        Convert model to dictionary.
        
        Args:
            include_relationships: Include relationship data
        
        Returns:
            Dictionary representation
        """
        data = {'id': self.id}
        data.update(self._data)
        
        if include_relationships:
            for name in self._relationships.keys():
                rel_data = self._load_relationship(name)
                if isinstance(rel_data, list):
                    data[name] = [r.to_dict() for r in rel_data]
                elif rel_data:
                    data[name] = rel_data.to_dict()
                else:
                    data[name] = None
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """
        Create model from dictionary.
        
        Args:
            data: Dictionary with field values
        
        Returns:
            Model instance
        """
        return cls(**data)
    
    def update(self, **kwargs):
        """
        Update model fields.
        
        Args:
            **kwargs: Field values to update
        
        Returns:
            Self for chaining
        """
        for key, value in kwargs.items():
            if key in self._fields:
                self._data[key] = value
        return self
    
    def reload(self):
        """Reload model from database."""
        if not self.id:
            return self
        
        fresh = self.find(self.id)
        if fresh:
            self._data = fresh._data
        return self


def define_model(table_name, fields):
    """
    Define ORM model dynamically.
    
    Args:
        table_name: Database table name
        fields: Dictionary of field definitions
    
    Returns:
        Model class
    
    Example:
        User = orm.define_model('users', {
            'name': orm.StringField(required=True),
            'email': orm.StringField(required=True),
            'active': orm.BooleanField(default=True)
        })
        
        User.set_database(db)
        User.create_table()
        
        user = User(name="John", email="john@example.com")
        user.save()
    """
    class_dict = {
        '_table_name': table_name,
        '_fields': fields
    }
    
    return type('DynamicModel', (Model,), class_dict)


def create_field(field_type, **kwargs):
    """
    Create field by type name.
    
    Args:
        field_type: Field type ('string', 'integer', 'boolean', 'datetime', 'foreign_key')
        **kwargs: Field options
    
    Returns:
        Field instance
    
    Example:
        name_field = orm.create_field('string', max_length=100, required=True)
    """
    field_types = {
        'string': StringField,
        'integer': IntegerField,
        'boolean': BooleanField,
        'datetime': DateTimeField,
        'foreign_key': ForeignKey,
    }
    field_class = field_types.get(field_type)
    if not field_class:
        raise ValueError(f"Unknown field type: {field_type}")
    return field_class(**kwargs)


def belongs_to(model_class, foreign_key=None):
    """
    Define belongs_to relationship.
    
    Args:
        model_class: Related model class
        foreign_key: Foreign key field name
    
    Returns:
        Relationship descriptor
    
    Example:
        Post.belongs_to(User, foreign_key='user_id')
    """
    return {'type': 'belongs_to', 'model': model_class, 'foreign_key': foreign_key}


def has_many(model_class, foreign_key=None):
    """
    Define has_many relationship.
    
    Args:
        model_class: Related model class
        foreign_key: Foreign key field name
    
    Returns:
        Relationship descriptor
    
    Example:
        User.has_many(Post, foreign_key='user_id')
    """
    return {'type': 'has_many', 'model': model_class, 'foreign_key': foreign_key}


def has_one(model_class, foreign_key=None):
    """
    Define has_one relationship.
    
    Args:
        model_class: Related model class
        foreign_key: Foreign key field name
    
    Returns:
        Relationship descriptor
    
    Example:
        User.has_one(Profile, foreign_key='user_id')
    """
    return {'type': 'has_one', 'model': model_class, 'foreign_key': foreign_key}


__all__ = [
    'Field',
    'StringField',
    'IntegerField',
    'BooleanField',
    'DateTimeField',
    'ForeignKey',
    'QueryBuilder',
    'Model',
    'define_model',
    'create_field',
    'belongs_to',
    'has_many',
    'has_one',
]
