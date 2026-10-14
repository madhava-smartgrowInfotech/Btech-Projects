import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartTooltip, gridProps, STATUS } from "@/components/charts/Chart";
import type { HeartFactor } from "@/lib/types";

/**
 * SHAP contributions as a diverging bar chart. Red raises the risk, green lowers it.
 * Loaded with React.lazy from the result page so recharts only ships where it is used.
 */
export default function ShapChart({ factors }: { factors: HeartFactor[] }) {
  const data = factors.map((f) => ({ name: f.label, impact: f.impact }));
  return (
    <div className="h-72 w-full" role="img" aria-label="Top risk factors and their SHAP contribution to the predicted risk">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
          <CartesianGrid {...gridProps} horizontal={false} />
          <XAxis type="number" {...axisProps} tickFormatter={(v: number) => v.toFixed(2)} />
          <YAxis type="category" dataKey="name" width={150} {...axisProps} tick={{ fontSize: 11, fill: "var(--chart-axis)" }} />
          <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip formatter={(v) => Number(v).toFixed(3)} />} />
          <Bar dataKey="impact" radius={4}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.impact > 0 ? STATUS.critical : STATUS.good} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
