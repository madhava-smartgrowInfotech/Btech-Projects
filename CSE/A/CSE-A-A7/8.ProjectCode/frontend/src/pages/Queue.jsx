import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, Inbox, PlusSquare, RefreshCw } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, SearchField, SkeletonBlock, Table, Tabs } from '../components/ui'
import { PriorityBlock } from '../components/athena/bits'
import { api } from '../lib/api'
import { fmtPct, PRIORITY_NAME, timeAgo } from '../lib/format'

const POLL_MS = 15000

export default function Queue() {
  const nav = useNavigate()
  const [state, setState] = useState({ loading: true, items: [], error: null })
  const [tab, setTab] = useState('all')
  const [q, setQ] = useState('')
  const [updated, setUpdated] = useState(null)

  const load = useCallback((quiet) => {
    if (!quiet) setState((s) => ({ ...s, loading: true, error: null }))
    return api
      .patients()
      .then((r) => {
        setState({ loading: false, items: r.items, error: null })
        setUpdated(new Date())
      })
      .catch((error) => setState((s) => (quiet && s.items.length ? s : { loading: false, items: [], error })))
  }, [])

  useEffect(() => {
    load(false)
    const t = setInterval(() => load(true), POLL_MS)
    return () => clearInterval(t)
  }, [load])

  const counts = useMemo(() => {
    const c = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
    state.items.forEach((p) => (c[p.priority] += 1))
    return c
  }, [state.items])

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return state.items.filter((p) => (tab === 'all' || String(p.priority) === tab) && (!needle || p.name.toLowerCase().includes(needle) || p.headline.join(' ').toLowerCase().includes(needle)))
  }, [state.items, tab, q])

  const columns = [
    { key: 'priority', label: 'Priority', numeric: true, render: (r) => <PriorityBlock p={r.priority} />, sortValue: (r) => r.priority },
    {
      key: 'name',
      label: 'Patient',
      render: (r) => (
        <div>
          <strong>{r.name}</strong>
          <div className="tiny muted">{r.source === 'sample' ? 'Sample case' : `Age ${r.vitals.age} · ${r.vitals.arrival_mode}`}</div>
        </div>
      ),
    },
    { key: 'headline', label: 'Main drivers', sortable: false, render: (r) => r.headline.join(', ') || '—' },
    { key: 'risk_level', label: 'Risk', render: (r) => <Badge tone={r.risk_level === 'High' ? 'blocked' : r.risk_level === 'Moderate' ? 'upcoming' : 'pass'}>{r.risk_level}</Badge> },
    { key: 'confidence', label: 'Confidence', numeric: true, render: (r) => fmtPct(r.confidence), sortValue: (r) => r.confidence },
    {
      key: 'reviewed',
      label: 'Clinician',
      render: (r) => (r.overridden ? <Badge tone="info">Changed</Badge> : r.reviewed ? <Badge tone="pass"><Check size={12} strokeWidth={3} aria-hidden="true" /> Accepted</Badge> : <span className="muted">Pending</span>),
      sortValue: (r) => (r.overridden ? 2 : r.reviewed ? 1 : 0),
    },
    { key: 'created_at', label: 'Arrived', render: (r) => timeAgo(r.created_at), sortValue: (r) => r.created_at },
  ]

  const tabs = [
    { id: 'all', label: 'All', count: state.items.length },
    ...[1, 2, 3, 4, 5].map((n) => ({ id: String(n), label: `P${n}`, count: counts[n] })),
  ]

  return (
    <>
      <PageHeader
        eyebrow="Live"
        title="Triage queue"
        description="Sickest first. Ties go to whoever arrived earlier. The list refreshes every 15 seconds."
        actions={
          <>
            <Button icon={RefreshCw} onClick={() => load(false)} loading={state.loading && state.items.length > 0}>Refresh</Button>
            <Button variant="primary" icon={PlusSquare} to="/app/new">New patient</Button>
          </>
        }
      />

      {state.loading && !state.items.length ? (
        <SkeletonBlock rows={6} label="Loading the queue" />
      ) : state.error ? (
        <ErrorState title="Could not load the queue" error={state.error} onRetry={() => load(false)} />
      ) : (
        <div className="stack" style={{ '--gap': '20px' }}>
          <div className="queue-stats">
            {[1, 2, 3, 4, 5].map((n) => (
              <div className="queue-tile" key={n}>
                <PriorityBlock p={n} />
                <span className="n">{counts[n]}</span>
                <span className="l">{PRIORITY_NAME[n]}</span>
              </div>
            ))}
          </div>
          <Card flat>
            <div className="row-between" style={{ marginBottom: 16 }}>
              <Tabs tabs={tabs} value={tab} onChange={setTab} label="Filter by priority" />
              <SearchField value={q} onChange={setQ} label="Search patients" placeholder="Search name or driver…" />
            </div>
            <Table
              columns={columns}
              rows={rows}
              pageSize={10}
              caption="Patients ordered by triage priority"
              onRowClick={(r) => nav(`/app/patients/${r.id}`)}
              empty={
                state.items.length === 0 ? (
                  <EmptyState icon={Inbox} title="The queue is empty" action={<Button variant="primary" icon={PlusSquare} to="/app/new">Triage a patient</Button>}>
                    New arrivals appear here, ordered by priority.
                  </EmptyState>
                ) : (
                  <EmptyState icon={Inbox} title="No patients match" action={<Button onClick={() => { setTab('all'); setQ('') }}>Clear filters</Button>}>
                    Try another priority or a different search.
                  </EmptyState>
                )
              }
            />
            {updated && <p className="tiny muted" style={{ marginTop: 12 }}>Updated {updated.toLocaleTimeString()}</p>}
          </Card>
        </div>
      )}
    </>
  )
}
