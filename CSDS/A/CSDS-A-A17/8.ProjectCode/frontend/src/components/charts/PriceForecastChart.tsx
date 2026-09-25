import { Area, CartesianGrid, ComposedChart, Line, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { dayLabel, formatCurrency } from "@/lib/format";

interface Props {
  forecast: Record<string, number>;
  confidenceLow: number;
  confidenceHigh: number;
  bestSellDay: number;
}

export function PriceForecastChart({ forecast, confidenceLow, confidenceHigh, bestSellDay }: Props) {
  const spread = confidenceHigh - confidenceLow;
  const data = Object.entries(forecast)
    .map(([offset, price]) => ({
      offset: Number(offset),
      label: dayLabel(Number(offset)),
      price,
      low: Math.max(0, price - spread * 0.4),
      bandHeight: spread * 0.8,
    }))
    .sort((a, b) => a.offset - b.offset);

  const bestPoint = data.find((d) => d.offset === bestSellDay);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4d7c0f" stopOpacity={0.28} />
            <stop offset="100%" stopColor="#4d7c0f" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="#eef0e8" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "#78716c" }}
          axisLine={{ stroke: "#e7e5df" }}
          tickLine={false}
          interval={4}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#78716c" }}
          axisLine={false}
          tickLine={false}
          width={56}
          tickFormatter={(v) => `₹${Math.round(v / 100) / 10}k`}
        />
        <Tooltip
          formatter={(value, name) => (name === "price" ? [formatCurrency(Number(value)), "Predicted price"] : ["", ""])}
          labelFormatter={(label) => label}
          contentStyle={{ borderRadius: 12, border: "1px solid #e7e5df", fontSize: 12 }}
        />
        <Area type="monotone" dataKey="low" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} />
        <Area
          type="monotone"
          dataKey="bandHeight"
          stackId="band"
          stroke="none"
          fill="url(#priceFill)"
          isAnimationActive={false}
        />
        <Line type="monotone" dataKey="price" stroke="#166534" strokeWidth={2.5} dot={false} activeDot={{ r: 5 }} />
        {bestPoint && (
          <ReferenceDot x={bestPoint.label} y={bestPoint.price} r={5.5} fill="#a3e635" stroke="#166534" strokeWidth={2} />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
