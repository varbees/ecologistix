-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge Base for RAG
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    source VARCHAR(255),
    embedding vector(384), -- Dimension for all-MiniLM-L6-v2
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit Reports
CREATE TABLE IF NOT EXISTS audit_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES active_shipments(id),
    route_id TEXT, -- ID from Route Planner options
    total_emissions_kg DECIMAL(10,2),
    compliance_status VARCHAR(50), -- COMPLIANT, NON_COMPLIANT, WARNING
    audit_details JSONB, -- Full report from Agent
    audited_at TIMESTAMP DEFAULT NOW()
);
