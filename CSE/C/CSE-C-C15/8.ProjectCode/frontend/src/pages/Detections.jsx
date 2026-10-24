import { Activity, ListTree } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ThreatDetail from '../components/app/ThreatDetail'
import { PageHeader } from '../components/ui/AppShell'
import Table from '../components/ui/Table'
import { Button, SearchField, Select } from '../components/ui/controls'
import { Card, Prediction, Severity } from '../components/ui/display'
import { Badge } from '../components/ui/display'
import { Drawer, EmptyState, ErrorState, PageSkeleton } from '../components/ui/feedback'
import { clock, fmt, mitLabel, mitTone, pct, SEVERITIES } from '../format'
import { useLive } from '../lib/live'

export default function Detections() {
  const { loaded, error, refresh, detections, status, busy, startSim } = useLive()
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState('')
  const [pred, setPred] = useState('all')
  const [sev, setSev] = useState('all')
  const [openId, setOpenId] = useState(() => params.get('id'))

  useEffect(() => { setOpenId(params.get('id')) }, [params])

  const rows = useMemo(() => {
    const term = q.trim().toLowerCase()
    return detections.filter((d) => (pred === 'all' || d.prediction === pred) && (sev === 'all' || d.severity === sev)
      && (!term || [d.id, d.source, d.interface, d.mitigation_status, d.prediction, d.severity].join(' ').toLowerCase().includes(term)))
  }, [detections, q, pred, sev])

  const selected = openId ? detections.find((d) => String(d.id) === String(openId)) : null
  const select = (d) => setParams(d ? { id: d.id } : {}, { replace: true })

  const columns = [
    { key: 'timestamp', label: 'Time', sortable: true, render: (d) => <span className="font-mono text-xs text-muted">{clock(d.timestamp)}</span> },
    { key: 'id', label: 'Window', sortable: true, render: (d) => <span className="font-mono text-xs">#{d.id}</span> },
    { key: 'source', label: 'Source', render: (d) => <span className="text-xs text-muted">{d.source}</span> },
    { key: 'prediction', label: 'Prediction', sortable: true, render: (d) => <Prediction p={d.prediction} /> },
    { key: 'confidence', label: 'Conf.', align: 'right', sortable: true, render: (d) => <span className="font-mono text-xs tabular-nums">{pct(d.confidence)}</span> },
    { key: 'severity', label: 'Severity', sortable: true, sortValue: (d) => SEVERITIES.indexOf(d.severity), render: (d) => <Severity s={d.severity} /> },
    { key: 'source_count', label: 'Srcs', align: 'right', sortable: true, render: (d) => <span className="font-mono text-xs tabular-nums">{fmt(d.source_count)}</span> },
    { key: 'destination_count', label: 'Dsts', align: 'right', sortable: true, render: (d) => <span className="font-mono text-xs tabular-nums">{fmt(d.destination_count)}</span> },
    { key: 'packet_rate', label: 'Pkt/s', align: 'right', sortable: true, render: (d) => <span className="font-mono text-xs tabular-nums">{fmt(d.packet_rate)}</span> },
    { key: 'mitigation_status', label: 'Mitigation', render: (d) => <Badge tone={mitTone(d.mitigation_status)}>{mitLabel(d.mitigation_status)}</Badge> },
    { key: 'open', label: '', align: 'right', render: (d) => <Button size="sm" variant="ghost" onClick={() => select(d)} aria-label={`Inspect window ${d.id}`}>Inspect</Button> },
  ]

  if (!loaded) return <PageSkeleton />

  const filtered = pred !== 'all' || sev !== 'all' || q

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="console / detections" title="Detections"
        subtitle="Every scored monitoring window, newest first. Select a row to see the model verdict, risk breakdown and mitigation taken." />
      {error && <ErrorState error={error} title="Backend unreachable" onRetry={refresh} />}
      <Card title="Detection log" action={<span className="font-mono text-[11px] text-dim">{rows.length} of {detections.length} · refreshes every 3s</span>}>
        <div className="mb-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_160px_160px]">
          <SearchField value={q} onChange={setQ} label="Filter detections" placeholder="Filter by window, source, mitigation…" />
          <Select srLabel="Prediction filter" value={pred} onChange={(e) => setPred(e.target.value)} options={[['all', 'All predictions'], ['Attack', 'Attack'], ['Benign', 'Benign']]} />
          <Select srLabel="Severity filter" value={sev} onChange={(e) => setSev(e.target.value)} options={[['all', 'All severities'], ...SEVERITIES.map((s) => [s, s])]} />
        </div>
        <Table caption="Scored monitoring windows" columns={columns} rows={rows} rowKey={(d) => d.id} initialSort={{ key: 'id', dir: 'desc' }} pageSize={15}
          empty={detections.length === 0 ? (
            <EmptyState icon={ListTree} title="No detections recorded yet"
              body="Windows appear here as soon as a monitoring session scores them."
              action={<Button icon={Activity} loading={busy === 'sim'} disabled={status?.monitoring || !!error} onClick={() => startSim(5)}>Start simulation</Button>} />
          ) : (
            <EmptyState icon={ListTree} title="No windows match these filters" body="Loosen the prediction or severity filter."
              action={filtered ? <Button variant="secondary" onClick={() => { setQ(''); setPred('all'); setSev('all') }}>Clear filters</Button> : null} />
          )}
          cards={(d) => (
            <button type="button" onClick={() => select(d)} className="panel w-full space-y-2 p-3 text-left">
              <div className="flex items-center justify-between gap-2"><Prediction p={d.prediction} /><Severity s={d.severity} /></div>
              <div className="flex justify-between font-mono text-[11px] text-muted"><span>#{d.id} · {clock(d.timestamp)}</span><span>{pct(d.confidence)}</span></div>
              <div className="flex justify-between font-mono text-[11px] text-dim"><span>{fmt(d.packet_rate)} pkt/s · {d.source_count} src</span><span>{mitLabel(d.mitigation_status)}</span></div>
            </button>
          )} />
      </Card>
      <Drawer open={!!openId} onClose={() => select(null)} title={selected ? `Threat detail · window #${selected.id}` : 'Threat detail'} width="w-[min(560px,100vw)]">
        {selected ? <ThreatDetail d={selected} /> : (
          <EmptyState icon={ListTree} title="That window is no longer in the recent log" body="The console keeps the latest 100 windows. Pick another row." />
        )}
      </Drawer>
    </div>
  )
}
