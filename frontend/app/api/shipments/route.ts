import { NextResponse } from 'next/server';
import pool from '@/lib/db';

export async function GET() {
  try {
    const client = await pool.connect();
    try {
      // Fetch shipments linked with latest route plan and audit report
      const query = `
        SELECT 
           s.id, s.vessel_name, ST_AsText(s.current_location) as location_wkt, s.origin_port, s.destination_port, 
           s.status, s.risk_score, s.risk_factors,
           rh.reason_for_change as latest_plan, 
           ar.compliance_status, ar.total_emissions_kg, ar.audit_details
        FROM active_shipments s
        LEFT JOIN LATERAL (
            SELECT reason_for_change FROM route_history 
            WHERE shipment_id = s.id 
            ORDER BY created_at DESC LIMIT 1
        ) rh ON true
        LEFT JOIN LATERAL (
            SELECT compliance_status, total_emissions_kg, audit_details 
            FROM audit_reports 
            WHERE shipment_id = s.id 
            ORDER BY audited_at DESC LIMIT 1
        ) ar ON true
      `;
      
      const result = await client.query(query);
      return NextResponse.json(result.rows);
    } finally {
      client.release();
    }
  } catch (err) {
    console.error("DB Error:", err);
    return NextResponse.json({ error: 'Failed to fetch shipments' }, { status: 500 });
  }
}
