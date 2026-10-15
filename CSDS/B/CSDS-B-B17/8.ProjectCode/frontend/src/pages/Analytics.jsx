import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, BarChart3, Flag, PhoneCall, ShieldAlert, Smile, Trophy } from 'lucide-react'
import api, { errorText } from '../api'
import { EMOTION_COLOR, fmtTime, signed } from '../lib/format'
import { Alert, Button, Card, EmptyState, ErrorState, PageHeader, Select, SkeletonBlock, StatCard, Table } from '../components/ui'
import { HBarBlocks, TrendBlocks } from '../components/ui/Charts'
import { ScorePill, SentimentValue } from '../components/app/Bits'

export default function Analytics() {
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/analytics', { params: { days } })
      setData(data)
      setError('')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    load()
  }, [load])
  useEffect(() => {
    const t = setInterval(load, 15000) // refresh while calls are being analysed
    return () => clearInterval(t)
  }, [load])

  const picker = (
    <div style={{ minWidth: 180 }}>
      <Select label="Period" value={days} onChange={(e) => setDays(Number(e.target.value))}>
        <option value={7}>Last 7 days</option>
        <option value={30}>Last 30 days</option>
        <option value={90}>Last 90 days</option>
      </Select>
    </div>
  )

  const header = (
    <PageHeader
      eyebrow={loading && data ? 'Updating…' : 'Refreshes every 15 seconds'}
      title="Analytics"
      description="Volumes, intents, sentiment and agent performance across the analysed calls."
      actions={picker}
    />
  )

  if (error && !data) {
    return (
      <>
        {header}
        <ErrorState title="Could not load analytics" error={error} onRetry={load} />
      </>
    )
  }
  if (!data) {
    return (
      <>
        {header}
        <SkeletonBlock rows={6} label="Loading analytics" />
      </>
    )
  }

  const t = data.totals
  const leaderboard = data.leaderboard.map((r, i) => ({ ...r, rank: i + 1, id: r.agent_id }))
  return (
    <>
      {header}
      <div className="stack" style={{ '--gap': '24px' }}>
        {error && <Alert tone="error">{error}</Alert>}
        <div className="stat-row">
          <StatCard label="Calls" value={t.calls} icon={PhoneCall} hint={`${t.minutes} minutes of audio`} />
          <StatCard
            label="Analysed"
            value={t.analysed}
            icon={Activity}
            hint={t.processing ? `${t.processing} in progress` : t.failed ? `${t.failed} failed` : 'all done'}
          />
          <StatCard label="Avg agent score" value={t.avg_score ?? '—'} decimals={1} icon={Trophy} hint="out of 100" />
          <StatCard
            label="Avg customer sentiment"
            value={t.avg_sentiment != null ? signed(t.avg_sentiment) : '—'}
            icon={Smile}
            hint="-1 to +1"
          />
          <StatCard label="Escalations" value={t.escalations} icon={ShieldAlert} tone={t.escalations ? 'coral' : undefined} hint="calls with high-severity flags" />
          <StatCard label="Coverage" value={t.calls ? `${Math.round((100 * t.analysed) / t.calls)}%` : '—'} icon={BarChart3} hint="of calls analysed" />
        </div>

        {t.calls === 0 ? (
          <EmptyState
            icon={BarChart3}
            title="No calls in this period"
            action={
              <Button variant="primary" to="/calls">
                Go to Calls
              </Button>
            }
          >
            Upload recordings or load the sample calls on the Calls page, or pick a longer period.
          </EmptyState>
        ) : (
          <>
            <div className="grid grid-2" style={{ '--gap': '24px' }}>
              <Card title="Call volume and sentiment trend" className="span-all">
                <TrendBlocks data={data.trend} />
              </Card>
              <Card title="Top intents">
                {data.intents.length ? <HBarBlocks rows={data.intents} labelKey="intent" name="Calls" ariaLabel="Top intents" /> : <p className="muted">No analysed calls yet.</p>}
              </Card>
              <Card title="Topics">
                {data.topics.length ? (
                  <HBarBlocks rows={data.topics} labelKey="topic" name="Calls" color="#7cc6ff" ariaLabel="Calls by topic" />
                ) : (
                  <p className="muted">No analysed calls yet.</p>
                )}
              </Card>
              <Card title="Customer emotions (turns)">
                {data.emotions.length ? (
                  <HBarBlocks
                    rows={data.emotions}
                    labelKey="emotion"
                    name="Turns"
                    colorFn={(d) => EMOTION_COLOR[d.emotion] || '#cfc9b8'}
                    ariaLabel="Customer turns by emotion"
                  />
                ) : (
                  <p className="muted">No analysed calls yet.</p>
                )}
              </Card>
              <Card title="Recent escalations" actions={<Flag size={20} aria-hidden="true" />}>
                {data.recent_escalations.length ? (
                  <ul className="flag-list">
                    {data.recent_escalations.map((e, i) => (
                      <li key={i}>
                        <Link to={`/calls/${e.call_id}`} className="call-title">
                          {e.title.replace('[Sample] ', '')}
                        </Link>
                        <span className="small mono muted">
                          {e.agent || 'unassigned'} at {fmtTime(e.t)}
                        </span>
                        <span>{e.text}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No high-severity escalations in this period.</p>
                )}
              </Card>
            </div>

            <Card title="Agent leaderboard" actions={<Trophy size={20} aria-hidden="true" />}>
              {leaderboard.length ? (
                <Table
                  caption="Agent leaderboard"
                  rows={leaderboard}
                  pageSize={10}
                  columns={[
                    { key: 'rank', label: '#', numeric: true },
                    { key: 'agent', label: 'Agent', render: (r) => <strong>{r.agent}</strong> },
                    { key: 'calls', label: 'Calls', numeric: true },
                    { key: 'avg_score', label: 'Avg score', numeric: true, render: (r) => <ScorePill score={r.avg_score} /> },
                    { key: 'avg_sentiment_change', label: 'Sentiment change', numeric: true, render: (r) => <SentimentValue value={r.avg_sentiment_change} /> },
                    { key: 'flags', label: 'Flags', numeric: true },
                  ]}
                />
              ) : (
                <p className="muted">No analysed calls assigned to agents yet.</p>
              )}
            </Card>
          </>
        )}
      </div>
    </>
  )
}
