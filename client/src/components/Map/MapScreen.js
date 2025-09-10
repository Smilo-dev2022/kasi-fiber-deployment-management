import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const SA_BBOX = [16.45, -34.84, 32.89, -22.13];

export default function MapScreen() {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);

  useEffect(() => {
    if (map) return;
    const m = new maplibregl.Map({
      container: mapRef.current,
      style: '/map/tiles?token=' + (window.localStorage.getItem('TILES_TOKEN') || ''),
      center: [24.25, -30.0],
      zoom: 5,
      maxZoom: 16,
    });
    m.fitBounds([[SA_BBOX[0], SA_BBOX[1]], [SA_BBOX[2], SA_BBOX[3]]], { padding: 20, duration: 0 });

    m.on('load', async () => {
      // Wards fill/border styling
      const wards = await fetch('/map/wards').then(r => r.json());
      m.addSource('wards', { type: 'geojson', data: wards });
      m.addLayer({ id: 'wards-fill', type: 'fill', source: 'wards', paint: { 'fill-color': '#CFE8FF', 'fill-opacity': 0.25 } });
      m.addLayer({ id: 'wards-line', type: 'line', source: 'wards', paint: { 'line-color': '#3A7ABF', 'line-width': 1 } });
    });

    setMap(m);
    return () => m && m.remove();
  }, [map]);

  return (
    <div style={{ position: 'relative', height: '100%', width: '100%' }}>
      <div ref={mapRef} style={{ position: 'absolute', inset: 0 }} />
    </div>
  );
}

