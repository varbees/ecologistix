import os
import asyncpg
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ShipmentDB:
    def __init__(self):
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "ecologistix")
        
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    async def get_active_shipments(self) -> List[Dict[str, Any]]:
        """Fetch all shipments with status ON_TRACK or AT_RISK"""
        conn = await asyncpg.connect(self.dsn)
        try:
            # Fetch shipments that haven't been updated in the last hour? 
            # Or just all active ones for the continuous loop.
            # Providing basic fields needed for risk analysis.
            rows = await conn.fetch("""
                SELECT id, vessel_name, ST_AsText(current_location) as current_location_wkt, 
                       origin_port, destination_port, eta
                FROM active_shipments
                WHERE status IN ('ON_TRACK', 'AT_RISK')
            """)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def update_shipment_risk(self, shipment_id: str, risk_score: float, risk_factors: List[str]):
        """Update shipment risk assessment"""
        conn = await asyncpg.connect(self.dsn)
        try:
            new_status = 'AT_RISK' if risk_score > 0.7 else 'ON_TRACK'
            
            await conn.execute("""
                UPDATE active_shipments
                SET risk_score = $1,
                    risk_factors = $2,
                    status = $3,
                    last_updated = NOW()
                WHERE id = $4
            """, risk_score, risk_factors, new_status, shipment_id)
        finally:
            await conn.close()
            
    async def log_disruption(self, event_data: Dict[str, Any]):
        """Log a new disruption event"""
        conn = await asyncpg.connect(self.dsn)
        try:
            await conn.execute("""
                INSERT INTO disruption_events (
                    id, event_type, severity, location, description, 
                    affected_shipments, data_source, detected_at
                ) VALUES (
                    gen_random_uuid(), $1, $2, ST_GeomFromText($3, 4326), $4, 
                    $5, $6, NOW()
                )
            """, 
            event_data['event_type'],
            event_data['severity'],
            event_data.get('location_wkt', 'POINT(0 0)'), # Default if missing
            event_data['description'],
            event_data.get('affected_shipments', []),
            event_data['data_source']
            )
        finally:
            await conn.close()

    async def save_route_alternatives(self, shipment_id: str, alternatives_json: Any):
        """Save generated route alternatives to history"""
        conn = await asyncpg.connect(self.dsn)
        try:
            # For this Phase, we store the raw JSON in 'reason_for_change' or 'alternative_route' logic
            # The schema has 'alternative_route' as Geometry.
            # To keep it simple for Week 6 MVP, we'll store the full analysis in 'reason_for_change' text field 
            # or ideally expand schema. But 'reason_for_change' is TEXT.
            # Let's stringify the JSON into 'reason_for_change' for now as a log.
            
            # Convert to string if dict
            if not isinstance(alternatives_json, str):
                import json
                alternatives_json = json.dumps(alternatives_json)
                
            await conn.execute("""
                INSERT INTO route_history (
                    id, shipment_id, reason_for_change, approved_by, created_at
                ) VALUES (
                    gen_random_uuid(), $1, $2, 'ROUTE_PLANNER', NOW()
                )
            """, shipment_id, alternatives_json)
            
        finally:
            await conn.close()
