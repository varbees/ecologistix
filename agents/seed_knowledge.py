import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import asyncio
from rag_manager import RAGManager

async def seed():
    rag = RAGManager()
    
    docs = [
        {
            "content": "EU ETS 2025: Shipping companies must surrender allowances for 40% of verified emissions reported for 2024. By 2027, this increases to 100%.",
            "source": "EU Commission Directive 2023/959"
        },
        {
            "content": "Scope 3 Emissions: Logistics providers must report indirect emissions from transportation and distribution. The carbon intensity cap for container ships is 8g CO2/ton-km.",
            "source": "CSRD Reporting Standard E1"
        },
        {
            "content": "Carbon Border Adjustment Mechanism (CBAM): Importers of cement, iron, steel, aluminum, fertilizers, electricity and hydrogen must buy certificates corresponding to the carbon price that would have been paid had the goods been produced under the EU's carbon pricing rules.",
            "source": "Regulation (EU) 2023/956"
        }
    ]
    
    print("Seeding Knowledge Base...")
    for doc in docs:
        await rag.ingest_document(doc["content"], doc["source"])
    print("Seeding Complete.")

if __name__ == "__main__":
    asyncio.run(seed())
