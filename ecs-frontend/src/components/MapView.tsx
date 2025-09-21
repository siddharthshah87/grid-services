import { useEffect, useMemo, useRef, useState } from 'react';
import { useVens } from '@/hooks/useApi';

const MAPS_API_KEY = (import.meta as any)?.env?.VITE_GOOGLE_MAPS_API_KEY || 'AIzaSyDXc2YBTobbyySrM-CgMpx5NvkMC3ZAPn0';

function useGoogleMaps() {
  const [loaded, setLoaded] = useState<boolean>(false);
  useEffect(() => {
    if ((window as any).google && (window as any).google.maps) {
      setLoaded(true);
      return;
    }
    const existing = document.querySelector('script[data-google-maps]') as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener('load', () => setLoaded(true));
      return;
    }
    const s = document.createElement('script');
    s.src = `https://maps.googleapis.com/maps/api/js?key=${MAPS_API_KEY}`;
    s.async = true;
    s.defer = true;
    s.setAttribute('data-google-maps', 'true');
    s.onload = () => setLoaded(true);
    document.body.appendChild(s);
  }, []);
  return loaded;
}

const mapStyle: google.maps.MapTypeStyle[] = [
  { elementType: 'geometry', stylers: [{ color: '#0b0e14' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0b0e14' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#9aa4b2' }] },
  { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: '#cbd5e1' }] },
  { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#94a3b8' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#0f1320' }] },
  { featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{ color: '#6ee7b7' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#1f2937' }] },
  { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#111827' }] },
  { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#9ca3af' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#334155' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0a0f1f' }] },
  { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#64748b' }] }
];

export const MapView = () => {
  const loaded = useGoogleMaps();
  const { data: vens } = useVens();
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<google.maps.Map | null>(null);
  const markers = useRef<google.maps.Marker[]>([]);

  const center = useMemo(() => {
    if (vens && vens.length > 0) {
      const first = vens[0];
      return { lat: first.location.lat, lng: first.location.lon };
    }
    return { lat: 37.42, lng: -122.08 };
  }, [vens]);

  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    if (!mapInstance.current) {
      mapInstance.current = new google.maps.Map(mapRef.current, {
        center,
        zoom: 6,
        styles: mapStyle,
        disableDefaultUI: true,
      });
    } else {
      mapInstance.current.setCenter(center);
    }
  }, [loaded, center]);

  useEffect(() => {
    if (!loaded || !mapInstance.current) return;
    // clear existing markers
    markers.current.forEach((m) => m.setMap(null));
    markers.current = [];
    (vens || []).forEach((v) => {
      const color = v.status === 'online' ? '#22c55e' : v.status === 'offline' ? '#ef4444' : '#f59e0b';
      const m = new google.maps.Marker({
        map: mapInstance.current!,
        position: { lat: v.location.lat, lng: v.location.lon },
        title: `${v.name} / ${v.id}`,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 6,
          fillColor: color,
          fillOpacity: 1,
          strokeColor: '#0b0e14',
          strokeOpacity: 0.9,
          strokeWeight: 2,
        },
      });
      const info = new google.maps.InfoWindow({
        content: `
          <div style="font-family: Inter, sans-serif; font-size: 12px; color: #e2e8f0;">
            <div style="font-weight: 600; margin-bottom: 4px;">${v.name}</div>
            <div style="opacity: 0.8">ID: ${v.id}</div>
            <div style="opacity: 0.8">Status: ${v.status}</div>
            <div style="opacity: 0.8">Power: ${(v.metrics.currentPowerKw).toFixed(1)} kW</div>
            <div style="opacity: 0.8">Controllable: ${(v.metrics.shedAvailabilityKw).toFixed(1)} kW</div>
          </div>
        `,
      });
      m.addListener('click', () => info.open({ map: mapInstance.current!, anchor: m }));
      markers.current.push(m);
    });
  }, [loaded, vens]);

  return (
    <div className="p-4">
      <div className="rounded-lg border h-[450px] overflow-hidden">
        <div ref={mapRef} className="w-full h-full" />
      </div>
      <div className="mt-3 bg-card/90 backdrop-blur-sm border rounded-lg p-3">
        <h4 className="text-sm font-semibold mb-2">VEN Status</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-online inline-block"></span> Online</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-offline inline-block"></span> Offline</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-warning inline-block"></span> Maintenance</div>
        </div>
      </div>
    </div>
  );
};
