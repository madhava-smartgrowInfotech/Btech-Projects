import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CalendarClock, PlusSquare, RotateCcw } from 'lucide-react'
import { Badge, Button, EmptyState, ErrorState, PageHeader, SearchField, Select, SkeletonBlock, StatusBadge, Table } from '../components/ui'
import { PageTransition } from '../components/motion'
import { useApi } from '../lib/useApi'

export default function Sessions() {
  const nav = useNavigate()
  const { data, error, loading, reload } = useApi('/api/sessions')
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('all')

  const rows = useMemo(() => {
    const term = q.trim().toLowerCase()
    return (data || []).filter(
      (s) =>
        (status === 'all' || s.status === status) &&
        (!term || `${s.course_code} ${s.course_name} ${s.section} ${s.allowed_rolls}`.toLowerCase().includes(term)),
    )
  }, [data, q, status])

  const columns = [
    { key: 'status', label: 'Status', render: (s) => <StatusBadge status={s.status} /> },
    {
      key: 'course_code',
      label: 'Course',
      render: (s) => (
        <span>
          <strong>{s.course_code}</strong>
          <br />
          <span className="small muted">{s.course_name}</span>
        </span>
      ),
    },
    { key: 'section', label: 'Section' },
    { key: 'starts_at', label: 'Starts', render: (s) => <span className="mono small">{s.starts_local}</span> },
    { key: 'ends_at', label: 'Ends', render: (s) => <span className="mono small">{s.ends_local}</span> },
    { key: 'present', label: 'Present', numeric: true, render: (s) => (s.expected ? `${s.present}/${s.expected}` : s.present) },
    { key: 'blocked', label: 'Blocked', numeric: true, render: (s) => (s.blocked ? <Badge tone="blocked">{s.blocked}</Badge> : 0) },
    { key: 'radius_m', label: 'Radius', numeric: true, render: (s) => `${Math.round(s.radius_m)} m` },
  ]

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Sessions & records"
        title="Sessions"
        description="Every attendance session you created. Open one for its records, map, verification log and Excel export."
        actions={
          <>
            <Button icon={RotateCcw} onClick={() => reload()}>
              Refresh
            </Button>
            <Button variant="primary" to="/app/sessions/new" icon={PlusSquare}>
              New session
            </Button>
          </>
        }
      />
      {loading && !data ? (
        <SkeletonBlock rows={6} label="Loading sessions" />
      ) : error && !data ? (
        <ErrorState title="Couldn't load sessions" error={error} onRetry={reload} />
      ) : !data.length ? (
        <EmptyState
          icon={CalendarClock}
          title="No sessions yet"
          action={
            <Button variant="primary" to="/app/sessions/new" icon={PlusSquare}>
              Create a session
            </Button>
          }
        >
          No sessions yet. Create one to get a shareable link and QR code.
        </EmptyState>
      ) : (
        <div className="stack">
          <div className="row" style={{ alignItems: 'flex-end' }}>
            <SearchField value={q} onChange={setQ} label="Search sessions" placeholder="Search course, section, roll pattern…" />
            <div style={{ width: 200 }}>
              <Select
                label="Status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                options={[
                  { value: 'all', label: 'All statuses' },
                  { value: 'live', label: 'Live' },
                  { value: 'upcoming', label: 'Upcoming' },
                  { value: 'expired', label: 'Expired' },
                  { value: 'closed', label: 'Closed' },
                ]}
              />
            </div>
          </div>
          <Table
            caption="Your attendance sessions"
            columns={columns}
            rows={rows}
            onRowClick={(s) => nav(`/app/sessions/${s.id}`)}
            empty={
              <EmptyState
                title="No matching sessions"
                action={
                  <Button
                    onClick={() => {
                      setQ('')
                      setStatus('all')
                    }}
                  >
                    Clear filters
                  </Button>
                }
              >
                Nothing matches “{q}” {status !== 'all' ? `with status ${status}` : ''}.
              </EmptyState>
            }
          />
        </div>
      )}
    </PageTransition>
  )
}
