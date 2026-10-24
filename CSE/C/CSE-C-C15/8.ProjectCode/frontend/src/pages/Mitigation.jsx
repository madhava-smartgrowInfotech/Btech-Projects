import { ShieldAlert, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import Table from '../components/ui/Table'
import { Button } from '../components/ui/controls'
import { Badge, Card, StatCard, StatusDot } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton, ProgressBar } from '../components/ui/feedback'
import { dateTime } from '../format'
import { useLive } from '../lib/live'

// Local clock so the quarantine timers tick smoothly between polls.
function useNow() {
  const [now, setNow] = useState(() => Date.now() / 1000)
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now() / 1000), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

export default function Mitigation() {
  const { loaded, error, refresh, mitigations } = useLive()
  const now = useNow()
  if (!loaded) return <PageSkeleton />

  const active = mitigations?.active || []
  const history = mitigations?.history || []
  const columns = [
    { key: 'timestamp', label: 'Time', sortable: true, render: (h) => <span className="font-mono text-xs text-muted">{dateTime(h.timestamp)}</span> },
    { key: 'ip', label: 'Source IP', sortable: true, render: (h) => <span className="font-mono text-xs text-fg">{h.ip}</span> },
    { key: 'status', label: 'Status', sortable: true, render: (h) => <Badge tone={h.status === 'active' ? 'alert' : 'ok'} dot>{h.status}</Badge> },
    { key: 'duration', label: 'Duration', align: 'right', sortable: true, render: (h) => <span className="font-mono text-xs tabular-nums">{h.duration}s</span> },
    { key: 'reason', label: 'Reason', render: (h) => <span className="text-xs text-muted">{h.reason}</span> },
  ]

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="console / mitigation" title="Mitigation center"
        subtitle="High and critical windows quarantine the top suspicious sources inside SentinelFlow. Quarantines expire on their own; the OS firewall is never touched." />
      {error && <ErrorState error={error} title="Backend unreachable" onRetry={refresh} />}
      <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        <StatCard label="Active quarantines" tone={active.length ? 'alert' : 'ok'} icon={ShieldAlert} value={active.length} live={active.length > 0} />
        <StatCard label="Recorded actions" value={history.length} sub="latest 100 in history" />
        <StatCard label="Quarantine length" value={`${mitigations?.quarantine_seconds ?? '-'}s`} sub="doubled for critical windows" />
      </Stagger>
      <Card title="Active quarantines" action={<span className="font-mono text-[11px] text-dim">auto-recover</span>}>
        {active.length === 0 ? (
          <EmptyState icon={ShieldCheck} title="No sources are quarantined" body="Quarantines appear when a high or critical attack window is scored."
            action={<Link to="/app"><Button variant="secondary">Open session control</Button></Link>} />
        ) : (
          <ul className="grid gap-3 md:grid-cols-2">
            {active.map((a) => {
              const left = Math.max(0, Math.round(a.expires_at - now))
              return (
                <li key={a.ip} className="rounded-[6px] border border-alert/30 bg-alert/[0.05] p-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2 font-mono text-sm text-fg"><StatusDot tone="alert" />{a.ip}</span>
                    <Badge tone="alert">{left}s left</Badge>
                  </div>
                  <ProgressBar value={a.duration ? (left / a.duration) * 100 : 0} tone="alert" segments={28} label={`of ${a.duration}s`} />
                  <p className="mt-2 truncate text-xs text-muted" title={a.reason}>{a.reason}</p>
                </li>
              )
            })}
          </ul>
        )}
      </Card>
      <Card title="Mitigation history">
        <Table caption="Mitigation history" columns={columns} rows={history} rowKey={(h) => h.id} initialSort={{ key: 'timestamp', dir: 'desc' }} pageSize={10}
          empty={<EmptyState icon={ShieldCheck} title="No mitigation history" body="Nothing has been quarantined yet." />}
          cards={(h) => (
            <div className="panel space-y-1 p-3">
              <div className="flex items-center justify-between"><span className="font-mono text-sm">{h.ip}</span><Badge tone={h.status === 'active' ? 'alert' : 'ok'} dot>{h.status}</Badge></div>
              <div className="font-mono text-[11px] text-muted">{dateTime(h.timestamp)} · {h.duration}s</div>
              <div className="text-xs text-dim">{h.reason}</div>
            </div>
          )} />
      </Card>
    </div>
  )
}
