import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import asyncio
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import asyncpg
from pgvector.asyncpg import register_vector
from utils.logger import get_logger
from db import ShipmentDB

logger = get_logger("RAGManager")

class RAGManager:
    def __init__(self):
        # Initialize Embedding Model
        # all-MiniLM-L6-v2 is small and fast (384 dim)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = ShipmentDB()
        
    async def ingest_document(self, content: str, source: str):
        """Embed and save document to knowledge base"""
        embedding = self.model.encode(content).tolist()
        
        conn = await asyncpg.connect(self.db.dsn)
        try:
            await register_vector(conn)
            await conn.execute("""
                INSERT INTO knowledge_base (content, source, embedding)
                VALUES ($1, $2, $3)
            """, content, source, embedding)
            logger.info(f"Ingested document from {source}")
        except Exception as e:
            logger.error(f"Failed to ingest document: {e}")
        finally:
            await conn.close()
            
    async def query_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant documents"""
        query_embedding = self.model.encode(query).tolist()
        
        conn = await asyncpg.connect(self.db.dsn)
        try:
            await register_vector(conn)
            # Cosine similarity (<=> is L2 distance, <=> is cosine distance operator in pgvector? 
            # Actually <=> is cosine distance. 
            # Docs say: <-> Euclidean, <=> Cosine, <#> Inner Product
            # We want closest distance = most similar.
            rows = await conn.fetch("""
                SELECT content, source, (embedding <=> $1) as distance
                FROM knowledge_base
                ORDER BY distance ASC
                LIMIT $2
            """, query_embedding, limit)
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to query knowledge: {e}")
            return []
        finally:
            await conn.close()
