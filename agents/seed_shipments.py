import os
import sys
import random
import asyncio
from datetime import datetime, timedelta

# Setup path to include 'agents' folder if running from there
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Also add parent dir for 'agents' package resolution if needed
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import asyncpg
try:
    from tools.shipping_tool import ShippingTool
except ImportError:
    from agents.tools.shipping_tool import ShippingTool

from dotenv import load_dotenv

load_dotenv()

# DB Config
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ecologistix")
DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

tool = ShippingTool()

VESSEL_PREFIXES = ["MSC", "Maersk", "CMA CGM", "Hapag-Lloyd", "Evergreen", "ONE", "COSCO", "Hyundai"]
VESSEL_NAMES = ["Pearl", "Diamond", "Titan", "Spirit", "Hope", "Glory", "Star", "Ocean", "Blue", "Green"]

def generate_shipment(i):
    origin_name, origin_coords = random.choice(list(tool.MAJOR_PORTS.items()))
    dest_name, dest_coords = random.choice(list(tool.MAJOR_PORTS.items()))
    
    while origin_name == dest_name:
        dest_name, dest_coords = random.choice(list(tool.MAJOR_PORTS.items()))
        
    vessel = f"{random.choice(VESSEL_PREFIXES)} {random.choice(VESSEL_NAMES)} {random.randint(100, 999)}"
    
    # Random progress 0-100%
    progress = random.random()
    
    # Simple linear interpolation for current location (roughly)
    # Lat
    cur_lat = origin_coords[0] + (dest_coords[0] - origin_coords[0]) * progress
    # Lon (handle dateline roughly? na, flat earth for MVP)
    cur_lon = origin_coords[1] + (dest_coords[1] - origin_coords[1]) * progress
    
    # Add some noise to be off the straight line (realistic great circle arc is too complex for this script, just noise)
    cur_lat += random.uniform(-1, 1)
    cur_lon += random.uniform(-1, 1)
    
    status = "ON_TRACK"
    # 20% chance of Risk
    if random.random() < 0.2:
        status = "AT_RISK"
        
    return {
        "vessel_name": vessel,
        "origin": origin_name,
        "destination": dest_name,
        "lat": cur_lat,
        "lon": cur_lon,
        "status": status,
        "risk_score": 0.0 if status == "ON_TRACK" else random.uniform(0.7, 0.95)
    }

async def seed():
    print("Seeding ~40 active shipments...")
    conn = await asyncpg.connect(DSN)
    
    try:
        # Clear existing? maybe not, just append or upsert
        # await conn.execute("DELETE FROM active_shipments")
        
        for i in range(40):
            s = generate_shipment(i)
            print(f"Generating {s['vessel_name']} from {s['origin']} to {s['destination']}")
            
            wkt = f"POINT({s['lon']} {s['lat']})"
            
            await conn.execute("""
                INSERT INTO active_shipments (
                    id, vessel_name, origin_port, destination_port, 
                    current_location, status, risk_score, eta, last_updated
                ) VALUES (
                    gen_random_uuid(), $1, $2, $3, 
                    ST_GeomFromText($4, 4326), $5, $6, NOW() + INTERVAL '5 days', NOW()
                )
            """, s['vessel_name'], s['origin'], s['destination'], wkt, s['status'], s['risk_score'])
            
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(seed())
