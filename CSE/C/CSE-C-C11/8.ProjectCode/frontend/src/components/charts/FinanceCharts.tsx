import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartGradients, ChartTooltip, GlowDot, gridProps, SERIES } from "@/components/charts/Chart";
import { monthLabel, useMoney } from "@/lib/format";
import { useReducedMotionFlag } from "@/lib/motion";

/** Extended palette for pies with many slices (violet, cyan, magenta lead, as everywhere else). */
export const PALETTE = ["#7C5CFF", "#22D3EE", "#F472B6", "#A3E635", "#FBBF24", "#FB923C", "#34D399", "#60A5FA", "#C084FC", "#F87171", "#2DD4BF", "#94A3B8"];

/** Crowded category axes tilt their labels instead of overprinting each other. */
function labelProps(count: number) {
  return count > 5 ? ({ angle: -35, textAnchor: "end" as const, height: 62, tick: { fontSize: 11 } }) : ({ tick: { fontSize: 11 } });
}

export const colorFor = (i: number) => PALETTE[i % PALETTE.length];

export function Donut({ data, height = 260 }: { data: { name: string; value: number }[]; height?: number }) {
  const money = useMoney();
  const reduce = useReducedMotionFlag();
  const total = data.reduce((a, d) => a + d.value, 0);
  return (
    <div className="grid items-center gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<ChartTooltip formatter={(v) => `${money(Number(v))} (${total ? Math.round((Number(v) / total) * 100) : 0}%)`} />} />
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius="58%"
              outerRadius="92%"
              paddingAngle={2}
              stroke="none"
              isAnimationActive={!reduce}
            >
              {data.map((d, i) => (
                <Cell key={`${d.name}-${i}`} fill={colorFor(i)} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="grid max-h-56 grid-cols-2 gap-x-4 gap-y-1 overflow-auto text-xs text-muted-foreground sm:grid-cols-1" aria-label="Legend">
        {data.map((d, i) => (
          <li key={`${d.name}-${i}`} className="flex items-center gap-1.5">
            <span className="size-2.5 shrink-0 rounded-full" style={{ background: colorFor(i), boxShadow: `0 0 8px ${colorFor(i)}` }} />
            <span className="truncate">{d.name}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function TrendChart({
  data,
  series,
  height = 260,
}: {
  data: { month: string; [k: string]: number | string }[];
  series: { key: string; name: string; color: string; index: number }[];
  height?: number;
}) {
  const money = useMoney();
  const reduce = useReducedMotionFlag();
  const rows = data.map((d) => ({ ...d, label: monthLabel(d.month) }));
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: -4 }}>
          <ChartGradients id="tr" />
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="label" {...axisProps} />
          <YAxis tickFormatter={(v: number) => money.compact(v)} {...axisProps} />
          <Tooltip content={<ChartTooltip formatter={(v) => money(Number(v))} />} />
          {series.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2.5}
              fill={`url(#areatr-${s.index})`}
              activeDot={GlowDot(s.color)}
              dot={{ r: 3, fill: s.color }}
              isAnimationActive={!reduce}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function GroupedBars({
  data,
  xKey,
  series,
  height = 260,
  money: asMoney = true,
}: {
  data: Record<string, number | string>[];
  xKey: string;
  series: { key: string; name: string; color: string }[];
  height?: number;
  money?: boolean;
}) {
  const money = useMoney();
  const reduce = useReducedMotionFlag();
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -4 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey={xKey} interval={0} {...labelProps(data.length)} {...axisProps} />
          <YAxis tickFormatter={(v: number) => (asMoney ? money.compact(v) : `${v}`)} {...axisProps} />
          <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip formatter={(v) => (asMoney ? money(Number(v)) : String(v))} />} />
          {series.map((s) => (
            <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color} radius={[8, 8, 0, 0]} maxBarSize={44} isAnimationActive={!reduce} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** One bar per item, each a different palette colour (category distribution, goal progress...). */
export function ColorBars({
  data,
  height = 260,
  domain,
  format,
  name,
}: {
  data: { name: string; value: number }[];
  height?: number;
  domain?: [number, number];
  format: (v: number) => string;
  name: string;
}) {
  const reduce = useReducedMotionFlag();
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -4 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="name" interval={0} {...labelProps(data.length)} {...axisProps} />
          <YAxis domain={domain} tickFormatter={(v: number) => format(v)} {...axisProps} />
          <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip formatter={(v) => format(Number(v))} />} />
          <Bar dataKey="value" name={name} radius={[8, 8, 0, 0]} maxBarSize={52} isAnimationActive={!reduce}>
            {data.map((d, i) => (
              <Cell key={`${d.name}-${i}`} fill={SERIES[i % SERIES.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
