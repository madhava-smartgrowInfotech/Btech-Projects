import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Trash2, Search, Sprout, XCircle, Inbox } from 'lucide-react'
import { AppShell } from '../components/layout/AppShell'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { HistoryDetailModal } from '../components/history/HistoryDetailModal'
import { deleteHistoryItem, getHistory } from '../lib/api'
import type { PredictionRecord, SeedType } from '../types'

const seedTypes: (SeedType | 'All')[] = [
  'All',
  'Pearl Millet',
  'Finger Millet',
  'Foxtail Millet',
  'Little Millet',
  'Kodo Millet',
  'Proso Millet',
  'Barnyard Millet',
]

export function History() {
  const [records, setRecords] = useState<PredictionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [seedFilter, setSeedFilter] = useState<SeedType | 'All'>('All')
  const [outcomeFilter, setOutcomeFilter] = useState<'all' | 'germinate' | 'no_germinate'>('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<PredictionRecord | null>(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    setError(false)
    try {
      const data = await getHistory(50)
      setRecords(data)
    } catch (err) {
      console.error(err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    setRecords((prev) => prev.filter((r) => r.id !== id))
    try {
      await deleteHistoryItem(id)
    } catch (err) {
      console.error(err)
    }
  }

  const filtered = useMemo(() => {
    return records.filter((r) => {
      if (seedFilter !== 'All' && r.seed_type !== seedFilter) return false
      if (outcomeFilter !== 'all' && r.prediction !== outcomeFilter) return false
      if (search && !r.seed_type.toLowerCase().includes(search.toLowerCase()) && !r.id.toLowerCase().includes(search.toLowerCase())) return false
      return true
    })
  }, [records, seedFilter, outcomeFilter, search])

  return (
    <AppShell>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-display text-2xl sm:text-3xl font-bold">History</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1.5">
          Every prediction your team has run, filterable by variety and outcome.
        </p>
      </motion.div>

      <Card className="mb-6" padding="p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-faint)]" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by variety or ID…"
              className="w-full rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] pl-9 pr-3.5 py-2.5 text-sm focus:outline-none focus:border-emerald-500/60 transition-colors"
            />
          </div>
          <select
            value={seedFilter}
            onChange={(e) => setSeedFilter(e.target.value as SeedType | 'All')}
            className="rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] px-3.5 py-2.5 text-sm focus:outline-none focus:border-emerald-500/60"
          >
            {seedTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <select
            value={outcomeFilter}
            onChange={(e) => setOutcomeFilter(e.target.value as any)}
            className="rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] px-3.5 py-2.5 text-sm focus:outline-none focus:border-emerald-500/60"
          >
            <option value="all">All outcomes</option>
            <option value="germinate">Germinate</option>
            <option value="no_germinate">No germinate</option>
          </select>
        </div>
      </Card>

      {loading && (
        <div className="grid gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 rounded-2xl bg-[var(--color-surface)] animate-pulse" />
          ))}
        </div>
      )}

      {error && !loading && (
        <Card className="text-center py-16">
          <p className="text-sm text-[var(--color-text-muted)]">
            Couldn't load history — confirm the SeedIQ API is running.
          </p>
        </Card>
      )}

      {!loading && !error && filtered.length === 0 && (
        <Card className="text-center py-16 flex flex-col items-center gap-3">
          <Inbox className="text-[var(--color-text-faint)]" size={28} />
          <p className="text-sm text-[var(--color-text-muted)]">No predictions match these filters.</p>
        </Card>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="grid gap-3">
          {filtered.map((r, i) => (
            <motion.div
              key={r.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              onClick={() => setSelected(r)}
              className="glass rounded-2xl px-5 py-4 flex items-center gap-4 cursor-pointer hover:border-emerald-500/30 transition-colors"
            >
              {r.prediction === 'germinate' ? (
                <Sprout className="text-emerald-400 shrink-0" size={20} />
              ) : (
                <XCircle className="text-red-400 shrink-0" size={20} />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-sm">{r.seed_type}</span>
                  <Badge tone={r.prediction === 'germinate' ? 'emerald' : 'danger'}>
                    {r.prediction === 'germinate' ? 'Germinate' : 'No germinate'}
                  </Badge>
                  <Badge tone="neutral">{r.risk_level} risk</Badge>
                </div>
                <p className="text-xs text-[var(--color-text-faint)] mt-1">
                  {new Date(r.created_at).toLocaleString()} · Confidence {(r.confidence * 100).toFixed(1)}%
                </p>
              </div>
              <button
                onClick={(e) => handleDelete(r.id, e)}
                className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--color-text-faint)] hover:text-red-400 hover:bg-red-500/10 transition-colors shrink-0"
              >
                <Trash2 size={15} />
              </button>
            </motion.div>
          ))}
        </div>
      )}

      <HistoryDetailModal record={selected} onClose={() => setSelected(null)} />
    </AppShell>
  )
}
