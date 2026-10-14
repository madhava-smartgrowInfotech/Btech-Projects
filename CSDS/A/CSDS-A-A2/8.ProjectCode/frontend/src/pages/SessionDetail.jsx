import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Ban, BarChart3, Download, ListChecks, Map as MapIcon, RotateCcw, ScrollText, ShieldAlert, UserCheck, Users } from 'lucide-react'
import {
  Badge,
  Breadcrumbs,
  Button,
  Card,
  EmptyState,
  ErrorState,
  KeyValueList,
  Modal,
  PageHeader,
  ResultBadge,
  SkeletonBlock,
  StatCard,
  StatusBadge,
  Switch,
  Table,
  Tabs,
  useToast,
} from '../components/ui'
import { BarBlocks, PALETTE, StackedBlocks } from '../components/ui/Charts'
import { PageTransition, Stagger } from '../components/motion'
import { LazyMap } from '../components/LazyMap'
import { SharePanel } from '../components/SharePanel'
import { api, download } from '../lib/api'
import { useApi } from '../lib/useApi'
import { useConfig } from '../lib/config'
import { STAGE_LABEL, fmtNum } from '../lib/format'

const RECORD_COLS = [
  { key: 'Roll Number', label: 'Roll', render: (r) => <strong className="mono">{r['Roll Number']}</strong> },
  { key: 'Student Name', label: 'Name' },
  { key: 'Status', label: 'Status', render: (r) => <Badge tone={r.Status === 'Present' ? 'pass' : 'blocked'}>{r.Status}</Badge> },
  { key: 'Marked At', label: 'Marked at', render: (r) => <span className="mono small">{r['Marked At'] || '—'}</span> },
  { key: 'Distance (m)', label: 'Dist. m', numeric: true },
  { key: 'GPS Accuracy (m)', label: 'GPS ± m', numeric: true, render: (r) => (r['GPS Accuracy (m)'] === '' ? 'manual' : r['GPS Accuracy (m)'] ?? '—') },
  { key: 'Challenge', label: 'Challenge', render: (r) => <span className="mono small">{r.Challenge || '—'}</span> },
  { key: 'Liveness Score', label: 'Liveness', numeric: true },
  { key: 'Identity Similarity', label: 'Identity', numeric: true, render: (r) => (r['Identity Similarity'] === '' ? 'n/a' : r['Identity Similarity'] ?? '—') },
  { key: 'Max Duplicate Similarity', label: 'Max dup.', numeric: true, render: (r) => (r['Max Duplicate Similarity'] === '' ? '—' : r['Max Duplicate Similarity'] ?? '—') },
  { key: 'Device', label: 'Device', render: (r) => <span className="mono small">{r.Device || '—'}</span> },
]

const LOG_COLS = [
  { key: 'created_at', label: 'Time', render: (a) => <span className="mono small">{a.time}</span> },
  { key: 'roll_number', label: 'Roll', render: (a) => <span className="mono">{a.roll_number}</span> },
  { key: 'stage', label: 'Stage', render: (a) => STAGE_LABEL[a.stage] || a.stage },
  { key: 'passed', label: 'Result', render: (a) => <ResultBadge passed={a.passed} />, sortValue: (a) => (a.passed ? 1 : 0) },
  { key: 'reason', label: 'Reason', render: (a) => <span className="small">{a.reason}</span> },
  { key: 'device', label: 'Device', render: (a) => <span className="mono small">{a.device}</span> },
]

