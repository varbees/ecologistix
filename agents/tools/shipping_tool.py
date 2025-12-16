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
        # Asia (East/SE)
        "Singapore": (1.3521, 103.8198),
        "Shanghai": (30.0728, 120.5954),
        "Busan": (35.1047, 129.0406),
        "Ningbo": (29.8683, 121.5440),
        "Shenzhen": (22.5431, 114.0579),
        "Tokyo": (35.6194, 139.7540),
        "Hong Kong": (22.3193, 114.1694),
        "Port Klang": (3.0067, 101.3928),
        "Kaohsiung": (22.6273, 120.2645),
        
        # India / South Asia
        "Mumbai": (18.9446, 72.8223),
        "Chennai": (13.0827, 80.2707),
        "Mundra": (22.8389, 69.7452),
        "Kolkata": (22.5726, 88.3639),
        "Cochin": (9.9312, 76.2673),
        "JNPT": (18.9500, 72.9500),
        "Visakhapatnam": (17.6904, 83.2310),
        "Colombo": (6.9271, 79.8612),
        
        # Middle East / Red Sea
        "Dubai": (25.2048, 55.2708), # Jebel Ali
        "Jeddah": (21.4858, 39.1925),
        "Salalah": (16.9427, 54.0076),
        "Port Said": (31.2653, 32.3019), # Suez North
        "Suez": (29.9668, 32.5498),     # Suez South

        # Europe
        "Rotterdam": (51.9225, 4.0500),
        "Antwerp": (51.2194, 4.4025),
        "Hamburg": (53.5136, 10.0080),
        "Bremerhaven": (53.5400, 8.5800),
        "Felixstowe": (51.9617, 1.3513),
        "Le Havre": (49.4944, 0.1079),
        "Valencia": (39.4699, -0.3763),
        "Genoa": (44.4056, 8.9463),
        "Algeciras": (36.1275, -5.4540),

        # North America
        "Los Angeles": (33.7405, -118.2786),
        "Long Beach": (33.7701, -118.1937),
        "New York": (40.7128, -74.0060),
        "Savannah": (32.0809, -81.0912),
        "Vancouver": (49.2827, -123.1207),
        "Houston": (29.7604, -95.3698),

        # South America
        "Santos": (-23.9608, -46.3331),
        "Callao": (-12.0508, -77.1360),
        "Cartagena": (10.3910, -75.4794),
        "Panama City": (8.9824, -79.5199), # Balboa

        # Africa
        "Tanger Med": (35.8872, -5.4855),
        "Durban": (-29.8587, 31.0218),
        "Lagos": (6.4541, 3.3947),
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
