import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "./leaflet-setup";
import "leaflet.heat";

// Problem density: a single warm ramp from light amber (a few weak readings) to red (dead readings).
const GRADIENT = { 0.25: "#fde68a", 0.5: "#fab219", 0.75: "#ec835a", 1: "#d03b3b" };

export function HeatLayer({ points }: { points: [number, number, number][] }) {
  const map = useMap();
  const layer = useRef<L.HeatLayer | null>(null);

  useEffect(() => {
    layer.current = L.heatLayer([], { radius: 22, blur: 18, maxZoom: 17, minOpacity: 0.25, gradient: GRADIENT }).addTo(map);
    return () => {
      layer.current?.remove();
      layer.current = null;
    };
  }, [map]);

  useEffect(() => {
    layer.current?.setLatLngs(points);
  }, [points]);

  return null;
}
