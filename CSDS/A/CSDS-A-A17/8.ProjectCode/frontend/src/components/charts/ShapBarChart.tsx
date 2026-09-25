import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Feature {
  feature: string;
  contribution: number;
}

function capitalize(s: string): string {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ShapBarChart({ items }: { items: Feature[] }) {
  const data = [...items]
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 6)
    .map((d) => ({ ...d, label: capitalize(d.feature.replaceAll("_", " ")) }))
    .reverse();

  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 38)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="label"
          width={130}
          tick={{ fontSize: 12, fill: "#44403c" }}
          axisLine={false}
          tickLine={false}
        />
        <ReferenceLine x={0} stroke="#d6d3cd" />
        <Tooltip
          formatter={(value) => [Number(value).toFixed(3), "Contribution"]}
          contentStyle={{ borderRadius: 12, border: "1px solid #e7e5df", fontSize: 12 }}
        />
        <Bar dataKey="contribution" radius={4} barSize={14}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.contribution >= 0 ? "#4d7c0f" : "#e11d48"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
