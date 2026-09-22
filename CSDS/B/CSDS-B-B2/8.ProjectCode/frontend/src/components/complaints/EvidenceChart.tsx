import { useMemo } from "react";
import { CartesianGrid, Cell, ComposedChart, Line, ResponsiveContainer, Scatter, Tooltip, XAxis, YAxis } from "recharts";
import type { Evidence } from "@/lib/complaints";
import { ZONE_COLOR, type ZoneLabel } from "@/lib/zones";

type Metric = { key: "rsrp" | "latency_ms" | "wifi_rssi" | "dl_mbps"; label: string; unit: string };
const METRICS: Metric[] = [
  { key: "rsrp", label: "Signal level (RSRP)", unit: "dBm" },
  { key: "latency_ms", label: "Round-trip latency", unit: "ms" },
  { key: "wifi_rssi", label: "Wi-Fi signal", unit: "dBm" },
  { key: "dl_mbps", label: "Download speed", unit: "Mbps" },
];

/** The primary metric over time; each reading is a dot in its class colour (legend below, tooltip on hover). */
export function EvidenceChart({ series }: { series: NonNullable<Evidence["series"]> }) {
  const metric = METRICS.find((m) => series.filter((p) => p[m.key] != null).length >= Math.max(2, series.length * 0.3)) ?? null;
  // Break the line across long gaps (separate visits) so it never implies readings that were not taken.
  const data = useMemo(() => {
    const pts = series.map((p) => ({ t: new Date(p.ts).getTime(), v: metric ? (p[metric.key] as number | null) : null, label: p.label })).filter((d) => d.v != null);
    if (pts.length < 2) return pts;
    const gap = Math.max(10 * 60_000, (pts[pts.length - 1]!.t - pts[0]!.t) * 0.05);
    const out: { t: number; v: number | null; label: ZoneLabel; gap?: boolean }[] = [];
    pts.forEach((p, i) => {
      if (i && p.t - pts[i - 1]!.t > gap) out.push({ t: (p.t + pts[i - 1]!.t) / 2, v: null, label: p.label, gap: true });
      out.push(p);
    });
    return out;
  }, [series, metric]);
  if (!metric || data.length < 2) {
    return <p className="py-10 text-center text-sm text-muted-foreground">Not enough metric values to chart - the evidence is in the tables above.</p>;
  }
  const spanDays = (data[data.length - 1]!.t - data[0]!.t) / 86_400_000;
  const fmt = (t: number) => new Date(t).toLocaleString(undefined, spanDays > 2 ? { day: "numeric", month: "short" } : { hour: "2-digit", minute: "2-digit" });

  return (
    <div>
      <p className="mb-2 text-xs text-muted-foreground">{metric.label} ({metric.unit})</p>
      <div className="h-56 w-full">
        <ResponsiveContainer>
          <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="0" vertical={false} />
            <XAxis dataKey="t" type="number" domain={["dataMin", "dataMax"]} tickFormatter={fmt} tick={{ fontSize: 11, fill: "var(--chart-text)" }} stroke="var(--chart-grid)" minTickGap={40} />
            <YAxis dataKey="v" width={44} tick={{ fontSize: 11, fill: "var(--chart-text)" }} stroke="var(--chart-grid)" domain={["auto", "auto"]} />
            <Tooltip
              cursor={{ stroke: "var(--chart-text)", strokeWidth: 1, strokeDasharray: "3 3" }}
              content={({ active, payload }) => {
                const p = active && payload?.[0]?.payload as { t: number; v: number | null; label: ZoneLabel } | undefined;
                if (!p || p.v == null) return null;
                return (
                  <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
                    <p className="text-muted-foreground">{new Date(p.t).toLocaleString()}</p>
                    <p className="mt-0.5 font-mono font-semibold">{Number(p.v).toFixed(metric.key === "dl_mbps" ? 1 : 0)} {metric.unit}</p>
                    <p className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: ZONE_COLOR[p.label] }} />{p.label}</p>
                  </div>
                );
              }}
            />
            <Line dataKey="v" type="linear" stroke="var(--series-1)" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
            <Scatter dataKey="v" isAnimationActive={false}>
              {data.map((d, i) => <Cell key={i} fill={d.v == null ? "transparent" : ZONE_COLOR[d.label]} stroke={d.v == null ? "transparent" : "var(--background)"} strokeWidth={1.5} r={4} />)}
            </Scatter>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
        {(Object.keys(ZONE_COLOR) as ZoneLabel[]).map((z) => (
          <span key={z} className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ZONE_COLOR[z] }} />{z}</span>
        ))}
      </div>
    </div>
  );
}
