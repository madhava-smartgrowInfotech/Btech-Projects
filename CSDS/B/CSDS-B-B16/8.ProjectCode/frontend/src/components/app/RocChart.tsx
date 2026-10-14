import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartTooltip, gridProps, SERIES } from "@/components/charts/Chart";
import type { RocCurve } from "@/lib/types";

const TICKS = [0, 0.25, 0.5, 0.75, 1];

/** ROC curve with the chance diagonal. Lazy-loaded with the performance page. */
export default function RocChart({ curve, auc }: { curve: RocCurve; auc: number }) {
  const data = curve.fpr.map((fpr, i) => ({ fpr, tpr: curve.tpr[i] }));
  return (
    <div className="h-64 w-full" role="img" aria-label={`ROC curve, AUC ${auc.toFixed(3)}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 20, left: 0 }}>
          <CartesianGrid {...gridProps} vertical />
          <XAxis
            type="number"
            dataKey="fpr"
            domain={[0, 1]}
            ticks={TICKS}
            {...axisProps}
            label={{ value: "False positive rate", position: "insideBottom", offset: -10, fontSize: 11, fill: "var(--chart-axis)" }}
          />
          <YAxis
            type="number"
            domain={[0, 1]}
            ticks={TICKS}
            width={36}
            {...axisProps}
            label={{ value: "True positive rate", angle: -90, position: "insideLeft", fontSize: 11, fill: "var(--chart-axis)" }}
          />
          <Tooltip content={<ChartTooltip formatter={(v) => Number(v).toFixed(3)} labelFormatter={(l) => `FPR ${Number(l).toFixed(3)}`} />} />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--chart-axis)" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="tpr" name="True positive rate" stroke={SERIES[0]} strokeWidth={2.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
