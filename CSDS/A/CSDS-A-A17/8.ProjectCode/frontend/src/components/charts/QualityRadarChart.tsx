import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";

const LABELS: Record<string, string> = {
  color_uniformity: "Color",
  texture_homogeneity: "Texture",
  size_score: "Size",
  edge_density: "Surface",
  blemish_ratio: "Blemish (inv)",
  mean_saturation: "Vibrancy",
};

export function QualityRadarChart({ features }: { features: Record<string, number> }) {
  const data = Object.entries(LABELS).map(([key, label]) => {
    const raw = features[key] ?? 0;
    const value = key === "blemish_ratio" || key === "edge_density" ? 1 - raw : raw;
    return { label, value: Math.round(value * 100) };
  });

  return (
    <ResponsiveContainer width="100%" height={240}>
      <RadarChart data={data} outerRadius="75%">
        <PolarGrid stroke="#e7e5df" />
        <PolarAngleAxis dataKey="label" tick={{ fontSize: 11, fill: "#57534e" }} />
        <Radar dataKey="value" stroke="#166534" fill="#4d7c0f" fillOpacity={0.35} strokeWidth={2} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
