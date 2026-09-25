import { AlertTriangle, CheckCircle2, Gauge, ScanSearch } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { InspectionCard } from '@/components/dashboard/InspectionCard'
import { PageHeader } from '@/components/dashboard/PageHeader'
import { UploadCard } from '@/components/dashboard/UploadCard'
import { Card, CardContent } from '@/components/ui/Card'
import { useAuth } from '@/context/AuthContext'
import { inspectionsApi, type InspectionOut } from '@/lib/api'
import { formatPercent } from '@/lib/utils'

export function DashboardPage() {
  const { user } = useAuth()
  const [inspections, setInspections] = useState<InspectionOut[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    inspectionsApi
      .list()
      .then(setInspections)
      .finally(() => setLoading(false))
  }, [])

  const total = inspections.length
  const avgConfidence = total ? inspections.reduce((s, i) => s + i.confidence, 0) / total : 0
  const highSeverity = inspections.filter((i) => i.severity === 'high').length

  const stats = [
    { label: 'Total inspections', value: total, icon: ScanSearch, color: 'text-cyan-300' },
    { label: 'Average confidence', value: formatPercent(avgConfidence), icon: Gauge, color: 'text-violet-300' },
    { label: 'High severity flags', value: highSeverity, icon: AlertTriangle, color: 'text-rose-300' },
    {
      label: 'Resolved / tracked',
      value: total - highSeverity,
      icon: CheckCircle2,
      color: 'text-emerald-300',
    },
  ]

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${user?.name?.split(' ')[0] ?? 'Inspector'}`}
        description="Here's what's happening across your inspection line."
      />

      <div className="p-8 space-y-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardContent className="pt-6">
                <stat.icon className={`h-5 w-5 ${stat.color} mb-3`} />
                <p className="font-display text-2xl font-bold text-white">{stat.value}</p>
                <p className="text-xs text-slate-500 mt-1">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1">
            <CardContent className="pt-6">
              <h2 className="font-display text-base font-semibold text-white mb-4">Quick Inspection</h2>
              <UploadCard />
            </CardContent>
          </Card>

          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-base font-semibold text-white">Recent Inspections</h2>
              <Link to="/app/history" className="text-sm text-cyan-400 hover:text-cyan-300">
                View all →
              </Link>
            </div>

            {loading ? (
              <div className="glass-card rounded-2xl p-10 text-center text-slate-500 text-sm">Loading…</div>
            ) : inspections.length === 0 ? (
              <div className="glass-card rounded-2xl p-10 text-center">
                <p className="text-slate-400 text-sm">No inspections yet. Run your first one to get started.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {inspections.slice(0, 4).map((i) => (
                  <InspectionCard key={i.id} inspection={i} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
