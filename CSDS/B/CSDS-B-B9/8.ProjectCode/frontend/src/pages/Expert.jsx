import { useState } from 'react'
import { Award, Loader2 } from 'lucide-react'
import api from '../api'
import { Badge, Empty, ErrorBox, Loadable, PageHeader, SampleTag, fmtDate, useAction, useFetch } from '../components/ui'

const RUBRIC = [
  ['technical_depth', 'Technical depth'],
  ['problem_solving', 'Problem solving'],
  ['communication', 'Communication'],
  ['role_knowledge', 'Role knowledge'],
  ['professionalism', 'Professionalism'],
]

export default function Expert() {
  const q = useFetch('/interviews/expert/queue')
  const open = q.data?.filter((x) => x.status !== 'completed') || []
  const done = q.data?.filter((x) => x.status === 'completed') || []
  return (
    <>
      <PageHeader title="Expert interview queue" subtitle="Final-level mock interviews - a 7/10 average passes the candidate to Job-ready" />
      <Loadable loading={q.loading} error={q.error} onRetry={q.reload}>
        {open.length === 0 && <div className="card"><Empty>No pending requests. Candidates can request an expert interview once they reach Level 4.</Empty></div>}
        <div className="space-y-4">
          {open.map((iv) => <Item key={iv.id} iv={iv} onChange={() => q.reload(true)} />)}
        </div>
        {done.length > 0 && (
          <div className="card p-5 mt-6">
            <div className="text-sm font-semibold text-slate-500 mb-3">Completed</div>
            <table className="w-full">
              <tbody>
                {done.map((iv) => (
                  <tr key={iv.id}>
                    <td className="td">{iv.candidate?.name}</td><td className="td">{iv.role}</td><td className="td">{iv.score}/10</td>
                    <td className="td">{iv.report?.passed ? <Badge tone="emerald"><Award className="w-3 h-3" /> passed</Badge> : <Badge tone="rose">not passed</Badge>}</td>
                    <td className="td">{iv.expert}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Loadable>
    </>
  )
}

function Item({ iv, onChange }) {
  const [when, setWhen] = useState('')
  const [scores, setScores] = useState(Object.fromEntries(RUBRIC.map(([k]) => [k, 7])))
  const [notes, setNotes] = useState('')
  const { busy, error, run } = useAction()
  const ev = iv.evidence
  const avg = (Object.values(scores).reduce((a, b) => a + Number(b), 0) / RUBRIC.length).toFixed(1)
  const schedule = () => run(async () => {
    if (!when) throw new Error('Pick a date and time')
    await api.post(`/interviews/expert/${iv.id}/schedule`, { scheduled_at: new Date(when).toISOString() })
    onChange()
  })
  const evaluate = () => run(async () => {
    await api.post(`/interviews/expert/${iv.id}/evaluate`, { scores, notes })
    onChange()
  })
  return (
    <div className="card p-5">
      <div className="flex flex-wrap justify-between gap-2">
        <div>
          <div className="font-semibold text-slate-900">{iv.candidate?.name} <SampleTag show={iv.candidate?.is_sample} /></div>
          <div className="text-sm text-slate-500">{iv.role} - requested {fmtDate(iv.created_at)}</div>
        </div>
        <Badge tone={iv.status === 'scheduled' ? 'sky' : 'amber'}>{iv.status}{iv.scheduled_at ? ` - ${fmtDate(iv.scheduled_at)} UTC` : ''}</Badge>
      </div>
      <div className="flex flex-wrap gap-2 mt-3 text-xs">
        <Badge tone="indigo">Level {ev.level}</Badge><Badge>Readiness {ev.readiness}</Badge><Badge>Aptitude {ev.aptitude_best}%</Badge>
        <Badge>Technical {ev.technical_best}%</Badge><Badge>{ev.solved} solved</Badge><Badge>AI interview {ev.ai_interview}/10</Badge>
        <Badge>ATS {Math.round(ev.ats)}</Badge><Badge>Rating {ev.rating}</Badge>
      </div>
      <div className="grid lg:grid-cols-3 gap-4 mt-4">
        <div className="space-y-2">
          <label className="label">Schedule</label>
          <input type="datetime-local" className="input" value={when} onChange={(e) => setWhen(e.target.value)} />
          <button className="btn-secondary w-full" onClick={schedule} disabled={busy}>Schedule & notify candidate</button>
        </div>
        <div className="lg:col-span-2">
          <label className="label">Rubric (0-10) - average {avg}</label>
          <div className="grid sm:grid-cols-5 gap-2">
            {RUBRIC.map(([k, l]) => (
              <div key={k}>
                <div className="text-xs text-slate-500">{l}</div>
                <input type="number" min={0} max={10} className="input" value={scores[k]} onChange={(e) => setScores({ ...scores, [k]: Number(e.target.value) })} />
              </div>
            ))}
          </div>
          <textarea className="input mt-2 h-20" placeholder="Notes for the candidate" value={notes} onChange={(e) => setNotes(e.target.value)} />
          <button className="btn-primary mt-2" onClick={evaluate} disabled={busy}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Submit evaluation</button>
        </div>
      </div>
      <div className="mt-2"><ErrorBox error={error} /></div>
    </div>
  )
}
