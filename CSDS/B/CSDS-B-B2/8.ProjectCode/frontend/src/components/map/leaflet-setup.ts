// leaflet.heat is a classic plugin that extends the global `L`; expose Leaflet before it loads.
import L from "leaflet";
import "leaflet/dist/leaflet.css";

(window as unknown as { L: typeof L }).L = L;

export default L;
