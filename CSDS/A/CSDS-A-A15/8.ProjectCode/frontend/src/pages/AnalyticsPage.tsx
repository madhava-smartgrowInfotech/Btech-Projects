import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { PageHeader } from '@/components/dashboard/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { analyticsApi, type AnalyticsSummary } from '@/lib/api'
import { formatPercent } from '@/lib/utils'

const PIE_COLORS = ['#22d3ee', '#8b5cf6', '#34d399', '#fbbf24', '#fb7185', '#60a5fa']
const SEVERITY_COLORS: Record<string, string> = { low: '#34d399', medium: '#fbbf24', high: '#fb7185' }

const tooltipStyle = {
  background: '#0b0f19',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 12,
  fontSize: 12,
}

export function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)

  useEffect(() => {
    analyticsApi.summary().then(setSummary)
  }, [])

  if (!summary) {
    return (
      <div className="p-8">
        <div className="h-8 w-8 rounded-full border-2 border-cyan-400/30 border-t-cyan-400 animate-spin" />
      </div>
    )
  }

  const defectData = Object.entries(summary.defect_distribution).map(([name, value]) => ({ name, value }))
  const severityData = Object.entries(summary.severity_distribution).map(([name, value]) => ({ name, value }))
  const metrics = summary.model_metrics

  const f1Data = metrics.classification_report
    ? Object.entries(metrics.classification_report)
        .filter(([k]) => !['accuracy', 'macro avg', 'weighted avg'].includes(k))
        .map(([label, stats]) => ({
          label,
          f1: Math.round(stats['f1-score'] * 1000) / 10,
        }))
    : []

  return (
    <div>
      <PageHeader title="Analytics" description="Inspection trends and model performance." />

      <div className="p-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <p className="text-xs text-slate-500 mb-1">Total inspections</p>
              <p className="font-display text-3xl font-bold text-white">{summary.total_inspections}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-xs text-slate-500 mb-1">Average confidence</p>
              <p className="font-display text-3xl font-bold text-white">
                {formatPercent(summary.average_confidence)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-xs text-slate-500 mb-1">Model test accuracy</p>
              <p className="font-display text-3xl font-bold text-white">
                {metrics.test_accuracy ? formatPercent(metrics.test_accuracy) : '—'}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Defect Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              {defectData.length === 0 ? (
                <EmptyState />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={defectData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={3}>
                      {defectData.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Severity Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {severityData.length === 0 ? (
                <EmptyState />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={severityData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={3}>
                      {severityData.map((entry, i) => (
                        <Cell key={i} fill={SEVERITY_COLORS[entry.name] ?? '#94a3b8'} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Inspections Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            {summary.inspections_over_time.length === 0 ? (
              <EmptyState />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={summary.inspections_over_time}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line type="monotone" dataKey="count" stroke="#22d3ee" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {f1Data.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Model Performance — Per-Class F1 Score</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={f1Data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v}%`, 'F1 score']} />
                  <Bar dataKey="f1" radius={[6, 6, 0, 0]}>
                    {f1Data.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="text-xs text-slate-500 mt-2">
                Evaluated on a held-out test split · trained {metrics.trained_at ?? 'recently'}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="h-56 flex items-center justify-center text-sm text-slate-500">
      Not enough data yet — run a few inspections first.
    </div>
  )
}
