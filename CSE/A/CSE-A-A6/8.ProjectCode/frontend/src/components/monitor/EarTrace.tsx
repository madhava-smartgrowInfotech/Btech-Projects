import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { axisProps, ChartGradients, gridProps } from "@/components/charts/Chart";
import type { TracePoint } from "@/lib/useRiderSession";

/** The last ~15 s of smoothed EAR from the server, with the closed-eye threshold drawn across it. */
export function EarTrace({ points, threshold }: { points: TracePoint[]; threshold: number }) {
  const data = points.map((p, i) => ({ i, ear: p.ear }));
  return (
    <div className="h-36 w-full" role="img" aria-label={`Live eye aspect ratio trace with the closed-eye threshold at ${threshold.toFixed(3)}`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
          <ChartGradients id="ear" />
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="i" hide />
          <YAxis {...axisProps} domain={[0, 0.5]} ticks={[0, 0.1, 0.2, 0.3, 0.4, 0.5]} />
          <ReferenceLine y={threshold} stroke="#FB7185" strokeDasharray="5 4" label={{ value: "threshold", fill: "#FB7185", fontSize: 10, position: "insideTopRight" }} />
          <Area type="monotone" dataKey="ear" stroke="#22D3EE" strokeWidth={2} fill="url(#area-ear-1)" isAnimationActive={false} connectNulls={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
