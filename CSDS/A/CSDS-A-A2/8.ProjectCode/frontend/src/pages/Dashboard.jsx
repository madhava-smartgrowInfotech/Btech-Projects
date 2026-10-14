import { Link } from 'react-router-dom'
import { Activity, ArrowRight, CalendarClock, PlusSquare, ShieldAlert, UserCheck } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, ResultBadge, SkeletonBlock, StatCard, StatusBadge, Timeline } from '../components/ui'
import { BarBlocks, PALETTE, StackedBlocks } from '../components/ui/Charts'
import { CursorHighlight, InkRule, Marquee, PageTransition, Stagger } from '../components/motion'
import { useAuth } from '../lib/auth'
import { useApi } from '../lib/useApi'
import { STAGE_LABEL } from '../lib/format'

export default function Dashboard() {
  const { user } = useAuth()
  const { data, error, loading, reload } = useApi('/api/dashboard', { interval: 15000 })

  const header = (
    <PageHeader
      eyebrow="Faculty dashboard"
      title={`Hi, ${(user?.full_name || 'Faculty').split(' ')[0]}.`}
      description="Live view of every session you have created. Numbers refresh every 15 seconds."
      actions={
        <Button variant="primary" to="/app/sessions/new" icon={PlusSquare}>
          New session
        </Button>
      }
    />
  )

  if (loading && !data) {
    return (
      <>
        {header}
        <SkeletonBlock rows={6} label="Loading dashboard" />
      </>
    )
  }
  if (error && !data) {
    return (
      <>
        {header}
        <ErrorState title="Couldn't load the dashboard" error={error} onRetry={reload} />
      </>
    )
  }

  const { totals, sessions, stages, recent_attempts: recent } = data
  if (!sessions.length) {
    return (
      <PageTransition>
        {header}
        <EmptyState
          icon={CalendarClock}
          title="No sessions yet"
          action={
            <Button variant="primary" to="/app/sessions/new" icon={PlusSquare}>
              Create your first session
            </Button>
          }
        >
          Create a time-bound, geo-fenced session and share its link or QR code with your class. Check-ins appear here live.
        </EmptyState>
      </PageTransition>
    )
  }

  const chrono = [...sessions].reverse() // oldest → newest for sparklines
  const live = sessions.filter((s) => s.status === 'live')
  const blockRate = totals.attempts ? Math.round((totals.blocked / totals.attempts) * 100) : 0
  const ticker = [
    { label: 'Live now', value: totals.live },
    ...live.slice(0, 4).map((s) => ({ label: `${s.course_code} ${s.section}`.trim(), value: `${s.present} present` })),
    { label: 'Check-ins verified', value: totals.present },
    { label: 'Checks run', value: totals.attempts },
    { label: 'Blocked', value: totals.blocked },
    { label: 'Block rate', value: `${blockRate}%` },
    { label: 'Sessions', value: totals.sessions },
  ]
  const perSession = chrono.slice(-10).map((s) => ({
    name: s.course_code,
    title: `${s.course_code} · ${s.starts_local}`,
    present: s.present,
    status: s.status,
  }))
  const stageData = stages.map((s) => ({ ...s, label: STAGE_LABEL[s.stage] || s.stage }))

  return (
    <PageTransition>
      {header}
      <div style={{ margin: '-8px 0 28px' }}>
        <Marquee items={ticker} label="Live session statistics" />
      </div>

      <Stagger className="grid grid-4" inView={false}>
        <StatCard label="Sessions" value={totals.sessions} icon={CalendarClock} spark={chrono.map((s) => s.attempts)} hint="trend: checks per session" />
        <StatCard label="Live now" value={totals.live} icon={Activity} tone={totals.live ? 'lime' : undefined} hint={live.map((s) => s.course_code).join(', ') || 'none open'} />
        <StatCard label="Check-ins" value={totals.present} icon={UserCheck} spark={chrono.map((s) => s.present)} hint="verified and recorded" />
        <StatCard
          label="Blocked"
          value={totals.blocked}
          icon={ShieldAlert}
          spark={chrono.map((s) => s.blocked)}
          delta={`${blockRate}% of checks`}
          deltaTone={blockRate ? PALETTE.coral : undefined}
        />
      </Stagger>

      <div className="grid grid-2" style={{ marginTop: 28 }}>
        <Card title="Check-ins per session">
          <BarBlocks data={perSession} xKey="name" yKey="present" name="Present" labelKey="title" colorFn={(d) => (d.status === 'live' ? PALETTE.lime : PALETTE.sky)} />
          <div className="legend" style={{ marginTop: 8 }} aria-hidden="true">
            <span>
              <i style={{ background: PALETTE.lime }} />
              Live session
            </span>
            <span>
              <i style={{ background: PALETTE.sky }} />
              Other
            </span>
          </div>
        </Card>
        <Card title="Checks by stage">
          {stageData.length ? (
            <StackedBlocks
              data={stageData}
              xKey="label"
              series={[
                { key: 'passed', name: 'Passed', color: PALETTE.lime },
                { key: 'blocked', name: 'Blocked', color: PALETTE.coral },
              ]}
            />
          ) : (
            <EmptyState title="No checks yet">Attempts appear here as students start checking in.</EmptyState>
          )}
        </Card>
      </div>

      <InkRule style={{ margin: '36px 0 28px' }} />

      <div className="grid grid-2" style={{ alignItems: 'start' }}>
        <section>
          <div className="row-between" style={{ marginBottom: 16 }}>
            <h2 className="display-sm">Recent sessions</h2>
            <Button size="sm" variant="ghost" to="/app/sessions" iconRight={ArrowRight}>
              All sessions
            </Button>
          </div>
          <div className="stack">
            {sessions.slice(0, 4).map((s) => (
              <CursorHighlight key={s.id} as={Link} to={`/app/sessions/${s.id}`} className="card card-interactive" style={{ padding: 18 }}>
                <div className="row-between">
                  <strong className="card-title">
                    {s.course_code} {s.section && <span className="small mono">· {s.section}</span>}
                  </strong>
                  <StatusBadge status={s.status} />
                </div>
                <div className="row small mono" style={{ marginTop: 10 }}>
                  <span>{s.starts_local}</span>
                  <Badge tone="pass">{s.present} present</Badge>
                  {s.blocked > 0 && <Badge tone="blocked">{s.blocked} blocked</Badge>}
                </div>
              </CursorHighlight>
            ))}
          </div>
        </section>
        <Card title="Latest verification attempts">
          {recent.length ? (
            <Timeline
              items={recent.map((a) => ({
                key: a.id,
                tone: a.passed ? 'ok' : 'bad',
                title: (
                  <span className="row" style={{ '--gap': '8px' }}>
                    {a.roll_number} · {STAGE_LABEL[a.stage] || a.stage} <ResultBadge passed={a.passed} />
                  </span>
                ),
                meta: `${a.time} · ${a.course_code}`,
                body: a.reason,
              }))}
            />
          ) : (
            <EmptyState title="No attempts yet">Share a session link — every check, pass or block, is logged here.</EmptyState>
          )}
        </Card>
      </div>
    </PageTransition>
  )
}
