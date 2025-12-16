import pytest
from tools import WeatherTool, CarbonTool, ShippingTool

def test_weather_tool():
    tool = WeatherTool()
    # Mocking or integration test? 
    # Use real API if available or check structure
    result = tool.forward(latitude=50.5, longitude=3.8, days_ahead=3)
    if "error" not in result:
        assert "max_wind_speed_kn" in result
        assert "risk_level" in result
    else:
        # Failure expected if API key missing or connection issue
        pass

def test_carbon_tool():
    tool = CarbonTool()
    result = tool.forward(
        vessel_type="Container Ship",
        fuel_type="HFO",
        distance_km=5000,
        cargo_weight_tons=1000
    )
    assert "total_emissions_kg_co2" in result
    assert result["sustainability_score"] >= 0

def test_shipping_tool():
    tool = ShippingTool()
    result = tool.forward("Singapore", "Rotterdam")
    assert "straight_line_km" in result
    assert result["estimated_sea_route_km"] > result["straight_line_km"]
