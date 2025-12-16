'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import useSWR from 'swr';
import { Ship, AlertTriangle, Leaf, Activity } from 'lucide-react';
import AgentConsole from '@/components/AgentConsole';

// Map must be client-side only
const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

const fetcher = (url: string) => fetch(url).then(r => r.json());

export default function Dashboard() {
  const { data: shipments, error } = useSWR('/api/shipments', fetcher, { refreshInterval: 2000 });

  const loading = !shipments && !error;
  const activeCount = shipments?.length || 0;
  const riskCount = shipments?.filter((s:any) => s.status === 'AT_RISK' || s.risk_score > 0.5).length || 0;
  const nonCompliantCount = shipments?.filter((s:any) => s.compliance_status === 'NON_COMPLIANT').length || 0;

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <header className="h-16 border-b border-gray-800 flex items-center px-6 gap-4 bg-gray-950">
        <div className="font-bold text-xl tracking-tight text-blue-500">EcoLogistix AI</div>
        <div className="flex-1"></div>
        <div className="flex gap-4 text-sm font-mono">
           <div className="flex items-center gap-2">
             <Ship className="w-4 h-4 text-blue-400" /> 
             <span>{activeCount} Active</span>
           </div>
           <div className="flex items-center gap-2">
             <AlertTriangle className="w-4 h-4 text-red-400" /> 
             <span>{riskCount} At Risk</span>
           </div>
           <div className="flex items-center gap-2">
             <Leaf className="w-4 h-4 text-green-400" /> 
             <span>{nonCompliantCount} Flags</span>
           </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Map Area */}
        <div className="flex-1 relative bg-gray-800">
           {loading ? (
             <div className="flex items-center justify-center h-full">Loading System...</div>
           ) : (
             <MapView shipments={shipments || []} />
           )}
        </div>

        {/* Sidebar Console */}
        <div className="w-96 border-l border-gray-800 bg-gray-950 flex flex-col">
            <div className="p-4 border-b border-gray-800">
               <h2 className="font-semibold flex items-center gap-2">
                 <Activity className="w-4 h-4" /> Agent Operations
               </h2>
            </div>
            <div className="flex-1 p-2 overflow-hidden">
                <AgentConsole shipments={shipments || []} />
            </div>
        </div>
      </main>
    </div>
  );
}
