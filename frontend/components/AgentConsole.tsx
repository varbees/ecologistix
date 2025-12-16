'use client';
import { Scroll, Terminal } from 'lucide-react';

export default function AgentConsole({ shipments }: { shipments: any[] }) {
    // Filter shipments that have recent activity
    const activeAudits = shipments.filter(s => s.latest_plan || s.compliance_status);
    
    return (
        <div className="bg-black text-green-400 font-mono p-4 rounded-lg h-full overflow-auto shadow-lg border border-gray-800">
            <div className="flex items-center gap-2 mb-4 border-b border-gray-700 pb-2">
                <Terminal className="w-4 h-4" />
                <h2 className="font-bold">Agent Neural Link</h2>
            </div>
            
            <div className="space-y-4 text-sm">
                {activeAudits.length === 0 && (
                    <p className="opacity-50">System Nominal. Listening for events...</p>
                )}
                
                {activeAudits.map((s) => (
                    <div key={s.id} className="border-l-2 border-green-700 pl-3">
                        <div className="opacity-70 text-xs mb-1">{s.vessel_name} ({s.id.substring(0,8)})</div>
                        
                        {s.risk_score > 0.7 && (
                            <div className="text-red-400">
                                [RISK_SCOUT] ALERT: High Risk Detected (Score: {s.risk_score})
                                <br/>Factors: {JSON.stringify(s.risk_factors)}
                            </div>
                        )}
                        
                        {s.latest_plan && (
                            <div className="text-blue-400 mt-1">
                                [ROUTE_PLANNER] Alternative Route Generated.
                            </div>
                        )}
                        
                        {s.compliance_status && (
                            <div className="text-yellow-400 mt-1">
                                [CARBON_AUDITOR] {s.compliance_status} ({s.total_emissions_kg} kg CO2)
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
