-- Enable PostGIS for geospatial queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pgvector for RAG / embeddings
CREATE EXTENSION IF NOT EXISTS pgvector;
