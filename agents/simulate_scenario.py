import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import json
import time
import asyncio
import redis
from db import ShipmentDB

# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379

async def reset_db(db):
    print("[SIM] Resetting DB constraints and seeding test shipment...")
    import asyncpg
    conn = await asyncpg.connect(db.dsn)
    try:
        # Create test shipment
        await conn.execute("""
            INSERT INTO active_shipments (id, vessel_name, origin_port, destination_port, status)
            VALUES ('e2e-test-shipment', 'Simulated Vessel', 'Shanghai', 'Rotterdam', 'IN_TRANSIT')
            ON CONFLICT (id) DO UPDATE SET status = 'IN_TRANSIT';
        """)
        # Clear previous history
        await conn.execute("DELETE FROM route_history WHERE shipment_id = 'e2e-test-shipment'")
        await conn.execute("DELETE FROM audit_reports WHERE shipment_id = 'e2e-test-shipment'")
    finally:
        await conn.close()

def inject_high_risk_event(r):
    event = {
        "event_type": "HIGH_RISK_DETECTED",
        "shipment_id": "e2e-test-shipment",
        "risk_score": 0.95,
        "risk_factors": ["Simulated Typhoon", "Port Closure"],
        "detected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    print(f"[SIM] Injecting High Risk Event: {json.dumps(event)}")
    r.lpush("event:queue:high_priority", json.dumps(event))

async def monitor_progress(db):
    print("[SIM] Monitoring progress...")
    
    import asyncpg
    # Wait for Route Plan
    for i in range(30):
        conn = await asyncpg.connect(db.dsn)
        routes = await conn.fetchval("SELECT count(*) FROM route_history WHERE shipment_id = 'e2e-test-shipment'")
        await conn.close()
        if routes > 0:
            print("[SIM] ✅ Route Planner produced alternatives!")
            break
        await asyncio.sleep(2)
        if i % 5 == 0: print("[SIM] ... waiting for Route Planner ...")
    else:
        print("[SIM] ❌ Route Planner timed out.")
        return

    # Wait for Audit
    for i in range(30):
        conn = await asyncpg.connect(db.dsn)
        audits = await conn.fetchval("SELECT count(*) FROM audit_reports WHERE shipment_id = 'e2e-test-shipment'")
        await conn.close()
        if audits > 0:
            print("[SIM] ✅ Carbon Auditor produced report!")
            break
        await asyncio.sleep(2)
        if i % 5 == 0: print("[SIM] ... waiting for Carbon Auditor ...")
    else:
        print("[SIM] ❌ Carbon Auditor timed out.")
        return
        
    print("[SIM] 🎉 FULL E2E FLOW COMPLETE!")

async def run_simulation():
    db = ShipmentDB()
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    
    await reset_db(db)
    inject_high_risk_event(r)
    await monitor_progress(db)

if __name__ == "__main__":
    asyncio.run(run_simulation())
