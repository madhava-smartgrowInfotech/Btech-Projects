import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartCard, ChartTooltip, axisProps } from "@/components/charts/ChartCard";

/** Single-measure horizontal bar chart (one series: the title names it, no legend box). */
export function HBar({
  title,
  subtitle,
  data,
  format = (v) => v.toFixed(3),
  highlight,
  color = "var(--series-1)",
  valueLabel,
  labelWidth = 150,
}: {
  title: string;
  subtitle?: string;
  data: { label: string; value: number }[];
  format?: (v: number) => string;
  highlight?: string;
  color?: string;
  valueLabel: string;
  labelWidth?: number;
}) {
  const height = Math.max(140, data.length * 34 + 30);
  return (
    <ChartCard title={title} subtitle={subtitle} table={{ columns: ["", valueLabel], rows: data.map((d) => [d.label, format(d.value)]) }}>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 56, left: 4, bottom: 4 }} barCategoryGap={6}>
            <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
            <XAxis type="number" {...axisProps} tickFormatter={(v: number) => format(v)} />
            <YAxis type="category" dataKey="label" {...axisProps} width={labelWidth} tick={{ fill: "var(--chart-ink)", fontSize: 11 }} />
            <Tooltip content={<ChartTooltip format={format} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
            <Bar dataKey="value" name={valueLabel} radius={[0, 4, 4, 0]} maxBarSize={22}>
              {data.map((d) => (
                <Cell key={d.label} fill={color} fillOpacity={highlight && d.label !== highlight ? 0.45 : 1} />
              ))}
              <LabelList dataKey="value" position="right" formatter={(v: unknown) => format(Number(v))} style={{ fill: "var(--chart-ink)", fontSize: 11 }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
