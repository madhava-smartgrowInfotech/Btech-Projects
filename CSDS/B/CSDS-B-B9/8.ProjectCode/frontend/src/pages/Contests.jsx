import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Award, Loader2, Plus } from 'lucide-react'
import api from '../api'
import { useAuth } from '../App'
import { Badge, Empty, ErrorBox, Loadable, PageHeader, SampleTag, fmtDate, useAction, useFetch } from '../components/ui'

const STATUS_TONE = { running: 'emerald', upcoming: 'sky', ended: 'slate' }

export default function Contests() {
  const { user } = useAuth()
  const contests = useFetch('/contests')
  const board = useFetch('/leaderboard')
  useEffect(() => {
    const t = setInterval(() => board.reload(true), 10000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  return (
    <>
      <PageHeader title="Contests & leaderboard" subtitle="Scheduled coding contests with live standings and ratings" />
      {user.role === 'career' && <CreateContest onCreated={() => contests.reload(true)} />}
      <div className="grid lg:grid-cols-5 gap-4">
        <div className="lg:col-span-2 space-y-3">
          <Loadable loading={contests.loading} error={contests.error} onRetry={contests.reload}>
            {contests.data?.map((c) => (
              <Link key={c.id} to={`/contests/${c.id}`} className="card p-4 block hover:border-indigo-300">
                <div className="flex justify-between items-start gap-2">
                  <div className="font-semibold text-slate-900">{c.title}</div>
                  <Badge tone={STATUS_TONE[c.status]}>{c.status}</Badge>
                </div>
                <div className="text-xs text-slate-500 mt-1">{fmtDate(c.start_at)} - {fmtDate(c.end_at)}</div>
                <div className="text-xs text-slate-500 mt-1">{c.problem_count} problems - {c.participants} participants {c.rated && '- rated'}</div>
              </Link>
            ))}
            {contests.data?.length === 0 && <Empty>No contests scheduled</Empty>}
          </Loadable>
        </div>
        <div className="lg:col-span-3 card p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-semibold text-slate-500">Practice leaderboard (live)</div>
            <div className="text-xs text-slate-400">Easy 10 / Medium 20 / Hard 30 points per solved problem</div>
          </div>
          <Loadable loading={board.loading} error={board.error} onRetry={board.reload}>
            <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
              <table className="w-full">
                <thead><tr><th className="th">#</th><th className="th">Candidate</th><th className="th">Points</th><th className="th">Solved</th><th className="th">Rating</th><th className="th">Level</th></tr></thead>
                <tbody>
                  {board.data?.map((r) => (
                    <tr key={r.user_id} className={r.me ? 'bg-indigo-50' : ''}>
                      <td className="td font-semibold">{r.rank}</td>
                      <td className="td">{r.name} {r.me && <Badge tone="indigo">you</Badge>} <SampleTag show={r.is_sample} /> {r.job_ready && <Award className="w-4 h-4 text-emerald-600 inline" />}</td>
                      <td className="td font-semibold">{r.points}</td><td className="td">{r.solved}</td><td className="td">{r.rating}</td><td className="td">L{r.level}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Loadable>
        </div>
      </div>
    </>
  )
}

function CreateContest({ onCreated }) {
  const probs = useFetch('/problems')
  const [open, setOpen] = useState(false)
  const [f, setF] = useState({ title: '', start: '', duration: 120, slugs: [] })
  const { busy, error, run } = useAction()
  const toggle = (s) => setF({ ...f, slugs: f.slugs.includes(s) ? f.slugs.filter((x) => x !== s) : [...f.slugs, s] })
  const save = () => run(async () => {
    if (!f.start) throw new Error('Pick a start time')
    await api.post('/contests', { title: f.title, start_at: new Date(f.start).toISOString(), duration_minutes: Number(f.duration), problem_slugs: f.slugs })
    setOpen(false)
    setF({ title: '', start: '', duration: 120, slugs: [] })
    onCreated()
  })
  if (!open) return <button className="btn-primary mb-4" onClick={() => setOpen(true)}><Plus className="w-4 h-4" /> Schedule a contest</button>
  return (
    <div className="card p-5 mb-4 space-y-3">
      <div className="grid sm:grid-cols-3 gap-3">
        <div><label className="label">Title</label><input className="input" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></div>
        <div><label className="label">Start</label><input type="datetime-local" className="input" value={f.start} onChange={(e) => setF({ ...f, start: e.target.value })} /></div>
        <div><label className="label">Duration (minutes)</label><input type="number" className="input" value={f.duration} onChange={(e) => setF({ ...f, duration: e.target.value })} /></div>
      </div>
      <div>
        <label className="label">Problems ({f.slugs.length} selected)</label>
        <div className="flex flex-wrap gap-1 max-h-40 overflow-y-auto">
          {probs.data?.map((p) => (
            <button key={p.slug} onClick={() => toggle(p.slug)}
              className={`text-xs px-2 py-1 rounded border ${f.slugs.includes(p.slug) ? 'bg-indigo-600 text-white border-indigo-600' : 'border-slate-300'}`}>{p.title}</button>
          ))}
        </div>
      </div>
      <ErrorBox error={error} />
      <div className="flex gap-2">
        <button className="btn-primary" onClick={save} disabled={busy}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Create contest</button>
        <button className="btn-secondary" onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </div>
  )
}
