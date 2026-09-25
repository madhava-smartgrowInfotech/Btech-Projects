import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { Activity, Target, Percent, Gauge } from 'lucide-react'
import { AppShell } from '../components/layout/AppShell'
import { Card } from '../components/ui/Card'
import { ConfusionMatrix } from '../components/insights/ConfusionMatrix'
import { getModelInfo, getStats } from '../lib/api'
import type { ModelInfoResponse, StatsResponse } from '../types'

const PIE_COLORS = ['#34d399', '#fbbf24', '#6ee7b7', '#f59e0b', '#059669', '#d97706', '#a7f3d0']

const tooltipStyle = {
  background: '#0e1712',
  border: '1px solid #1e2f26',
  borderRadius: 12,
  fontSize: 12,
  color: '#eef6f1',
}

export function Insights() {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([getStats(), getModelInfo()])
      .then(([s, m]) => {
        setStats(s)
        setModelInfo(m)
      })
      .catch((err) => {
        console.error(err)
        setError(true)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <AppShell>
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-40 rounded-2xl bg-[var(--color-surface)] animate-pulse" />
          ))}
        </div>
      </AppShell>
    )
  }

  if (error || !stats || !modelInfo) {
    return (
      <AppShell>
        <Card className="text-center py-16">
          <p className="text-sm text-[var(--color-text-muted)]">
            Couldn't load insights — confirm the SeedIQ API is running.
          </p>
        </Card>
      </AppShell>
    )
  }

  const metricsData = [
    { name: 'Accuracy', value: stats.model_metrics.accuracy },
    { name: 'Precision', value: stats.model_metrics.precision },
    { name: 'Recall', value: stats.model_metrics.recall },
    { name: 'F1', value: stats.model_metrics.f1 },
  ]

  const seedBreakdown = Object.entries(stats.seed_type_breakdown).map(([name, value]) => ({ name, value }))

  return (
    <AppShell>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-display text-2xl sm:text-3xl font-bold">Insights</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1.5">
          Model performance and prediction analytics across every batch processed.
        </p>
      </motion.div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Activity} label="Total predictions" value={stats.total_predictions.toLocaleString()} />
        <StatCard icon={Target} label="Germination rate" value={`${(stats.germination_rate * 100).toFixed(1)}%`} />
        <StatCard icon={Percent} label="Avg. confidence" value={`${(stats.avg_confidence * 100).toFixed(1)}%`} />
        <StatCard icon={Gauge} label="Model accuracy" value={`${(stats.model_metrics.accuracy * 100).toFixed(1)}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <Card>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
            Model metrics
          </h4>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={metricsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f26" vertical={false} />
              <XAxis dataKey="name" stroke="#5f7a6e" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#5f7a6e" fontSize={12} tickLine={false} axisLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`} />
              <Bar dataKey="value" fill="#34d399" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
            Confusion matrix
          </h4>
          <div className="flex items-center justify-center h-[240px]">
            <div className="w-full max-w-xs">
              <ConfusionMatrix matrix={stats.model_metrics.confusion_matrix} />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <Card>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
            Germination rate trend
          </h4>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={stats.trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f26" vertical={false} />
              <XAxis dataKey="date" stroke="#5f7a6e" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#5f7a6e" fontSize={12} tickLine={false} axisLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`} />
              <Line type="monotone" dataKey="germination_rate" stroke="#fbbf24" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
            Variety distribution
          </h4>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={seedBreakdown} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3}>
                {seedBreakdown.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="none" />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#9db3a8' }} />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
            Architecture
          </h4>
          <div className="flex flex-col gap-3">
            {modelInfo.pipeline_stages.map((s) => (
              <div key={s.stage} className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3">
                <span className="text-sm font-medium text-emerald-300">{s.stage}</span>
                <p className="text-xs text-[var(--color-text-muted)] mt-1">{s.description}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
            Global feature importance
          </h4>
          <ResponsiveContainer width="100%" height={Math.max(220, modelInfo.global_feature_importance.length * 34)}>
            <BarChart data={modelInfo.global_feature_importance} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f26" horizontal={false} />
              <XAxis type="number" stroke="#5f7a6e" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis dataKey="feature" type="category" stroke="#5f7a6e" fontSize={11} tickLine={false} axisLine={false} width={120} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="importance" fill="#fbbf24" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </AppShell>
  )
}

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <Card padding="p-5">
      <Icon size={17} className="text-emerald-300 mb-3" />
      <div className="font-display text-2xl font-bold">{value}</div>
      <p className="text-xs text-[var(--color-text-faint)] mt-1">{label}</p>
    </Card>
  )
}
