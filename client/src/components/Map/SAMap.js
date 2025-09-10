import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export default function SAMap() {
  const mapRef = useRef(null);
  useEffect(() => {
    const styleUrl = process.env.REACT_APP_TILE_STYLE_URL || "https://api.maptiler.com/maps/streets/style.json?key=" + (process.env.REACT_APP_MAPTILER_KEY || "");
    const map = new maplibregl.Map({
      container: mapRef.current,
      style: styleUrl,
      center: [24.0, -28.5],
      zoom: 4.2,
    });

    map.on("load", () => {
      fetch("/map/wards")
        .then((r) => r.json())
        .then((fc) => {
          map.addSource("wards", { type: "geojson", data: fc });
          map.addLayer({ id: "wards-fill", type: "fill", source: "wards", paint: { "fill-color": "#0A6EBD", "fill-opacity": 0.05 } });
          map.addLayer({ id: "wards-outline", type: "line", source: "wards", paint: { "line-color": "#0A6EBD", "line-width": 1 } });
        });

      fetch("/map/incidents?since_minutes=1440")
        .then((r) => r.json())
        .then((fc) => {
          map.addSource("incidents", { type: "geojson", data: fc, cluster: true, clusterRadius: 40 });
          map.addLayer({ id: "incidents-circle", type: "circle", source: "incidents", paint: { "circle-radius": 6, "circle-color": "#F4A024" } });
        });
    });

    return () => map.remove();
  }, []);

  return <div ref={mapRef} style={{ height: "100vh" }} />;
}

