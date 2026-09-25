import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ClassProbability } from '@/lib/api'

const COLORS = ['#22d3ee', '#8b5cf6', '#34d399', '#fbbf24', '#fb7185', '#60a5fa']

export function ClassProbabilityChart({ data }: { data: ClassProbability[] }) {
  const chartData = data.map((d) => ({ ...d, percent: Math.round(d.probability * 1000) / 10 }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis
          type="category"
          dataKey="display_name"
          width={120}
          tick={{ fill: '#94a3b8', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          contentStyle={{
            background: '#0b0f19',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 12,
            fontSize: 12,
          }}
          formatter={(value) => [`${value}%`, 'Confidence']}
        />
        <Bar dataKey="percent" radius={[0, 6, 6, 0]} barSize={16}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
