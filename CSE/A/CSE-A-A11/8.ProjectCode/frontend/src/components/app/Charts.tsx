import { useId } from "react";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartTooltip } from "@/components/charts/Chart";

export interface Datum {
  name: string;
  value: number;
}

/** Horizontal bars, largest on top. Long labels are truncated (the full name is in the tooltip and the table view). */
export function HBarChart({
  data,
  color = "#7C5CFF",
  top = 8,
  valueLabel = "Count",
  format = (n: number) => String(n),
  labelWidth = 120,
}: {
  data: Datum[];
  color?: string;
  top?: number;
  valueLabel?: string;
  format?: (n: number) => string;
  labelWidth?: number;
}) {
  const id = useId().replace(/:/g, "");
  const rows = [...data].sort((a, b) => b.value - a.value).slice(0, top);
  const height = Math.max(150, rows.length * 34 + 24);
  return (
    <div style={{ height }} role="img" aria-label={`${valueLabel} by category`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={`hb-${id}`} x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stopColor={color} stopOpacity={0.55} />
              <stop offset="100%" stopColor={color} stopOpacity={1} />
            </linearGradient>
          </defs>
          <XAxis type="number" hide domain={[0, "dataMax"]} />
          <YAxis
            type="category"
            dataKey="name"
            width={labelWidth}
            {...axisProps}
            tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
            tickFormatter={(v: string) => (v.length > 20 ? `${v.slice(0, 19)}…` : v)}
          />
          <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip formatter={(v) => format(Number(v))} />} />
          <Bar dataKey="value" name={valueLabel} fill={`url(#hb-${id})`} radius={[0, 8, 8, 0]} barSize={16} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DonutChart({ data, centerLabel }: { data: { name: string; value: number; color: string }[]; centerLabel?: string }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <div className="relative h-52" role="img" aria-label={`${centerLabel ?? "Total"}: ${total}`}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius="62%" outerRadius="88%" paddingAngle={2} stroke="none" isAnimationActive={false}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="font-display text-3xl font-semibold tabular-nums">{total}</div>
          {centerLabel && <div className="text-xs text-muted-foreground">{centerLabel}</div>}
        </div>
      </div>
    </div>
  );
}
