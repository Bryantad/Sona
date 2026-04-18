"""
migration - Enhanced database migration system for Sona stdlib

Comprehensive migration management:
- create: Create migration files
- run: Execute pending migrations
- rollback: Revert migrations
- status: Check migration status
- Versioning and tracking
- Auto-generation from models
- Batch operations
"""

import os
import time
import json
from datetime import datetime


class Migration:
    """Database migration."""
    
    def __init__(self, name, up_sql, down_sql):
        """Initialize migration."""
        self.name = name
        self.timestamp = int(time.time())
        self.up_sql = up_sql
        self.down_sql = down_sql
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'name': self.name,
            'timestamp': self.timestamp,
            'up_sql': self.up_sql,
            'down_sql': self.down_sql
        }


class MigrationManager:
    """Manage database migrations."""
    
    def __init__(self, db, migrations_dir='migrations'):
        """Initialize manager."""
        self.db = db
        self.migrations_dir = migrations_dir
        
        # Create migrations directory
        os.makedirs(migrations_dir, exist_ok=True)
        
        # Create migrations table
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                applied_at INTEGER NOT NULL
            )
        ''')
    
    def create(self, name, up_sql, down_sql):
        """Create migration file."""
        migration = Migration(name, up_sql, down_sql)
        
        filename = f"{migration.timestamp}_{name}.json"
        filepath = os.path.join(self.migrations_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(migration.to_dict(), f, indent=2)
        
        return migration
    
    def get_pending(self):
        """Get pending migrations."""
        # Get applied migrations
        applied = self.db.query('SELECT name FROM migrations')
        applied_names = {row['name'] for row in applied}
        
        # Get all migration files
        files = sorted([f for f in os.listdir(self.migrations_dir) if f.endswith('.json')])
        
        pending = []
        for filename in files:
            filepath = os.path.join(self.migrations_dir, filename)
            with open(filepath, 'r') as f:
                migration_data = json.load(f)
            
            if migration_data['name'] not in applied_names:
                pending.append(migration_data)
        
        return pending
    
    def run(self):
        """Run pending migrations."""
        pending = self.get_pending()
        
        for migration in pending:
            # Execute up SQL
            self.db.execute(migration['up_sql'])
            
            # Record migration
            self.db.execute(
                'INSERT INTO migrations (name, timestamp, applied_at) VALUES (?, ?, ?)',
                [migration['name'], migration['timestamp'], int(time.time())]
            )
        
        return len(pending)
    
    def rollback(self, steps=1):
        """
        Rollback last N migrations.
        
        Args:
            steps: Number of migrations to rollback
        
        Returns:
            Number of migrations rolled back
        """
        rolled_back = 0
        
        for _ in range(steps):
            # Get last migration
            results = self.db.query(
                'SELECT * FROM migrations ORDER BY applied_at DESC LIMIT 1'
            )
            
            if not results:
                break
            
            last = results[0]
            
            # Find migration file
            files = [f for f in os.listdir(self.migrations_dir) 
                    if f.endswith('.json')]
            for filename in files:
                filepath = os.path.join(self.migrations_dir, filename)
                with open(filepath, 'r') as f:
                    migration = json.load(f)
                
                if migration['name'] == last['name']:
                    # Execute down SQL
                    self.db.execute(migration['down_sql'])
                    
                    # Remove from migrations table
                    self.db.execute('DELETE FROM migrations WHERE name = ?',
                                  [last['name']])
                    
                    rolled_back += 1
                    break
        
        return rolled_back
    
    def status(self):
        """
        Get migration status.
        
        Returns:
            Dict with applied and pending migrations
        """
        applied = self.db.query('SELECT * FROM migrations ORDER BY applied_at')
        pending = self.get_pending()
        
        return {
            'applied': [{'name': m['name'], 'timestamp': m['timestamp'], 
                        'applied_at': m['applied_at']} for m in applied],
            'pending': [{'name': m['name'], 'timestamp': m['timestamp']} 
                       for m in pending],
            'applied_count': len(applied),
            'pending_count': len(pending)
        }
    
    def reset(self):
        """Reset all migrations (run all down migrations)."""
        # Get all applied migrations in reverse order
        applied = self.db.query(
            'SELECT * FROM migrations ORDER BY applied_at DESC'
        )
        
        for migration_record in applied:
            # Find migration file
            files = [f for f in os.listdir(self.migrations_dir) 
                    if f.endswith('.json')]
            for filename in files:
                filepath = os.path.join(self.migrations_dir, filename)
                with open(filepath, 'r') as f:
                    migration = json.load(f)
                
                if migration['name'] == migration_record['name']:
                    # Execute down SQL
                    self.db.execute(migration['down_sql'])
                    break
        
        # Clear migrations table
        self.db.execute('DELETE FROM migrations')
        return len(applied)
    
    def refresh(self):
        """Reset and re-run all migrations."""
        self.reset()
        return self.run()
    
    def run_to(self, target_migration):
        """
        Run migrations up to specific migration.
        
        Args:
            target_migration: Name of target migration
        
        Returns:
            Number of migrations run
        """
        pending = self.get_pending()
        count = 0
        
        for migration in pending:
            # Execute up SQL
            self.db.execute(migration['up_sql'])
            
            # Record migration
            self.db.execute(
                'INSERT INTO migrations (name, timestamp, applied_at) '
                'VALUES (?, ?, ?)',
                [migration['name'], migration['timestamp'], int(time.time())]
            )
            count += 1
            
            if migration['name'] == target_migration:
                break
        
        return count
    
    def rollback_to(self, target_migration):
        """
        Rollback to specific migration.
        
        Args:
            target_migration: Name of target migration
        
        Returns:
            Number of migrations rolled back
        """
        applied = self.db.query(
            'SELECT * FROM migrations ORDER BY applied_at DESC'
        )
        
        count = 0
        for migration_record in applied:
            if migration_record['name'] == target_migration:
                break
            
            # Find and execute down migration
            files = [f for f in os.listdir(self.migrations_dir) 
                    if f.endswith('.json')]
            for filename in files:
                filepath = os.path.join(self.migrations_dir, filename)
                with open(filepath, 'r') as f:
                    migration = json.load(f)
                
                if migration['name'] == migration_record['name']:
                    self.db.execute(migration['down_sql'])
                    self.db.execute('DELETE FROM migrations WHERE name = ?',
                                  [migration_record['name']])
                    count += 1
                    break
        
        return count
    
    def get_version(self):
        """
        Get current migration version (last applied migration).
        
        Returns:
            Name of last applied migration or None
        """
        results = self.db.query(
            'SELECT name FROM migrations ORDER BY applied_at DESC LIMIT 1'
        )
        return results[0]['name'] if results else None
    
    def has_pending(self):
        """Check if there are pending migrations."""
        return len(self.get_pending()) > 0
    
    def is_current(self):
        """Check if all migrations are applied."""
        return not self.has_pending()
    
    def generate_from_model(self, model_class, operation='create'):
        """
        Auto-generate migration from model.
        
        Args:
            model_class: Model class with _table_name and _fields
            operation: 'create' or 'drop'
        
        Returns:
            Migration object
        """
        table = model_class._table_name
        
        if operation == 'create':
            # Generate CREATE TABLE
            fields = ['id INTEGER PRIMARY KEY AUTOINCREMENT']
            for name, field in model_class._fields.items():
                field_def = f"{name} {field.field_type}"
                if field.required:
                    field_def += " NOT NULL"
                fields.append(field_def)
            
            up_sql = f"CREATE TABLE {table} ({', '.join(fields)})"
            down_sql = f"DROP TABLE {table}"
            
            migration_name = f"create_{table}_table"
        
        elif operation == 'drop':
            up_sql = f"DROP TABLE {table}"
            down_sql = ""  # Can't easily recreate
            migration_name = f"drop_{table}_table"
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return self.create(migration_name, up_sql, down_sql)
    
    def list_migrations(self):
        """
        List all migration files.
        
        Returns:
            List of migration filenames
        """
        files = sorted([f for f in os.listdir(self.migrations_dir) 
                       if f.endswith('.json')])
        return files


# Global migration manager
_default_manager = None


def create_manager(db, migrations_dir='migrations'):
    """
    Create migration manager.
    
    Args:
        db: Database connection
        migrations_dir: Migrations directory
    
    Returns:
        MigrationManager object
    
    Example:
        mgr = migration.create_manager(db)
        mgr.create("add_users_table",
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",
            "DROP TABLE users"
        )
        mgr.run()
    """
    global _default_manager
    _default_manager = MigrationManager(db, migrations_dir)
    return _default_manager


def get_manager():
    """Get or create default migration manager."""
    if _default_manager is None:
        raise RuntimeError("Migration manager not initialized. "
                         "Call create_manager() first.")
    return _default_manager


# Standalone API functions (use default manager)

def create(name, up_sql, down_sql):
    """Create migration using default manager."""
    return get_manager().create(name, up_sql, down_sql)


def run():
    """Run pending migrations using default manager."""
    return get_manager().run()


def rollback(steps=1):
    """Rollback migrations using default manager."""
    return get_manager().rollback(steps)


def status():
    """Get migration status using default manager."""
    return get_manager().status()


def reset():
    """Reset all migrations using default manager."""
    return get_manager().reset()


def refresh():
    """Refresh (reset and re-run) migrations using default manager."""
    return get_manager().refresh()


def run_to(target):
    """Run to specific migration using default manager."""
    return get_manager().run_to(target)


def rollback_to(target):
    """Rollback to specific migration using default manager."""
    return get_manager().rollback_to(target)


def get_version():
    """Get current version using default manager."""
    return get_manager().get_version()


def has_pending():
    """Check for pending migrations using default manager."""
    return get_manager().has_pending()


def is_current():
    """Check if all migrations applied using default manager."""
    return get_manager().is_current()


def generate_from_model(model_class, operation='create'):
    """Generate migration from model using default manager."""
    return get_manager().generate_from_model(model_class, operation)


def list_migrations():
    """List all migrations using default manager."""
    return get_manager().list_migrations()


def get_pending():
    """Get pending migrations using default manager."""
    return get_manager().get_pending()
