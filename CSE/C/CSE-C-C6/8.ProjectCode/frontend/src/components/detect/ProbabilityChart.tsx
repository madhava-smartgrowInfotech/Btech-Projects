import { BarChart3 } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartTooltip, gridProps } from "@/components/charts/Chart";
import { LABELS, type Label } from "@/lib/api";
import { pct, VERDICT } from "@/lib/verdict";

/** Class probabilities for one article (the Streamlit "Class probabilities" bar chart). */
export function ProbabilityChart({ probabilities }: { probabilities: Record<Label, number> }) {
  const data = LABELS.map((l) => ({ label: l, probability: probabilities[l] ?? 0 }));
  return (
    <ChartCard
      title="Class probabilities"
      description="How the model splits its belief across the three classes"
      icon={<BarChart3 />}
      legend={LABELS.map((l) => ({ label: l, color: VERDICT[l].color }))}
      table={{ columns: ["Class", "Probability"], rows: data.map((d) => [d.label, pct(d.probability)]) }}
    >
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="label" {...axisProps} />
            <YAxis domain={[0, 1]} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} {...axisProps} />
            <Tooltip
              cursor={{ fill: "var(--muted)" }}
              content={<ChartTooltip formatter={(v) => pct(Number(v))} />}
            />
            <Bar dataKey="probability" name="Probability" radius={[8, 8, 0, 0]} maxBarSize={72}>
              {data.map((d) => (
                <Cell key={d.label} fill={VERDICT[d.label].color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
