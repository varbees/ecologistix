from smolagents import Tool
import requests

class WeatherTool(Tool):
    """
    Fetches weather data from Open-Meteo API
    Returns: {
        max_wind_speed_kn: float,
        risk_level: str,
        summary: str
    }
    """
    name = "fetch_weather"
    description = "Get current/forecast weather for given lat/lon"
    inputs = {
        "latitude": {"type": "number", "description": "Latitude"},
        "longitude": {"type": "number", "description": "Longitude"},
        "days_ahead": {"type": "integer", "description": "Forecast days (1-7)", "nullable": True}
    }
    output_type = "object"
    
    def forward(self, latitude: float, longitude: float, days_ahead: int = 3):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "wind_speed_10m,wave_height,precipitation",
            "forecast_days": min(days_ahead, 7)
        }
        try:
            response = requests.get(url, params=params).json()
            
            # Extract worst-case values
            if 'hourly' not in response:
                return {"error": "Weather data unavailable"}
                
            wind_speeds = response['hourly']['wind_speed_10m']
            max_wind = max(wind_speeds) if wind_speeds else 0
            risk_level = self._assess_risk(max_wind)
            
            return {
                "max_wind_speed_kn": max_wind * 1.944,  # m/s to knots
                "risk_level": risk_level,
                "summary": f"Max wind {max_wind} m/s in next {days_ahead} days"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _assess_risk(self, wind_m_s: float) -> str:
        if wind_m_s > 20: return "CRITICAL"
        elif wind_m_s > 15: return "HIGH"
        elif wind_m_s > 10: return "MEDIUM"
        else: return "LOW"
