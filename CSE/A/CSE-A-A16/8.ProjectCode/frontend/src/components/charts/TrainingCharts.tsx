import { LineChart as LineIcon, TrendingDown } from "lucide-react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartTooltip, GlowDot, gridProps, SERIES } from "@/components/charts/Chart";

export interface History {
  accuracy?: number[];
  val_accuracy?: number[];
  loss?: number[];
  val_loss?: number[];
}

function rows(h: History, keys: (keyof History)[]) {
  const n = Math.max(0, ...keys.map((k) => h[k]?.length ?? 0));
  return Array.from({ length: n }, (_, i) => {
    const row: Record<string, number | null> = { epoch: i + 1 };
    for (const k of keys) row[k] = h[k]?.[i] ?? null;
    return row;
  });
}

function EpochChart({
  data,
  lines,
  percent,
}: {
  data: Record<string, number | null>[];
  lines: { key: string; name: string; color: string }[];
  percent?: boolean;
}) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="epoch" {...axisProps} allowDecimals={false} tickMargin={8} />
          <YAxis {...axisProps} width={44} domain={percent ? [0, 1] : ["auto", "auto"]} tickFormatter={(v: number) => (percent ? `${Math.round(v * 100)}%` : v.toFixed(2))} />
          <Tooltip
            content={
              <ChartTooltip
                labelFormatter={(l) => `Epoch ${l}`}
                formatter={(v) => (typeof v === "number" ? (percent ? `${(v * 100).toFixed(1)}%` : v.toFixed(4)) : String(v))}
              />
            }
          />
          {lines.map((l) => (
            <Line
              key={l.key}
              type="monotone"
              dataKey={l.key}
              name={l.name}
              stroke={l.color}
              strokeWidth={2.5}
              dot={data.length < 3 ? { r: 3, fill: l.color } : false}
              activeDot={GlowDot(l.color)}
              connectNulls
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Accuracy and loss per epoch, each with a "show as table" view. */
export function TrainingCharts({ history, running }: { history: History | null | undefined; running?: boolean }) {
  const h = history ?? {};
  const acc = rows(h, ["accuracy", "val_accuracy"]);
  const loss = rows(h, ["loss", "val_loss"]);
  const empty = acc.length === 0 ? (running ? "Waiting for the first epoch to finish…" : "No training history yet. Train a model to see the curves.") : undefined;
  const fmtPct = (v: number | null) => (v === null ? null : `${(v * 100).toFixed(1)}%`);
  const fmtNum = (v: number | null) => (v === null ? null : v.toFixed(4));

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <ChartCard
        title="Accuracy"
        description="Training vs validation, per epoch"
        icon={<LineIcon />}
        legend={[
          { label: "Training", color: SERIES[0] },
          { label: "Validation", color: SERIES[1] },
        ]}
        empty={empty}
        table={{ columns: ["Epoch", "Training", "Validation"], rows: acc.map((r) => [r.epoch, fmtPct(r.accuracy), fmtPct(r.val_accuracy)]) }}
      >
        <EpochChart
          data={acc}
          percent
          lines={[
            { key: "accuracy", name: "Training", color: SERIES[0] },
            { key: "val_accuracy", name: "Validation", color: SERIES[1] },
          ]}
        />
      </ChartCard>
      <ChartCard
        title="Loss"
        description="Lower is better"
        icon={<TrendingDown />}
        legend={[
          { label: "Training", color: SERIES[2] },
          { label: "Validation", color: SERIES[4] },
        ]}
        empty={empty}
        table={{ columns: ["Epoch", "Training", "Validation"], rows: loss.map((r) => [r.epoch, fmtNum(r.loss), fmtNum(r.val_loss)]) }}
      >
        <EpochChart
          data={loss}
          lines={[
            { key: "loss", name: "Training", color: SERIES[2] },
            { key: "val_loss", name: "Validation", color: SERIES[4] },
          ]}
        />
      </ChartCard>
    </div>
  );
}
