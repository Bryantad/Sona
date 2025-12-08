"""
permissions - Permission/authorization system for Sona stdlib

Provides permission management:
- Permission: Define permissions
- Role: Role-based access
- check: Check permissions
"""


class Permission:
    """Permission definition."""
    
    def __init__(self, name, description=''):
        """Initialize permission."""
        self.name = name
        self.description = description
    
    def __str__(self):
        """String representation."""
        return self.name
    
    def __eq__(self, other):
        """Equality check."""
        return isinstance(other, Permission) and self.name == other.name
    
    def __hash__(self):
        """Hash for set/dict usage."""
        return hash(self.name)


class Role:
    """Role with permissions."""
    
    def __init__(self, name, permissions=None):
        """Initialize role."""
        self.name = name
        self.permissions = set(permissions or [])
    
    def add(self, permission):
        """Add permission to role."""
        self.permissions.add(permission)
    
    def remove(self, permission):
        """Remove permission from role."""
        self.permissions.discard(permission)
    
    def has(self, permission):
        """Check if role has permission."""
        return permission in self.permissions
    
    def __str__(self):
        """String representation."""
        return f"{self.name} ({len(self.permissions)} permissions)"


class User:
    """User with roles and permissions."""
    
    def __init__(self, id, roles=None, permissions=None):
        """Initialize user."""
        self.id = id
        self.roles = set(roles or [])
        self.permissions = set(permissions or [])
    
    def add_role(self, role):
        """Add role to user."""
        self.roles.add(role)
    
    def remove_role(self, role):
        """Remove role from user."""
        self.roles.discard(role)
    
    def add_permission(self, permission):
        """Add direct permission to user."""
        self.permissions.add(permission)
    
    def remove_permission(self, permission):
        """Remove direct permission from user."""
        self.permissions.discard(permission)
    
    def can(self, permission):
        """
        Check if user has permission.
        
        Args:
            permission: Permission to check
        
        Returns:
            True if user has permission
        
        Example:
            if user.can("posts.delete"):
                delete_post()
        """
        # Check direct permissions
        if permission in self.permissions:
            return True
        
        # Check role permissions
        for role in self.roles:
            if role.has(permission):
                return True
        
        return False


class PermissionManager:
    """Manage permissions system."""
    
    def __init__(self):
        """Initialize manager."""
        self.permissions = {}
        self.roles = {}
        self.users = {}
    
    def define_permission(self, name, description=''):
        """Define new permission."""
        perm = Permission(name, description)
        self.permissions[name] = perm
        return perm
    
    def create_role(self, name, permissions=None):
        """Create new role."""
        perm_objects = [self.permissions.get(p, Permission(p)) for p in (permissions or [])]
        role = Role(name, perm_objects)
        self.roles[name] = role
        return role
    
    def create_user(self, id, roles=None, permissions=None):
        """Create user."""
        role_objects = [self.roles.get(r, Role(r)) for r in (roles or [])]
        perm_objects = [self.permissions.get(p, Permission(p)) for p in (permissions or [])]
        user = User(id, role_objects, perm_objects)
        self.users[id] = user
        return user
    
    def check(self, user_id, permission_name):
        """Check if user has permission."""
        user = self.users.get(user_id)
        if not user:
            return False
        
        permission = self.permissions.get(permission_name, Permission(permission_name))
        return user.can(permission)


def create_manager():
    """
    Create permission manager.
    
    Returns:
        PermissionManager object
    
    Example:
        mgr = permissions.create_manager()
        
        # Define permissions
        mgr.define_permission("posts.create")
        mgr.define_permission("posts.delete")
        
        # Create roles
        admin = mgr.create_role("admin", ["posts.create", "posts.delete"])
        editor = mgr.create_role("editor", ["posts.create"])
        
        # Create user
        user = mgr.create_user("user123", roles=["editor"])
        
        # Check permission
        can_delete = mgr.check("user123", "posts.delete")  # False
    """
    return PermissionManager()
