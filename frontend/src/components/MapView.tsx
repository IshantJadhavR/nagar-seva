import { useEffect, useRef } from "react";
import L from "leaflet";

export interface Marker { lat: number; lng: number; label?: string; radius?: number }
const MAHARASHTRA: [number, number] = [19.75, 75.71];

/** Plain Leaflet + OpenStreetMap tiles. Circle markers avoid bundler problems with Leaflet's default icon images. */
export default function MapView({
  markers = [], height = 280, onPick, picked, zoom,
}: {
  markers?: Marker[]; height?: number; onPick?: (lat: number, lng: number) => void; picked?: { lat: number; lng: number } | null; zoom?: number;
}) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);
  const pickCb = useRef(onPick);
  pickCb.current = onPick;

  useEffect(() => {
    if (!el.current || map.current) return;
    const m = L.map(el.current).setView(MAHARASHTRA, zoom ?? 7);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap contributors",
    }).addTo(m);
    layer.current = L.layerGroup().addTo(m);
    m.on("click", (e: L.LeafletMouseEvent) => pickCb.current?.(e.latlng.lat, e.latlng.lng));
    map.current = m;
    setTimeout(() => m.invalidateSize(), 0);
    return () => { m.remove(); map.current = null; };
  }, []);

  useEffect(() => {
    const m = map.current, g = layer.current;
    if (!m || !g) return;
    g.clearLayers();
    const pts: L.LatLngExpression[] = [];
    markers.forEach((k) => {
      L.circleMarker([k.lat, k.lng], { radius: k.radius ?? 8, color: "#146461", fillColor: "#1f9c92", fillOpacity: 0.55, weight: 2 })
        .bindTooltip(k.label ?? "").addTo(g);
      pts.push([k.lat, k.lng]);
    });
    if (picked) {
      L.circleMarker([picked.lat, picked.lng], { radius: 10, color: "#b75009", fillColor: "#f98b0b", fillOpacity: 0.9, weight: 3 }).addTo(g);
      m.setView([picked.lat, picked.lng], Math.max(m.getZoom(), 15));
    } else if (pts.length) {
      m.fitBounds(L.latLngBounds(pts), { padding: [30, 30], maxZoom: 15 });
    }
  }, [markers, picked]);

  return <div ref={el} style={{ height }} className="z-0 w-full overflow-hidden rounded-xl border border-line" />;
}
