-- ENUMS
DO $$ BEGIN
    CREATE TYPE vessel_type AS ENUM ('Container', 'Tanker', 'Bulk', 'General');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE shipment_status AS ENUM ('ON_TRACK', 'AT_RISK', 'REROUTING', 'DIVERTED', 'ARRIVED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE event_type AS ENUM ('WEATHER_STORM', 'PORT_CLOSURE', 'GEOPOLITICAL_ALERT', 'MECHANICAL_FAILURE', 'PIRACY_ALERT', 'LABOR_STRIKE', 'REGULATORY_CHANGE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- TABLES

CREATE TABLE IF NOT EXISTS active_shipments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vessel_name VARCHAR(255),
  vessel_type vessel_type,
  mmsi INTEGER UNIQUE,
  current_location GEOMETRY(POINT, 4326),
  current_speed DECIMAL(5,2),
  current_heading SMALLINT,
  cargo_type VARCHAR(255),
  cargo_weight_metric_tons DECIMAL(10,2),
  planned_route GEOMETRY(LINESTRING, 4326),
  actual_route GEOMETRY(LINESTRING, 4326),
  status shipment_status DEFAULT 'ON_TRACK',
  origin_port VARCHAR(100),
  destination_port VARCHAR(100),
  eta TIMESTAMP,
  risk_score DECIMAL(3,2) DEFAULT 0.0,
  risk_factors TEXT[],
  owner_company VARCHAR(255),
  last_updated TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS disruption_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type event_type,
  severity severity_level,
  location GEOMETRY(POINT, 4326),
  description TEXT,
  affected_shipments UUID[],
  data_source VARCHAR(100),
  raw_payload JSONB,
  detected_at TIMESTAMP,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_traces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_type VARCHAR(100),
  shipment_id UUID REFERENCES active_shipments(id),
  prompt TEXT,
  response TEXT,
  tools_called JSONB,
  reasoning_trace TEXT,
  execution_time_ms INTEGER,
  tokens_used INTEGER,
  success BOOLEAN,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS route_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id UUID REFERENCES active_shipments(id),
  original_route GEOMETRY(LINESTRING, 4326),
  alternative_route GEOMETRY(LINESTRING, 4326),
  reason_for_change TEXT,
  distance_original_km DECIMAL(10,2),
  distance_alternative_km DECIMAL(10,2),
  cost_original_usd DECIMAL(10,2),
  cost_alternative_usd DECIMAL(10,2),
  carbon_original_kg_co2 DECIMAL(10,2),
  carbon_alternative_kg_co2 DECIMAL(10,2),
  approved_at TIMESTAMP,
  approved_by VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);