export default function SessionDetail() {
  const { id } = useParams()
  const toast = useToast()
  const { config } = useConfig()
  const [auto, setAuto] = useState(true)
  const [tab, setTab] = useState('records')
  const [confirmClose, setConfirmClose] = useState(false)
  const [busy, setBusy] = useState('')
  const { data, error, loading, reload, setData } = useApi(`/api/sessions/${id}`, { interval: auto ? 10000 : 0 })

  if (loading && !data) return <SkeletonBlock rows={7} label="Loading session" />
  if (error && !data) {
    return <ErrorState title={error.status === 404 ? 'Session not found' : "Couldn't load this session"} error={error} onRetry={error.status === 404 ? undefined : reload} />
  }

  const { session: s, metrics: m, rows, records, attempts } = data
  const canClose = s.status === 'live' || s.status === 'upcoming'

  const exportXlsx = async () => {
    setBusy('export')
    try {
      const name = await download(`/api/sessions/${s.id}/export`, `attendance_${s.course_code}.xlsx`)
      toast.success(`Exported ${name}`)
    } catch (e) {
      toast.error(`Export failed: ${e.message}`)
    } finally {
      setBusy('')
    }
  }

  const close = async () => {
    setBusy('close')
    try {
      const updated = await api(`/api/sessions/${s.id}/close`, { method: 'POST' })
      setData((d) => ({ ...d, session: { ...d.session, ...updated }, metrics: { ...d.metrics, status: updated.status } }))
      toast.success('Session closed. No more check-ins will be accepted.')
      setConfirmClose(false)
      reload(true)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setBusy('')
    }
  }

  const refresh = async () => {
    await reload()
    toast.info('Records refreshed.')
  }

  const stageCounts = Object.values(
    attempts.reduce((acc, a) => {
      const k = a.stage
      acc[k] = acc[k] || { label: STAGE_LABEL[k] || k, passed: 0, blocked: 0 }
      acc[k][a.passed ? 'passed' : 'blocked'] += 1
      return acc
    }, {}),
  )

  return (
    <PageTransition>
      <PageHeader
        crumbs={<Breadcrumbs items={[{ label: 'Sessions', to: '/app/sessions' }, { label: s.course_code }]} />}
        title={`${s.course_code} · ${s.section || '—'}`}
        description={`${s.course_name} · ${s.starts_local} → ${s.ends_local}`}
        actions={
          <>
            <Switch label="Auto-refresh" checked={auto} onChange={setAuto} />
            <Button icon={RotateCcw} onClick={refresh}>
              Refresh
            </Button>
            <Button variant="primary" icon={Download} onClick={exportXlsx} loading={busy === 'export'}>
              Export to Excel
            </Button>
            {canClose && (
              <Button variant="danger" icon={Ban} onClick={() => setConfirmClose(true)}>
                Close session now
              </Button>
            )}
          </>
        }
      />

      <Stagger className="grid grid-4" inView={false}>
        <StatCard label="Status" value={<StatusBadge status={m.status} />} hint={s.is_closed ? 'closed by faculty' : `window ${s.starts_local.split(', ')[1]}–${s.ends_local.split(', ')[1]}`} />
        <StatCard label="Present" value={m.present} icon={UserCheck} tone={m.present ? 'lime' : undefined} />
        <StatCard label="Expected" value={m.expected ?? '—'} icon={Users} hint={m.expected ? 'explicit roll list' : 'wildcard roll pattern'} />
        <StatCard label="Blocked attempts" value={m.blocked} icon={ShieldAlert} hint={`${m.attempts} checks logged`} deltaTone={PALETTE.coral} />
      </Stagger>

      <div className="grid grid-2" style={{ marginTop: 28, alignItems: 'start' }}>
        <Card title="Share link">
          <SharePanel token={s.token} />
        </Card>
        <Card title="Session details">
          <KeyValueList
            items={[
              { label: 'Course', value: `${s.course_code} – ${s.course_name}` },
              { label: 'Faculty', value: s.faculty_name },
              { label: 'Window', value: `${s.starts_local} → ${s.ends_local}` },
              { label: 'Centre', value: <span className="mono">{`${s.latitude.toFixed(5)}, ${s.longitude.toFixed(5)}`}</span> },
              { label: 'Radius', value: `${Math.round(s.radius_m)} m` },
              { label: 'Allowed', value: <code>{s.allowed_rolls}</code> },
              { label: 'Streamlit link', value: <code className="small">{s.streamlit_link}</code> },
            ]}
          />
        </Card>
      </div>

      <div style={{ marginTop: 32 }}>
        <Tabs
          label="Session data"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: 'records', label: 'Attendance records', icon: ListChecks, count: rows.length },
            { id: 'map', label: 'Map', icon: MapIcon },
            { id: 'log', label: 'Verification log', icon: ScrollText, count: attempts.length },
            { id: 'charts', label: 'Analytics', icon: BarChart3 },
          ]}
        />
        {tab === 'records' &&
          (rows.length ? (
            <Table caption="Attendance records" columns={RECORD_COLS} rows={rows} rowKey={(r) => r['Roll Number']} pageSize={15} />
          ) : (
            <EmptyState
              icon={UserCheck}
              title="No attendance marked yet"
              action={
                <Button icon={RotateCcw} onClick={refresh}>
                  Refresh
                </Button>
              }
            >
              Share the link or QR code. Records appear here the moment a student passes all checks.
            </EmptyState>
          ))}
        {tab === 'map' && (
          <div className="stack">
            <LazyMap
              tall
              center={{ lat: s.latitude, lon: s.longitude }}
              radius={s.radius_m}
              tolerance={config?.geofence_tolerance_m || 0}
              points={records.map((r) => ({ lat: r.latitude, lon: r.longitude, label: `${r.roll_number} · ${Math.round(r.distance_m)} m` }))}
              label="Geo-fence and check-in positions"
            />
            <div className="legend">
              <span>
                <i style={{ background: PALETTE.coral }} />
                Geo-fence centre
              </span>
              <span>
                <i style={{ background: PALETTE.lime }} />
                Radius {Math.round(s.radius_m)} m
              </span>
              <span>
                <i style={{ background: PALETTE.sky }} />
                Check-ins ({records.length})
              </span>
            </div>
          </div>
        )}
        {tab === 'log' &&
          (attempts.length ? (
            <Table caption="Verification log" columns={LOG_COLS} rows={attempts} pageSize={15} />
          ) : (
            <EmptyState icon={ScrollText} title="No attempts yet">
              Every check — eligibility, location, liveness, face — is logged here with its reason, pass or block.
            </EmptyState>
          ))}
        {tab === 'charts' &&
          (attempts.length ? (
            <div className="grid grid-2">
              <Card title="Checks by stage">
                <StackedBlocks
                  data={stageCounts}
                  xKey="label"
                  series={[
                    { key: 'passed', name: 'Passed', color: PALETTE.lime },
                    { key: 'blocked', name: 'Blocked', color: PALETTE.coral },
                  ]}
                />
              </Card>
              <Card title="Distance from centre (m)">
                {records.length ? (
                  <BarBlocks
                    data={records.map((r) => ({ roll: r.roll_number.slice(-4), title: `${r.roll_number} · ${r.student_name}`, distance: Math.round(r.distance_m) }))}
                    xKey="roll"
                    yKey="distance"
                    name="Distance (m)"
                    labelKey="title"
                    color={PALETTE.sky}
                  />
                ) : (
                  <EmptyState title="No check-ins yet" />
                )}
                {records.length > 0 && (
                  <p className="small mono muted" style={{ marginTop: 8 }}>
                    Mean liveness {fmtNum(records.reduce((a, r) => a + r.liveness_score, 0) / records.length)} · limit {Math.round(s.radius_m)} m
                    {config ? ` + ${config.geofence_tolerance_m} m` : ''}
                  </p>
                )}
              </Card>
            </div>
          ) : (
            <EmptyState icon={BarChart3} title="Nothing to chart yet">
              Charts fill in as students attempt to check in.
            </EmptyState>
          ))}
      </div>

      <Modal
        open={confirmClose}
        onClose={() => setConfirmClose(false)}
        title="Close this session?"
        footer={
          <>
            <Button onClick={() => setConfirmClose(false)} data-autofocus>
              Keep it open
            </Button>
            <Button variant="danger" icon={Ban} onClick={close} loading={busy === 'close'}>
              Close session now
            </Button>
          </>
        }
      >
        <p>
          {s.course_code} stops accepting check-ins immediately. {m.present} student{m.present === 1 ? '' : 's'} already marked stay recorded. This cannot be
          undone.
        </p>
      </Modal>
    </PageTransition>
  )
}
