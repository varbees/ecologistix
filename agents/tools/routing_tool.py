from smolagents import Tool
import networkx as nx
from typing import List, Dict, Any

class RoutingTool(Tool):
    """
    Maritime routing engine using graph pathfinding.
    Calculates shortest paths between ports considering distance.
    """
    name = "find_route"
    description = "Find the optimal maritime route between two ports"
    inputs = {
        "origin": {"type": "string", "description": "Origin port name"},
        "destination": {"type": "string", "description": "Destination port name"},
        "avoid_nodes": {"type": "array", "items": {"type": "string"}, "description": "List of ports or regions to avoid", "nullable": True}
    }
    output_type = "object"
    
    def __init__(self):
        super().__init__()
        self.graph = self._build_graph()

    def _build_graph(self):
        G = nx.Graph()
        # Define ports with coordinates
        ports = {
            "Singapore": (1.3521, 103.8198),
            "Rotterdam": (51.9225, 4.0500),
            "Shanghai": (30.0728, 120.5954),
            "Dubai": (25.2048, 55.2708),
            "Hamburg": (53.5136, 10.0080),
            "Los Angeles": (33.7405, -118.2786),
            "New York": (40.7128, -74.0060),
            "Mumbai": (18.9446, 72.8223),
            "Chennai": (13.0827, 80.2707),
            "Mundra": (22.8389, 69.7452),
            "Kolkata": (22.5726, 88.3639),
            "Cochin": (9.9312, 76.2673),
            "JNPT": (18.9500, 72.9500),
            "Suez Canal": (30.5852, 32.2654),
            "Cape of Good Hope": (-34.3568, 18.4724),
            "Malacca Strait": (4.1936, 100.1739),
            "Panama Canal": (9.0768, -79.7196)
        }
        
        for port, coords in ports.items():
            G.add_node(port, pos=coords)
            
        # Define routes (edges) with approximate distances (km)
        # Verify these in production with real data
        routes = [
            ("Shanghai", "Singapore", 4200),
            ("Singapore", "Mumbai", 3900),
            ("Singapore", "Chennai", 2900),
            ("Mumbai", "Dubai", 1930),
            ("Dubai", "Suez Canal", 2600),
            ("Suez Canal", "Rotterdam", 6400), # Via Med
            ("Rotterdam", "Hamburg", 500),
            ("Shanghai", "Los Angeles", 10400),
            ("Los Angeles", "Panama Canal", 5400),
            ("Panama Canal", "New York", 3700),
            ("New York", "Rotterdam", 6100),
            # Alternative Route avoiding Suez (Cape Route)
            ("Singapore", "Cape of Good Hope", 9600),
            ("Cape of Good Hope", "Rotterdam", 12800),
            # Indian Coastal
            ("Mundra", "Mumbai", 800),
            ("Mumbai", "Cochin", 1100),
            ("Cochin", "Chennai", 1500), # Around Sri Lanka technically
            ("Chennai", "Kolkata", 1400),
        ]
        
        for u, v, dist in routes:
            G.add_edge(u, v, weight=dist)
            
        return G

    def forward(self, origin: str, destination: str, avoid_nodes: List[str] = None):
        if origin not in self.graph or destination not in self.graph:
            return {"error": f"Port not found in network: {origin} or {destination}"}
        
        # Create a temporary view of graph logic for avoidance
        # Ideally we don't modify self.graph, but filter paths
        # NetworkX shortest_path supports standard weight
        
        if avoid_nodes:
            # Check if avoid nodes exist
            valid_avoids = [n for n in avoid_nodes if n in self.graph]
            if valid_avoids:
                # Use a subgraph view without the avoided nodes
                view = self.graph.copy()
                view.remove_nodes_from(valid_avoids)
                try:
                    path = nx.shortest_path(view, source=origin, target=destination, weight="weight")
                    dist = nx.path_weight(view, path, weight="weight")
                    return {
                        "route": path,
                        "total_distance_km": dist,
                        "note": f"Route avoids {valid_avoids}"
                    }
                except nx.NetworkXNoPath:
                    return {"error": "No path found with avoidance constraints"}
        
        # Standard shortest path
        try:
            path = nx.shortest_path(self.graph, source=origin, target=destination, weight="weight")
            dist = nx.path_weight(self.graph, path, weight="weight")
            return {
                "route": path,
                "total_distance_km": dist,
                "note": "Standard shortest route"
            }
        except nx.NetworkXNoPath:
            return {"error": "No path found"}
