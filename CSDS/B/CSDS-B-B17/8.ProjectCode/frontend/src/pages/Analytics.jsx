import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Flag, Trophy } from 'lucide-react'
import api, { errorText, fmtTime } from '../api.js'
import { HBars, TrendChart } from '../components/charts.jsx'
import { EMOTION_COLOR, Empty, ErrorBox, ScorePill, SentimentValue, Spinner, Stat } from '../components/ui.jsx'

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
    const t = setInterval(load, 15000) // near real-time: refresh while calls are being analysed
    return () => clearInterval(t)
  }, [load])

  if (error && !data) return <ErrorBox error={error} onRetry={load} />
  if (!data) return <Spinner />
  const t = data.totals
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Analytics</h1>
          <p className="text-sm text-slate-500">Refreshes every 15 seconds{loading ? ' - updating...' : ''}</p>
        </div>
        <select className="input w-40" value={days} onChange={(e) => setDays(Number(e.target.value))} aria-label="Period">
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>
      <ErrorBox error={error} />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <Stat label="Calls" value={t.calls} sub={`${t.minutes} minutes of audio`} />
        <Stat label="Analysed" value={t.analysed} sub={t.processing ? `${t.processing} in progress` : t.failed ? `${t.failed} failed` : 'all done'} />
        <Stat label="Avg agent score" value={t.avg_score ?? '-'} sub="out of 100" />
        <Stat label="Avg customer sentiment" value={t.avg_sentiment != null ? (t.avg_sentiment > 0 ? '+' : '') + t.avg_sentiment.toFixed(2) : '-'} sub="-1 to +1" />
        <Stat label="Escalations" value={t.escalations} sub="calls with high-severity flags" />
        <Stat label="Coverage" value={t.calls ? `${Math.round((100 * t.analysed) / t.calls)}%` : '-'} sub="of calls analysed" />
      </div>
      {t.calls === 0 ? (
        <Empty>
          No calls in this period. Upload recordings on the <Link className="text-indigo-700 underline" to="/calls">Calls</Link> page
          or load the sample calls.
        </Empty>
      ) : (
        <>
          <div className="grid gap-5 lg:grid-cols-[2fr_1fr]">
            <div className="card">
              <h2 className="h2">Call volume & sentiment trend</h2>
              <TrendChart data={data.trend} />
              <div className="mt-1 flex gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-sm bg-indigo-200" /> calls per day</span>
                <span className="flex items-center gap-1"><span className="inline-block h-0.5 w-4 bg-teal-600" /> avg customer sentiment</span>
              </div>
            </div>
            <div className="card">
              <h2 className="h2">Top intents</h2>
              {data.intents.length ? <HBars rows={data.intents} labelKey="intent" /> : <Empty>No analysed calls yet</Empty>}
            </div>
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            <div className="card lg:col-span-2">
              <h2 className="h2 flex items-center gap-2"><Trophy className="h-4 w-4" /> Agent leaderboard</h2>
              {data.leaderboard.length ? (
                <table className="w-full text-sm">
                  <thead className="text-left text-xs uppercase text-slate-500">
                    <tr>
                      <th className="py-1">#</th>
                      <th>Agent</th>
                      <th>Calls</th>
                      <th>Avg score</th>
                      <th>Avg sentiment change</th>
                      <th>Flags</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.leaderboard.map((r, i) => (
                      <tr key={r.agent_id} className="border-t border-slate-100">
                        <td className="py-2 font-semibold text-slate-400">{i + 1}</td>
                        <td className="font-medium">{r.agent}</td>
                        <td>{r.calls}</td>
                        <td><ScorePill score={r.avg_score} /></td>
                        <td><SentimentValue value={r.avg_sentiment_change} /></td>
                        <td>{r.flags}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <Empty>No analysed calls assigned to agents yet</Empty>
              )}
            </div>
            <div className="space-y-5">
              <div className="card">
                <h2 className="h2">Topics</h2>
                <HBars rows={data.topics} labelKey="topic" color="#0d9488" />
              </div>
              <div className="card">
                <h2 className="h2">Customer emotions (turns)</h2>
                <div className="space-y-1.5">
                  {data.emotions.map((e) => (
                    <div key={e.emotion} className="flex items-center gap-2 text-sm">
                      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: EMOTION_COLOR[e.emotion] }} />
                      <span className="flex-1">{e.emotion}</span>
                      <span className="text-slate-500">{e.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="card">
            <h2 className="h2 flex items-center gap-2"><Flag className="h-4 w-4 text-red-600" /> Recent escalations</h2>
            {data.recent_escalations.length ? (
              <ul className="space-y-1.5 text-sm">
                {data.recent_escalations.map((e, i) => (
                  <li key={i} className="flex flex-wrap gap-2">
                    <Link to={`/calls/${e.call_id}`} className="font-medium text-indigo-700 hover:underline">
                      {e.title.replace('[Sample] ', '')}
                    </Link>
                    <span className="text-slate-500">{e.agent} at {fmtTime(e.t)}</span>
                    <span>{e.text}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>No escalations in this period</Empty>
            )}
          </div>
        </>
      )}
    </div>
  )
}
