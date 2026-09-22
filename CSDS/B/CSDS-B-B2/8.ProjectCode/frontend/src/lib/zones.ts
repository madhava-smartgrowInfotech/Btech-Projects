export type ZoneLabel = "Strong" | "Weak" | "Dead";

/** Reserved status colours - always shown together with the text label. */
export const ZONE_COLOR: Record<ZoneLabel, string> = { Strong: "#0ca30c", Weak: "#f0a30a", Dead: "#d03b3b" };
export const ZONE_TEXT: Record<ZoneLabel, string> = {
  Strong: "Reliable calls and data",
  Weak: "Slow, laggy or unstable",
  Dead: "No usable connection",
};

export const SOURCE_LABEL: Record<string, string> = {
  phone: "Phones",
  esp32: "Sensor nodes",
  simulator: "Simulated nodes",
  sample_dataset: "Sample data",
};

export const METHOD_LABEL: Record<string, string> = {
  model: "Zone classifier",
  "service-bands": "Measured service quality",
  "wifi-ranges": "Wi-Fi link ranges",
  ranges: "Documented ranges",
  "no-service": "No service",
  unclassified: "Not enough metrics",
};

export function isZone(v: unknown): v is ZoneLabel {
  return v === "Strong" || v === "Weak" || v === "Dead";
}
