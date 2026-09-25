import { Line, LineChart, ReferenceArea, ResponsiveContainer, YAxis } from "recharts";
import type { SensorReading } from "@/types";
import { cn } from "@/lib/format";

interface MetricProps {
  title: string;
  unit: string;
  data: { i: number; value: number }[];
  safeMin: number;
  safeMax: number;
  current: number;
  alert: boolean;
  color: string;
}

function MetricSparkline({ title, unit, data, safeMin, safeMax, current, alert, color }: MetricProps) {
  return (
    <div className={cn("rounded-xl border p-3", alert ? "border-rose-300 bg-rose-50/60" : "border-ink-100 bg-white")}>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-medium text-ink-500">{title}</span>
        <span className={cn("text-lg font-semibold tabular-nums", alert ? "text-rose-600" : "text-ink-900")}>
          {current.toFixed(1)}
          <span className="text-xs font-normal text-ink-400">{unit}</span>
        </span>
      </div>
      <ResponsiveContainer width="100%" height={64}>
        <LineChart data={data}>
          <YAxis hide domain={["dataMin - 2", "dataMax + 2"]} />
          <ReferenceArea y1={safeMin} y2={safeMax} fill="#4d7c0f" fillOpacity={0.08} />
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LiveSensorChart({ readings }: { readings: SensorReading[] }) {
  const ordered = [...readings].reverse();
  const withIndex = (key: keyof SensorReading) => ordered.map((r, i) => ({ i, value: r[key] as number }));
  const latest = ordered[ordered.length - 1];
  const anyAnomaly = ordered.slice(-5).some((r) => r.is_anomaly);

  if (!latest) return <p className="text-sm text-ink-500">Waiting for sensor data…</p>;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <MetricSparkline
        title="Temperature"
        unit="°C"
        data={withIndex("temperature_c")}
        safeMin={2}
        safeMax={8}
        current={latest.temperature_c}
        alert={anyAnomaly && (latest.temperature_c < 0.5 || latest.temperature_c > 9.5)}
        color="#0284c7"
      />
      <MetricSparkline
        title="Humidity"
        unit="%"
        data={withIndex("humidity_pct")}
        safeMin={55}
        safeMax={75}
        current={latest.humidity_pct}
        alert={anyAnomaly && (latest.humidity_pct < 47 || latest.humidity_pct > 83)}
        color="#4d7c0f"
      />
      <MetricSparkline
        title="Shock"
        unit="g"
        data={withIndex("shock_g")}
        safeMin={0}
        safeMax={2.4}
        current={latest.shock_g}
        alert={latest.shock_g >= 2.4}
        color="#d97706"
      />
    </div>
  );
}
