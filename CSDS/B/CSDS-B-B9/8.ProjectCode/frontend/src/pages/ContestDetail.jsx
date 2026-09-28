import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../App'
import { Badge, DiffBadge, Empty, Loadable, PageHeader, SampleTag, useFetch } from '../components/ui'

function useCountdown(target) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  const ms = Math.max(0, new Date(target).getTime() - now)
  const s = Math.floor(ms / 1000)
  const d = Math.floor(s / 86400)
  return `${d ? d + 'd ' : ''}${String(Math.floor((s % 86400) / 3600)).padStart(2, '0')}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

export default function ContestDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const c = useFetch(`/contests/${id}`)
  const board = useFetch(`/contests/${id}/leaderboard`)
  useEffect(() => {
    const t = setInterval(() => board.reload(true), 5000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])
  const ct = c.data
  const countdown = useCountdown(ct ? (ct.status === 'upcoming' ? ct.start_at : ct.end_at) : Date.now())
  return (
    <Loadable loading={c.loading} error={c.error} onRetry={c.reload}>
      {ct && (
        <>
          <Link to="/contests" className="text-sm text-indigo-600 flex items-center gap-1 mb-3"><ArrowLeft className="w-4 h-4" /> All contests</Link>
          <PageHeader title={ct.title} subtitle={`${ct.problem_count} problems - ranked by solved count, then penalty minutes (+5 per wrong attempt)`}>
            <Badge tone={ct.status === 'running' ? 'emerald' : ct.status === 'upcoming' ? 'sky' : 'slate'}>{ct.status}</Badge>
            {ct.status !== 'ended' && <Badge tone="indigo">{ct.status === 'upcoming' ? 'Starts in' : 'Ends in'} {countdown}</Badge>}
            {ct.rated && <Badge tone="amber">rated</Badge>}
          </PageHeader>
          <div className="grid lg:grid-cols-3 gap-4">
            <div className="card p-4 h-fit">
              <div className="text-sm font-semibold text-slate-500 mb-3">Problems</div>
              {ct.status === 'upcoming' && <Empty>Problems are revealed when the contest starts</Empty>}
              <ul className="space-y-2">
                {ct.problems.map((p, i) => (
                  <li key={p.slug} className="flex items-center justify-between gap-2">
                    {ct.status === 'running' && user.role === 'candidate' ? (
                      <Link className="text-indigo-600 font-medium hover:underline" to={`/problems/${p.slug}?contest=${ct.id}`}>{String.fromCharCode(65 + i)}. {p.title}</Link>
                    ) : <span className="font-medium text-slate-700">{String.fromCharCode(65 + i)}. {p.title}</span>}
                    <DiffBadge d={p.difficulty} />
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-4 lg:col-span-2">
              <div className="text-sm font-semibold text-slate-500 mb-3">Standings {ct.status === 'running' && '(updates every 5 seconds)'}</div>
              <Loadable loading={board.loading} error={board.error} onRetry={board.reload}>
                {board.data?.rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr>
                          <th className="th">#</th><th className="th">Candidate</th><th className="th">Solved</th><th className="th">Penalty</th>
                          {ct.problems.map((p, i) => <th key={p.slug} className="th text-center">{String.fromCharCode(65 + i)}</th>)}
                          {ct.rated && <th className="th">Rating</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {board.data.rows.map((r) => (
                          <tr key={r.user_id} className={r.user_id === user.id ? 'bg-indigo-50' : ''}>
                            <td className="td font-semibold">{r.rank}</td>
                            <td className="td">{r.name} <SampleTag show={r.is_sample} /></td>
                            <td className="td font-semibold">{r.solved}</td><td className="td">{r.penalty}</td>
                            {r.problems.map((p) => (
                              <td key={p.slug} className="td text-center text-xs">
                                {p.solved ? <span className="text-emerald-700"><CheckCircle2 className="w-4 h-4 inline" /> {p.minute}'{p.attempts ? ` (+${p.attempts})` : ''}</span>
                                  : p.attempts ? <span className="text-rose-600">-{p.attempts}</span> : ''}
                              </td>
                            ))}
                            {ct.rated && <td className="td">{r.rating} {r.rating_change != null && <span className={r.rating_change >= 0 ? 'text-emerald-600' : 'text-rose-600'}>({r.rating_change >= 0 ? '+' : ''}{r.rating_change})</span>}</td>}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : <Empty>No submissions yet - be the first!</Empty>}
              </Loadable>
            </div>
          </div>
        </>
      )}
    </Loadable>
  )
}
