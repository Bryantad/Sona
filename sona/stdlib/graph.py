"""
graph - Graph data structure for Sona stdlib

Provides graph operations:
- Graph: Directed/undirected graph
- add_node/add_edge: Build graph
- shortest_path: Pathfinding
- neighbors: Get adjacent nodes
"""

from collections import deque, defaultdict


class Graph:
    """Graph data structure."""
    
    def __init__(self, directed=False):
        """Initialize graph."""
        self.directed = directed
        self.nodes = set()
        self.edges = defaultdict(dict)
    
    def add_node(self, node):
        """Add node to graph."""
        self.nodes.add(node)
    
    def add_edge(self, from_node, to_node, weight=1):
        """
        Add edge between nodes.
        
        Args:
            from_node: Source node
            to_node: Target node
            weight: Edge weight
        
        Example:
            g = graph.Graph()
            g.add_edge("A", "B", weight=5)
        """
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        self.edges[from_node][to_node] = weight
        
        if not self.directed:
            self.edges[to_node][from_node] = weight
    
    def remove_node(self, node):
        """Remove node and its edges."""
        self.nodes.discard(node)
        self.edges.pop(node, None)
        
        for edges in self.edges.values():
            edges.pop(node, None)
    
    def remove_edge(self, from_node, to_node):
        """Remove edge."""
        if from_node in self.edges:
            self.edges[from_node].pop(to_node, None)
        
        if not self.directed and to_node in self.edges:
            self.edges[to_node].pop(from_node, None)
    
    def neighbors(self, node):
        """Get adjacent nodes."""
        return list(self.edges.get(node, {}).keys())
    
    def has_edge(self, from_node, to_node):
        """Check if edge exists."""
        return to_node in self.edges.get(from_node, {})
    
    def get_weight(self, from_node, to_node):
        """Get edge weight."""
        return self.edges.get(from_node, {}).get(to_node)
    
    def shortest_path(self, start, end):
        """
        Find shortest path using BFS (unweighted) or Dijkstra (weighted).
        
        Args:
            start: Start node
            end: End node
        
        Returns:
            List of nodes in path, or None if no path
        
        Example:
            path = g.shortest_path("A", "D")
            # ["A", "B", "C", "D"]
        """
        if start not in self.nodes or end not in self.nodes:
            return None
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            node, path = queue.popleft()
            
            if node == end:
                return path
            
            for neighbor in self.neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def has_cycle(self):
        """Check if graph has cycle."""
        visited = set()
        rec_stack = set()
        
        def dfs(node, parent=None):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.neighbors(node):
                if neighbor not in visited:
                    if dfs(neighbor, node):
                        return True
                elif neighbor in rec_stack:
                    if self.directed or neighbor != parent:
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def to_dict(self):
        """Convert graph to dictionary."""
        return {
            'directed': self.directed,
            'nodes': list(self.nodes),
            'edges': [
                {'from': from_node, 'to': to_node, 'weight': weight}
                for from_node, edges in self.edges.items()
                for to_node, weight in edges.items()
            ]
        }


def create(directed=False):
    """
    Create new graph.
    
    Args:
        directed: Create directed graph
    
    Returns:
        Graph object
    
    Example:
        g = graph.create()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        path = g.shortest_path("A", "C")
    """
    return Graph(directed)


def dfs(graph, start, visited=None):
    """
    Depth-first search traversal.
    
    Args:
        graph: Graph object
        start: Starting node
        visited: Set of visited nodes (for recursion)
    
    Returns:
        List of nodes in DFS order
    
    Example:
        nodes = graph.dfs(g, "A")
    """
    if visited is None:
        visited = set()
    
    result = []
    
    if start not in visited:
        visited.add(start)
        result.append(start)
        
        for neighbor in graph.neighbors(start):
            result.extend(dfs(graph, neighbor, visited))
    
    return result


def bfs(graph, start):
    """
    Breadth-first search traversal.
    
    Args:
        graph: Graph object
        start: Starting node
    
    Returns:
        List of nodes in BFS order
    
    Example:
        nodes = graph.bfs(g, "A")
    """
    visited = {start}
    queue = deque([start])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return result


def is_connected(graph):
    """
    Check if graph is connected.
    
    Args:
        graph: Graph object
    
    Returns:
        bool: True if connected
    
    Example:
        connected = graph.is_connected(g)
    """
    if not graph.nodes:
        return True
    
    start = next(iter(graph.nodes))
    visited = set(bfs(graph, start))
    
    return len(visited) == len(graph.nodes)


def find_components(graph):
    """
    Find connected components.
    
    Args:
        graph: Graph object
    
    Returns:
        List of components (each is a set of nodes)
    
    Example:
        components = graph.find_components(g)
    """
    visited = set()
    components = []
    
    for node in graph.nodes:
        if node not in visited:
            component = set(bfs(graph, node))
            visited.update(component)
            components.append(component)
    
    return components


def topological_sort(graph):
    """
    Topological sort of directed acyclic graph.
    
    Args:
        graph: Directed graph object
    
    Returns:
        List of nodes in topological order, or None if has cycle
    
    Example:
        order = graph.topological_sort(dag)
    """
    if not graph.directed:
        raise ValueError("Topological sort requires directed graph")
    
    if graph.has_cycle():
        return None
    
    in_degree = {node: 0 for node in graph.nodes}
    
    for node in graph.nodes:
        for neighbor in graph.neighbors(node):
            in_degree[neighbor] += 1
    
    queue = deque([node for node in graph.nodes if in_degree[node] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph.neighbors(node):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return result


def dijkstra(graph, start):
    """
    Dijkstra's shortest path algorithm.
    
    Args:
        graph: Graph object with weights
        start: Starting node
    
    Returns:
        Dict of node -> shortest distance from start
    
    Example:
        distances = graph.dijkstra(g, "A")
    """
    import heapq
    
    distances = {node: float('inf') for node in graph.nodes}
    distances[start] = 0
    
    pq = [(0, start)]
    visited = set()
    
    while pq:
        dist, node = heapq.heappop(pq)
        
        if node in visited:
            continue
        
        visited.add(node)
        
        for neighbor in graph.neighbors(node):
            weight = graph.get_weight(node, neighbor)
            new_dist = dist + weight
            
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    
    return distances


def degree(graph, node):
    """
    Get degree of a node.
    
    Args:
        graph: Graph object
        node: Node
    
    Returns:
        Degree (number of edges)
    
    Example:
        deg = graph.degree(g, "A")
    """
    return len(graph.neighbors(node))


def from_dict(data):
    """
    Create graph from dictionary.
    
    Args:
        data: Dict with 'directed', 'nodes', 'edges'
    
    Returns:
        Graph object
    
    Example:
        g = graph.from_dict({"directed": False, "nodes": ["A", "B"], ...})
    """
    g = Graph(directed=data.get('directed', False))
    
    for node in data.get('nodes', []):
        g.add_node(node)
    
    for edge in data.get('edges', []):
        g.add_edge(edge['from'], edge['to'], edge.get('weight', 1))
    
    return g


__all__ = [
    'Graph', 'create', 'dfs', 'bfs', 'is_connected',
    'find_components', 'topological_sort', 'dijkstra', 'degree', 'from_dict'
]
