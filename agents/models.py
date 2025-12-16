from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Shipment(BaseModel):
    id: Optional[str] = None # UUID
    vessel_name: str
    vessel_type: str
    mmsi: int
    current_location: Any # Geometry POINT
    current_speed: float
    current_heading: int
    cargo_type: str
    cargo_weight_metric_tons: float
    planned_route: Any # Geometry LINESTRING
    actual_route: Optional[Any] = None # Geometry LINESTRING
    status: str # ENUM
    origin_port: str
    destination_port: str
    eta: datetime
    risk_score: float = 0.0
    risk_factors: List[str] = []
    owner_company: str
    last_updated: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)

class DisruptionEvent(BaseModel):
    id: Optional[str] = None
    event_type: str
    severity: str
    location: Any # Geometry POINT
    description: str
    affected_shipments: List[str] = []
    data_source: str
    raw_payload: Optional[Dict] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Route(BaseModel):
    id: Optional[str] = None
    shipment_id: str
    original_route: Any
    alternative_route: Any
    reason_for_change: str
    distance_original_km: float
    distance_alternative_km: float
    cost_original_usd: float
    cost_alternative_usd: float
    carbon_original_kg_co2: float
    carbon_alternative_kg_co2: float
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
