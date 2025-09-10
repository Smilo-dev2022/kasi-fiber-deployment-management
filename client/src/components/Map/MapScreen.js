import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { Protocol as PMTilesProtocol } from 'pmtiles';
import 'maplibre-gl/dist/maplibre-gl.css';

const NATIONAL_BBOX = [16.45, -34.84, 32.89, -22.13];

export default function MapScreen() {
  const mapRef = useRef(null);
  const containerRef = useRef(null);
  const [showWards, setShowWards] = useState(true);
  const [showPoles, setShowPoles] = useState(true);
  const [showClosures, setShowClosures] = useState(true);
  const [showCables, setShowCables] = useState(true);

  useEffect(() => {
    if (!containerRef.current) return;
    // Register PMTiles protocol for offline packs
    try {
      const protocol = new PMTilesProtocol();
      maplibregl.addProtocol('pmtiles', protocol.tile);
    } catch (e) {
      // no-op if already registered
    }
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: '/map/tiles',
      center: [24.0, -29.0],
      zoom: 4,
      maxZoom: 16,
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl());
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }));

    map.on('load', async () => {
      // If offline and a local PMTiles file exists, switch base source
      if (!navigator.onLine) {
        try {
          const resp = await fetch('/tiles/sa.pmtiles', { method: 'HEAD' });
          if (resp.ok) {
            const style = map.getStyle();
            style.sources.osm = {
              type: 'vector',
              url: 'pmtiles:///tiles/sa.pmtiles',
              minzoom: 0,
              maxzoom: 14,
            };
            map.setStyle(style);
          }
        } catch {}
      }
      // Wards
      map.addSource('wards', {
        type: 'geojson',
        data: '/map/wards',
      });
      map.addLayer({
        id: 'wards-fill',
        type: 'fill',
        source: 'wards',
        paint: {
          'fill-color': '#f2f5ff',
          'fill-opacity': 0.4,
        },
      });
      map.addLayer({
        id: 'wards-outline',
        type: 'line',
        source: 'wards',
        paint: {
          'line-color': '#8aa0c7',
          'line-width': 1,
        },
      });
    });

    return () => map.remove();
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const vis = showWards ? 'visible' : 'none';
    ['wards-fill', 'wards-outline'].forEach((id) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', vis);
    });
  }, [showWards]);

  return (
    <div style={{ display: 'flex', height: '100%', width: '100%' }}>
      <div ref={containerRef} style={{ flex: 1 }} />
      <div style={{ width: 280, padding: 12, background: 'rgba(255,255,255,0.9)', borderLeft: '1px solid #ddd' }}>
        <h3 style={{ marginTop: 0 }}>Layers</h3>
        <label><input type="checkbox" checked={showWards} onChange={e => setShowWards(e.target.checked)} /> Wards</label><br/>
        <label><input type="checkbox" checked={showPoles} onChange={e => setShowPoles(e.target.checked)} /> Poles</label><br/>
        <label><input type="checkbox" checked={showClosures} onChange={e => setShowClosures(e.target.checked)} /> Closures</label><br/>
        <label><input type="checkbox" checked={showCables} onChange={e => setShowCables(e.target.checked)} /> Cables</label><br/>
      </div>
    </div>
  );
}

