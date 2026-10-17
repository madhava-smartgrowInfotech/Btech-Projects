import { Bell, RefreshCw, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { describeError } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Button, SearchField, Switch } from '../components/ui/controls'
import { Badge, Card, Severity, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Modal, Skeleton, useToast } from '../components/ui/feedback'
import { Tabs } from '../components/ui/nav'
import Table from '../components/ui/Table'
import { Stagger } from '../components/motion'
import { pct } from '../format'
import { logEvent } from '../lib/activity'

const SEVERITIES = ['critical', 'high', 'medium']

export default function Alerts() {
  const toast = useToast()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sev, setSev] = useState('all')
  const [q, setQ] = useState('')
  const [auto, setAuto] = useState(false)
  const [confirm, setConfirm] = useState(false)
  const [clearing, setClearing] = useState(false)

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      const r = await api.get('/alerts', { params: { limit: 500 }, silent })
      setData(r.data)
      setError(null)
    } catch (e) {
      setError(describeError(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    if (!auto) return
    const id = setInterval(() => load(true), 5000)
    return () => clearInterval(id)
  }, [auto, load])

  async function clearAll() {
    setClearing(true)
    try {
      await api.delete('/alerts')
      logEvent('ids', 'alerts cleared')
      toast({ tone: 'ok', title: 'Alerts cleared' })
      setConfirm(false)
      await load()
    } catch (e) {
      toast({ tone: 'alert', title: 'Could not clear alerts', body: describeError(e).message })
    } finally {
      setClearing(false)
    }
  }

  const alerts = data?.alerts
  const counts = useMemo(() => Object.fromEntries(SEVERITIES.map((s) => [s, alerts?.filter((a) => a.severity === s).length ?? 0])), [alerts])
  const rows = useMemo(() => {
    if (!alerts) return null
    const term = q.trim().toLowerCase()
    return alerts.filter((a) => (sev === 'all' || a.severity === sev)
      && (!term || `${a.timestamp} ${Object.values(a.features || {}).join(' ')}`.toLowerCase().includes(term)))
  }, [alerts, sev, q])

  const columns = [
    { key: 'timestamp', label: 'Timestamp', sortable: true, render: (r) => <span className="font-mono text-xs text-muted">{r.timestamp}</span> },
    { key: 'severity', label: 'Severity', sortable: true, sortValue: (r) => SEVERITIES.length - SEVERITIES.indexOf(r.severity), render: (r) => <Severity s={r.severity} /> },
    { key: 'confidence', label: 'Confidence', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => pct(r.confidence) },
    { key: 'features', label: 'Flow features', render: (r) => (
      <div className="flex flex-wrap gap-1">{Object.entries(r.features || {}).map(([k, v]) => <Badge key={k}>{k} {String(v)}</Badge>)}</div>
    ) },
    { key: 'scores', label: 'XGB / CNN', render: (r) => <span className="font-mono text-xs tabular-nums text-muted">{pct(r.scores?.xgb)} / {pct(r.scores?.cnn)}</span> },
  ]

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Detections" title="Alerts"
        subtitle="Every flow the ensemble labels an attack is logged here by the backend (latest 500, kept in memory until the server restarts or you clear them)."
        actions={(
          <>
            <Switch checked={auto} onChange={setAuto} label="auto-refresh 5s" />
            <Button variant="secondary" icon={RefreshCw} onClick={() => load()} loading={loading && !!data}>Refresh</Button>
            <Button variant="danger" icon={Trash2} onClick={() => setConfirm(true)} disabled={!data?.total}>Clear all</Button>
          </>
        )} />

      {error && <ErrorState error={error} onRetry={() => load()} title="Could not load alerts" />}

      <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Total alerts" value={data?.total ?? '-'} icon={Bell} tone="warn" live={auto} />
        {SEVERITIES.map((s) => (
          <StatCard key={s} label={s} value={data ? counts[s] : '-'} tone={s === 'critical' ? 'alert' : s === 'high' ? 'hot' : 'warn'} />
        ))}
      </Stagger>

      <Card title="Alert log" eyebrow={data ? `${rows?.length ?? 0} of ${data.total} shown` : 'loading'}>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Tabs id="sev" label="Filter by severity" value={sev} onChange={setSev}
            tabs={[{ id: 'all', label: 'All', count: data?.total }, ...SEVERITIES.map((s) => ({ id: s, label: s, count: data ? counts[s] : undefined }))]} />
          <SearchField value={q} onChange={setQ} label="Search alerts" placeholder="Search time, proto, service..." className="sm:w-72" />
        </div>
        {loading && !data ? (
          <div className="space-y-2">{Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-9 w-full" />)}</div>
        ) : (
          <Table columns={columns} rows={rows} rowKey={(r) => `${r.timestamp}-${r.confidence}-${JSON.stringify(r.features)}`} pageSize={12}
            initialSort={{ key: 'timestamp', dir: 'desc' }} caption="Detected intrusions"
            empty={data?.total
              ? <EmptyState icon={Bell} title="No alerts match this filter" body="Try another severity or clear the search box." action={<Button variant="secondary" size="sm" onClick={() => { setSev('all'); setQ('') }}>Reset filters</Button>} />
              : <EmptyState icon={Bell} title="No alerts yet" body="Alerts appear when the engine labels a flow as an attack. Score a record or a batch to generate some."
                action={<Link to="/app" className="inline-flex h-8 items-center rounded-[6px] border border-line-strong bg-panel-2 px-3 text-xs font-medium text-fg hover:border-ok/60 hover:text-ok">Go to live scoring</Link>} />}
            cards={(r) => (
              <div className="space-y-1.5 rounded border border-line bg-panel-2 p-3 text-xs">
                <div className="flex items-center justify-between"><Severity s={r.severity} /><span className="font-mono tabular-nums">{pct(r.confidence)}</span></div>
                <div className="font-mono text-muted">{r.timestamp}</div>
                <div className="font-mono text-dim">{Object.values(r.features || {}).join(' / ')}</div>
              </div>
            )} />
        )}
      </Card>

      <Modal open={confirm} onClose={() => setConfirm(false)} title="Clear all alerts" size="sm"
        footer={(
          <>
            <Button variant="ghost" onClick={() => setConfirm(false)}>Cancel</Button>
            <Button variant="danger" loading={clearing} onClick={clearAll}>Clear {data?.total} alerts</Button>
          </>
        )}>
        <p className="p-4 text-sm text-muted">This removes all {data?.total} alerts from the backend's in-memory log. It cannot be undone.</p>
      </Modal>
    </div>
  )
}
