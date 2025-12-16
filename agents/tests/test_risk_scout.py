import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from risk_scout import RiskScout

@pytest.mark.asyncio
async def test_run_analysis_flow():
    # Mock dependencies
    with patch("risk_scout.ShipmentDB") as MockDB, \
         patch("risk_scout.CodeAgent") as MockAgent, \
         patch("risk_scout.ApiModel") as MockModel:
             
        # Setup mocks
        mock_db_instance = MockDB.return_value
        mock_db_instance.get_active_shipments = AsyncMock(return_value=[
            {
                "id": "ship-123",
                "vessel_name": "Test Vessel",
                "current_location_wkt": "POINT(103.8 1.35)", # Singapore
                "origin_port": "Shanghai",
                "destination_port": "Rotterdam",
                "eta": "2025-12-25"
            }
        ])
        mock_db_instance.update_shipment_risk = AsyncMock()
        
        mock_agent_instance = MockAgent.return_value
        # Mock agent output to be valid JSON
        mock_agent_instance.run.return_value = """
        Thinking...
        Final Answer:
        {
            "risk_score": 0.8,
            "risk_factors": ["Typhoon Warning"],
            "recommended_action": "REROUTE"
        }
        """
        
        # Instantiate System Under Test
        scout = RiskScout()
        
        # Run single scan
        await scout.scan_shipment({
            "id": "ship-123", 
            "vessel_name": "Test Vessel",
            "current_location_wkt": "POINT(103.8 1.35)"
        })
        
        # Verify
        mock_db_instance.update_shipment_risk.assert_called_once()
        call_args = mock_db_instance.update_shipment_risk.call_args
        assert call_args[0][0] == "ship-123" # shipment_id
        assert call_args[0][1] == 0.8        # risk_score
        assert "Typhoon Warning" in call_args[0][2] # risk_factors
