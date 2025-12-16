'use client';

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';

// Fix default icons
const iconUrl = 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png';
const iconRetinaUrl = 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png';
const shadowUrl = 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png';

const defaultIcon = L.icon({
    iconUrl: iconUrl,
    iconRetinaUrl: iconRetinaUrl,
    shadowUrl: shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = defaultIcon;

const riskIcon = L.icon({
    ...defaultIcon.options,
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
});

function parseWKT(wkt: string): [number, number] | null {
    if (!wkt || wkt.indexOf('POINT') === -1) return null;
    const clean = wkt.replace('POINT(', '').replace(')', '');
    const parts = clean.split(' ');
    if (parts.length >= 2) {
        // WKT is Long Lat, Leaflet is Lat Long
        return [parseFloat(parts[1]), parseFloat(parts[0])];
    }
    return null;
}

export default function MapView({ shipments }: { shipments: any[] }) {
    return (
        <MapContainer center={[20, 0]} zoom={2} style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}>
            <TileLayer
                attribution='&copy; OpenStreetMap'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {shipments.map((s) => {
                const pos = parseWKT(s.location_wkt);
                if (!pos) return null;
                
                const isRisk = s.status === 'AT_RISK' || s.risk_score > 0.7;
                
                return (
                    <Marker key={s.id} position={pos} icon={isRisk ? riskIcon : defaultIcon}>
                        <Popup>
                            <div className="text-sm">
                                <h3 className="font-bold">{s.vessel_name}</h3>
                                <p>Status: <span className={isRisk ? "text-red-600" : "text-green-600"}>{s.status}</span></p>
                                <p>Risk Score: {s.risk_score}</p>
                                {s.latest_plan && <p className="mt-1 text-xs text-blue-600">Re-route Planned</p>}
                                {s.compliance_status && <p className="text-xs text-gray-600">Audit: {s.compliance_status}</p>}
                            </div>
                        </Popup>
                    </Marker>
                );
            })}
        </MapContainer>
    );
}
