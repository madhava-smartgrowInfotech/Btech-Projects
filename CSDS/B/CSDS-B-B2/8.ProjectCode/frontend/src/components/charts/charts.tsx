import type { ReactNode } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { cn } from "@/lib/utils";
import { ZONE_COLOR } from "@/lib/zones";
import type { TodCell, TrendDay } from "@/lib/analytics";

const AXIS = { fontSize: 11, fill: "var(--chart-text)" };
const shortDay = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { day: "numeric", month: "short" });

/** A single headline number with context - not a chart. */
export function StatTile({ label, value, hint, icon, tone }: { label: string; value: ReactNode; hint?: ReactNode; icon?: ReactNode; tone?: "bad" | "good" }) {
  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">{icon}{label}</p>
      <p className={cn("mt-2 font-display text-3xl font-bold tabular", tone === "bad" && "text-zone-dead", tone === "good" && "text-zone-strong")}>{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

/** Legend in ink colours; the swatch carries the identity. */
export function ChartLegend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <ul className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
      {items.map((i) => (
        <li key={i.label} className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: i.color }} aria-hidden />{i.label}</li>
      ))}
    </ul>
  );
}

const ZONE_LEGEND = (["Strong", "Weak", "Dead"] as const).map((k) => ({ label: k, color: ZONE_COLOR[k] }));

function ShareTooltip({ active, payload, label }: { active?: boolean; payload?: { payload: TrendDay }[]; label?: string }) {
  const d = active && payload?.[0]?.payload;
  if (!d) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-medium">{shortDay(label ?? d.day)} · {d.readings ? `${d.readings.toLocaleString()} readings` : "no readings"}</p>
      {d.readings > 0 && (["Strong", "Weak", "Dead"] as const).map((k) => (
        <p key={k} className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: ZONE_COLOR[k] }} /> {k}{" "}
          <span className="ml-auto pl-3 tabular">{Math.round((d[k.toLowerCase() as "dead"] / d.readings) * 100)}%</span>
        </p>
      ))}
    </div>
  );
}

/** Share of readings in each class per day (100% stacked bars; days without readings stay empty). */
export function ClassShareChart({ data, height = 240, className }: { data: TrendDay[]; height?: number; className?: string }) {
  return (
    <div className={cn("flex w-full flex-col", className)} style={className ? undefined : { height }}>
      <div className="min-h-0 flex-1">
        <ResponsiveContainer>
          <BarChart data={data} stackOffset="expand" margin={{ top: 8, right: 8, bottom: 0, left: -12 }} barCategoryGap="12%">
            <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
            <XAxis dataKey="day" tickFormatter={shortDay} tick={AXIS} stroke="var(--chart-grid)" minTickGap={28} />
            <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={AXIS} stroke="var(--chart-grid)" />
            <Tooltip content={<ShareTooltip />} cursor={{ fill: "var(--chart-grid)", opacity: 0.5 }} />
            <Bar dataKey="dead" name="Dead" stackId="1" fill={ZONE_COLOR.Dead} maxBarSize={24} isAnimationActive={false} />
            <Bar dataKey="weak" name="Weak" stackId="1" fill={ZONE_COLOR.Weak} maxBarSize={24} isAnimationActive={false} />
            <Bar dataKey="strong" name="Strong" stackId="1" fill={ZONE_COLOR.Strong} radius={[3, 3, 0, 0]} maxBarSize={24} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ChartLegend items={ZONE_LEGEND} />
    </div>
  );
}

/** Complaints registered and resolved per day (two categorical series). */
export function ComplaintFlowChart({ data, height = 220 }: { data: TrendDay[]; height?: number }) {
  const rows = data.filter((d) => d.registered || d.resolved);
  if (!rows.length) return <p className="py-12 text-center text-sm text-muted-foreground">No complaints registered in this period.</p>;
  return (
    <div className="w-full">
      <div style={{ height }}>
        <ResponsiveContainer>
          <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -20 }} barGap={2}>
          <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
          <XAxis dataKey="day" tickFormatter={shortDay} tick={AXIS} stroke="var(--chart-grid)" minTickGap={24} />
          <YAxis allowDecimals={false} tick={AXIS} stroke="var(--chart-grid)" />
          <Tooltip cursor={{ fill: "var(--chart-grid)", opacity: 0.4 }} labelFormatter={(l) => shortDay(String(l))}
            contentStyle={{ borderRadius: 8, fontSize: 12, background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))" }} />
          <Bar dataKey="registered" name="Registered" fill="var(--series-1)" radius={[4, 4, 0, 0]} maxBarSize={18} isAnimationActive={false} />
          <Bar dataKey="resolved" name="Resolved" fill="var(--series-3)" radius={[4, 4, 0, 0]} maxBarSize={18} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ChartLegend items={[{ label: "Registered", color: "var(--series-1)" }, { label: "Resolved", color: "var(--series-3)" }]} />
    </div>
  );
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
// Sequential single-hue ramp (orange) for "share of weak or dead readings": faint = few problems.
// Steps are theme tokens (--ramp-0..6) so dark mode has its own ramp, not a flipped one.
const RAMP = Array.from({ length: 7 }, (_, i) => `var(--ramp-${i})`);

export function TimeOfDayHeatmap({ cells }: { cells: TodCell[] }) {
  const map = new Map(cells.map((c) => [`${c.weekday}-${c.hour}`, c]));
  const color = (v: number) => RAMP[Math.min(RAMP.length - 1, Math.floor(v * RAMP.length))];
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] table-fixed border-separate" style={{ borderSpacing: 2 }}>
        <colgroup><col className="w-10" />{Array.from({ length: 24 }, (_, h) => <col key={h} />)}</colgroup>
        <thead>
          <tr>
            <th />
            {Array.from({ length: 24 }, (_, h) => (
              <th key={h} className="text-[10px] font-normal text-muted-foreground">{h % 3 === 0 ? String(h).padStart(2, "0") : ""}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {DAYS.map((d, wd) => (
            <tr key={d}>
              <th className="pr-1 text-right text-xs font-normal text-muted-foreground">{d}</th>
              {Array.from({ length: 24 }, (_, h) => {
                const c = map.get(`${wd}-${h}`);
                return (
                  <td key={h} className="h-6 rounded-[3px]" style={{ backgroundColor: c ? color(c.bad_share) : "hsl(var(--muted))" }}
                    title={c ? `${d} ${String(h).padStart(2, "0")}:00 - ${Math.round(c.bad_share * 100)}% weak or dead (${c.readings} readings)` : `${d} ${String(h).padStart(2, "0")}:00 - no readings`} />
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <span>0%</span>
        <div className="flex h-2.5 w-40 overflow-hidden rounded-full">{RAMP.map((c) => <span key={c} className="flex-1" style={{ backgroundColor: c }} />)}</div>
        <span>100% weak or dead</span>
        <span className="ml-3 inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-muted" /> no readings</span>
      </div>
    </div>
  );
}
