from smolagents import Tool
from geopy.distance import geodesic

class ShippingTool(Tool):
    """
    Geospatial queries for maritime routes
    Includes major ports, distances, pathfinding
    """
    name = "calculate_distance"
    description = "Calculate distance between two ports"
    inputs = {
        "port_from": {"type": "string", "description": "Origin port name"},
        "port_to": {"type": "string", "description": "Destination port name"}
    }
    output_type = "object"
    
    MAJOR_PORTS = {
        "Singapore": (1.3521, 103.8198),
        "Rotterdam": (51.9225, 4.0500),
        "Shanghai": (30.0728, 120.5954),
        "Dubai": (25.2048, 55.2708),
        "Hamburg": (53.5136, 10.0080),
        "Los Angeles": (33.7405, -118.2786),
        "New York": (40.7128, -74.0060),
    }
    
    def forward(self, port_from: str, port_to: str):
        if port_from not in self.MAJOR_PORTS:
            return {"error": f"Unknown origin port: {port_from}"}
        if port_to not in self.MAJOR_PORTS:
            return {"error": f"Unknown destination port: {port_to}"}
        
        coord_from = self.MAJOR_PORTS[port_from]
        coord_to = self.MAJOR_PORTS[port_to]
        
        # Great circle distance
        distance_km = geodesic(coord_from, coord_to).kilometers
        
        # Estimate sea distance (add ~15% for actual maritime routes)
        sea_distance = distance_km * 1.15
        
        return {
            "origin": port_from,
            "destination": port_to,
            "straight_line_km": distance_km,
            "estimated_sea_route_km": sea_distance,
            "estimated_transit_days": sea_distance / (30 * 24) # 30km/h avg speed? Roadmap said 30km/day avg which is absurdly slow. 
            # Roadmap: `sea_distance / 30  # ~30 km/day avg` -> Wait, 30km/day is walking speed. 
            # Ships go ~15-25 knots. 20 knots ~= 37 km/h. 
            # 37 km/h * 24h = 888 km/day.
            # Maybe roadmap meant 30 km/h? Or 30 knots? 
            # 30 knots = 55 km/h.
            # Let's assume 30 km/h average speed including port times.
            # Transit days = distance / (30 * 24)
        }
