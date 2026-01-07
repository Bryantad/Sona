"""
tree - Tree data structure for Sona stdlib

Provides tree operations:
- Node: Tree node
- Tree: Tree structure
- traverse: Tree traversal
"""


class Node:
    """Tree node."""
    
    def __init__(self, value, children=None):
        """Initialize node."""
        self.value = value
        self.children = children or []
        self.parent = None
        
        for child in self.children:
            child.parent = self
    
    def add_child(self, child):
        """Add child node."""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child):
        """Remove child node."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def is_leaf(self):
        """Check if node is leaf."""
        return len(self.children) == 0
    
    def is_root(self):
        """Check if node is root."""
        return self.parent is None
    
    def depth(self):
        """Get node depth."""
        if self.is_root():
            return 0
        return 1 + self.parent.depth()
    
    def height(self):
        """Get subtree height."""
        if self.is_leaf():
            return 0
        return 1 + max(child.height() for child in self.children)


class Tree:
    """Tree structure."""
    
    def __init__(self, root=None):
        """Initialize tree."""
        self.root = root
    
    def traverse_preorder(self, node=None):
        """
        Traverse tree in pre-order (root, children).
        
        Args:
            node: Starting node (default: root)
        
        Returns:
            List of node values
        
        Example:
            values = tree.traverse_preorder()
        """
        if node is None:
            node = self.root
        
        if node is None:
            return []
        
        result = [node.value]
        for child in node.children:
            result.extend(self.traverse_preorder(child))
        
        return result
    
    def traverse_postorder(self, node=None):
        """
        Traverse tree in post-order (children, root).
        
        Args:
            node: Starting node (default: root)
        
        Returns:
            List of node values
        """
        if node is None:
            node = self.root
        
        if node is None:
            return []
        
        result = []
        for child in node.children:
            result.extend(self.traverse_postorder(child))
        result.append(node.value)
        
        return result
    
    def traverse_levelorder(self):
        """
        Traverse tree level by level (BFS).
        
        Returns:
            List of node values
        """
        if self.root is None:
            return []
        
        result = []
        queue = [self.root]
        
        while queue:
            node = queue.pop(0)
            result.append(node.value)
            queue.extend(node.children)
        
        return result
    
    def find(self, value):
        """
        Find node by value.
        
        Args:
            value: Value to find
        
        Returns:
            Node or None
        """
        def search(node):
            if node is None:
                return None
            if node.value == value:
                return node
            for child in node.children:
                result = search(child)
                if result:
                    return result
            return None
        
        return search(self.root)
    
    def height(self):
        """Get tree height."""
        if self.root is None:
            return 0
        return self.root.height()
    
    def size(self):
        """Get number of nodes."""
        return len(self.traverse_preorder())


def create_node(value, children=None):
    """
    Create tree node.
    
    Args:
        value: Node value
        children: List of child nodes
    
    Returns:
        Node object
    
    Example:
        root = tree.create_node(1)
        child1 = tree.create_node(2)
        child2 = tree.create_node(3)
        root.add_child(child1)
        root.add_child(child2)
    """
    return Node(value, children)


def create(root=None):
    """
    Create tree.
    
    Args:
        root: Root node
    
    Returns:
        Tree object
    
    Example:
        t = tree.create(tree.create_node(1))
        values = t.traverse_preorder()
    """
    return Tree(root)


def from_dict(data, value_key='value', children_key='children'):
    """
    Create tree from dictionary.
    
    Args:
        data: Dictionary with nested structure
        value_key: Key for node value
        children_key: Key for children list
    
    Returns:
        Tree object
    
    Example:
        data = {'value': 1, 'children': [
            {'value': 2},
            {'value': 3}
        ]}
        t = from_dict(data)
    """
    def build_node(node_data):
        if not isinstance(node_data, dict):
            return None
        
        value = node_data.get(value_key)
        children_data = node_data.get(children_key, [])
        children = [build_node(child) for child in children_data]
        children = [c for c in children if c is not None]
        
        return Node(value, children)
    
    root = build_node(data)
    return Tree(root)


def to_dict(tree, value_key='value', children_key='children'):
    """
    Convert tree to dictionary.
    
    Args:
        tree: Tree object
        value_key: Key for node value
        children_key: Key for children list
    
    Returns:
        Dictionary representation
    
    Example:
        t = create(create_node(1))
        data = to_dict(t)
    """
    def build_dict(node):
        if node is None:
            return None
        
        result = {value_key: node.value}
        if node.children:
            result[children_key] = [
                build_dict(child) for child in node.children
            ]
        return result
    
    return build_dict(tree.root)


def map_tree(tree, func):
    """
    Map function over all node values.
    
    Args:
        tree: Tree object
        func: Function to apply
    
    Returns:
        New tree with transformed values
    
    Example:
        t = create(create_node(1))
        t2 = map_tree(t, lambda x: x * 2)
    """
    def map_node(node):
        if node is None:
            return None
        
        new_children = [map_node(child) for child in node.children]
        return Node(func(node.value), new_children)
    
    return Tree(map_node(tree.root))


def filter_tree(tree, predicate):
    """
    Filter tree nodes by predicate.
    
    Args:
        tree: Tree object
        predicate: Filter function
    
    Returns:
        New tree with filtered nodes
    
    Example:
        t = create(create_node(5))
        t2 = filter_tree(t, lambda x: x > 3)
    """
    def filter_node(node):
        if node is None:
            return None
        
        if not predicate(node.value):
            return None
        
        new_children = [filter_node(child) for child in node.children]
        new_children = [c for c in new_children if c is not None]
        
        return Node(node.value, new_children)
    
    return Tree(filter_node(tree.root))


def find_path(tree, value):
    """
    Find path from root to node with value.
    
    Args:
        tree: Tree object
        value: Value to find
    
    Returns:
        List of values from root to target, or None
    
    Example:
        path = find_path(tree, 5)
    """
    def search(node, target, path):
        if node is None:
            return None
        
        path = path + [node.value]
        
        if node.value == target:
            return path
        
        for child in node.children:
            result = search(child, target, path)
            if result:
                return result
        
        return None
    
    return search(tree.root, value, [])


def leaves(tree):
    """
    Get all leaf nodes.
    
    Args:
        tree: Tree object
    
    Returns:
        List of leaf node values
    
    Example:
        leaf_values = leaves(tree)
    """
    def collect_leaves(node):
        if node is None:
            return []
        
        if node.is_leaf():
            return [node.value]
        
        result = []
        for child in node.children:
            result.extend(collect_leaves(child))
        
        return result
    
    return collect_leaves(tree.root)


def ancestors(tree, value):
    """
    Get all ancestors of node with value.
    
    Args:
        tree: Tree object
        value: Node value
    
    Returns:
        List of ancestor values from root to parent
    
    Example:
        anc = ancestors(tree, 5)
    """
    path = find_path(tree, value)
    if path:
        return path[:-1]
    return []


def descendants(tree, value):
    """
    Get all descendants of node with value.
    
    Args:
        tree: Tree object
        value: Node value
    
    Returns:
        List of descendant values
    
    Example:
        desc = descendants(tree, 1)
    """
    node = tree.find(value)
    if node is None:
        return []
    
    subtree = Tree(node)
    result = subtree.traverse_preorder()
    return result[1:] if result else []


def is_balanced(tree):
    """
    Check if tree is balanced.
    
    A tree is balanced if heights of subtrees differ by at most 1.
    
    Args:
        tree: Tree object
    
    Returns:
        Boolean
    
    Example:
        balanced = is_balanced(tree)
    """
    def check_balance(node):
        if node is None:
            return True, 0
        
        if node.is_leaf():
            return True, 0
        
        heights = []
        for child in node.children:
            balanced, height = check_balance(child)
            if not balanced:
                return False, 0
            heights.append(height)
        
        if heights:
            max_h = max(heights)
            min_h = min(heights)
            if max_h - min_h > 1:
                return False, 0
            return True, max_h + 1
        
        return True, 0
    
    balanced, _ = check_balance(tree.root)
    return balanced


__all__ = [
    "Node",
    "Tree",
    "create_node",
    "create",
    "from_dict",
    "to_dict",
    "map_tree",
    "filter_tree",
    "find_path",
    "leaves",
    "ancestors",
    "descendants",
    "is_balanced",
]
