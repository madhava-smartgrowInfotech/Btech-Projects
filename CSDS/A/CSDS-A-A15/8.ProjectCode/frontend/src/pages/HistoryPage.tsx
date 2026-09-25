import { useEffect, useMemo, useState } from 'react'
import { InspectionCard } from '@/components/dashboard/InspectionCard'
import { PageHeader } from '@/components/dashboard/PageHeader'
import { inspectionsApi, type InspectionOut } from '@/lib/api'
import { cn } from '@/lib/utils'

const SEVERITY_FILTERS = ['all', 'low', 'medium', 'high'] as const

export function HistoryPage() {
  const [inspections, setInspections] = useState<InspectionOut[]>([])
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState<(typeof SEVERITY_FILTERS)[number]>('all')
  const [defectFilter, setDefectFilter] = useState<string>('all')

  useEffect(() => {
    inspectionsApi
      .list()
      .then(setInspections)
      .finally(() => setLoading(false))
  }, [])

  const defectTypes = useMemo(
    () => Array.from(new Set(inspections.map((i) => i.display_name))),
    [inspections],
  )

  const filtered = inspections.filter((i) => {
    if (severityFilter !== 'all' && i.severity !== severityFilter) return false
    if (defectFilter !== 'all' && i.display_name !== defectFilter) return false
    return true
  })

  return (
    <div>
      <PageHeader title="Inspection History" description="All inspections run on your account." />

      <div className="p-8 space-y-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-xl bg-white/5 p-1">
            {SEVERITY_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setSeverityFilter(s)}
                className={cn(
                  'px-3 py-1.5 text-xs font-medium rounded-lg capitalize transition-colors',
                  severityFilter === s ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white',
                )}
              >
                {s}
              </button>
            ))}
          </div>

          <select
            value={defectFilter}
            onChange={(e) => setDefectFilter(e.target.value)}
            className="rounded-xl bg-white/5 border border-white/10 px-3 py-1.5 text-xs text-slate-300 outline-none focus:border-cyan-400/50"
          >
            <option value="all">All defect types</option>
            {defectTypes.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <span className="text-xs text-slate-500 ml-auto">{filtered.length} results</span>
        </div>

        {loading ? (
          <div className="glass-card rounded-2xl p-10 text-center text-slate-500 text-sm">Loading…</div>
        ) : filtered.length === 0 ? (
          <div className="glass-card rounded-2xl p-10 text-center text-slate-400 text-sm">
            No inspections match these filters.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((i) => (
              <InspectionCard key={i.id} inspection={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
