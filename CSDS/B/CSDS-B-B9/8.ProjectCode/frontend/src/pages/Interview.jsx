import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Loader2, Mic, MicOff, Sparkles, UserCheck } from 'lucide-react'
import api from '../api'
import { Badge, Bar, Empty, ErrorBox, Loadable, PageHeader, fmtDate, useAction, useFetch } from '../components/ui'

const RUBRIC_LABEL = { relevance: 'Relevance', technical_accuracy: 'Technical accuracy', clarity: 'Clarity', structure: 'Structure', depth: 'Depth' }
const Speech = typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : null

export default function Interview() {
  const { id } = useParams()
  const nav = useNavigate()
  const mine = useFetch('/interviews/mine')
  const dash = useFetch('/me/dashboard')
  if (id) return <Session id={id} onDone={() => mine.reload(true)} />
  const level = dash.data?.stats?.level || 1
  const expert = mine.data?.filter((x) => x.kind === 'expert') || []
  return (
    <>
      <PageHeader title="Mock interviews" subtitle="AI interviewer with rubric scoring, then an expert-led final interview for the Job-ready badge" />
      <div className="grid lg:grid-cols-3 gap-4">
        <StartForm onStarted={(iv) => nav(`/interview/${iv.id}`)} />
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500 mb-3"><UserCheck className="w-4 h-4" /> Expert mock interview (Level 5)</div>
          <ExpertCard level={level} expert={expert} onChange={() => { mine.reload(true); dash.reload(true) }} />
        </div>
      </div>
      <div className="card p-5 mt-4">
        <div className="text-sm font-semibold text-slate-500 mb-3">Your interviews</div>
        <Loadable loading={mine.loading} error={mine.error} onRetry={mine.reload}>
          {mine.data?.filter((x) => x.kind === 'ai').length ? (
            <table className="w-full">
              <thead><tr><th className="th">When</th><th className="th">Role</th><th className="th">Status</th><th className="th">Score</th><th className="th"></th></tr></thead>
              <tbody>
                {mine.data.filter((x) => x.kind === 'ai').map((x) => (
                  <tr key={x.id}>
                    <td className="td">{fmtDate(x.created_at)}</td><td className="td">{x.role} ({x.level})</td>
                    <td className="td"><Badge tone={x.status === 'completed' ? 'emerald' : 'amber'}>{x.status.replace('_', ' ')}</Badge></td>
                    <td className="td font-semibold">{x.score != null ? `${x.score}/10` : '-'}</td>
                    <td className="td"><Link className="text-indigo-600" to={`/interview/${x.id}`}>{x.status === 'completed' ? 'View report' : 'Continue'}</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <Empty>No AI interviews yet</Empty>}
        </Loadable>
      </div>
    </>
  )
}

function StartForm({ onStarted }) {
  const [f, setF] = useState({ role: 'Software Engineer', level: 'Entry', count: 5 })
  const { busy, error, run } = useAction()
  const start = () => run(async () => {
    const r = await api.post('/interviews/start', { ...f, count: Number(f.count) })
    onStarted(r.data)
  })
  return (
    <div className="card p-5 space-y-3">
      <div className="text-sm font-semibold text-slate-500">New AI interview</div>
      <div><label className="label">Role</label><input className="input" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })} placeholder="e.g. Python Developer" /></div>
      <div className="grid grid-cols-2 gap-2">
        <div><label className="label">Seniority</label>
          <select className="input" value={f.level} onChange={(e) => setF({ ...f, level: e.target.value })}>{['Entry', 'Mid', 'Senior'].map((x) => <option key={x}>{x}</option>)}</select></div>
        <div><label className="label">Questions</label>
          <select className="input" value={f.count} onChange={(e) => setF({ ...f, count: e.target.value })}>{[3, 4, 5, 6, 8].map((x) => <option key={x}>{x}</option>)}</select></div>
      </div>
      <ErrorBox error={error} />
      <button className="btn-primary w-full" onClick={start} disabled={busy}>
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} {busy ? 'Generating questions...' : 'Start interview'}
      </button>
      <p className="text-xs text-slate-400">Questions are generated for your role and the skills on your resume.</p>
    </div>
  )
}

function ExpertCard({ level, expert, onChange }) {
  const [role, setRole] = useState('Software Engineer')
  const { busy, error, run } = useAction()
  const open = expert.find((x) => ['requested', 'scheduled'].includes(x.status))
  const done = expert.filter((x) => x.status === 'completed')
  const request = () => run(async () => { await api.post('/interviews/expert/request', { role }); onChange() })
  return (
    <div className="space-y-3">
      {done.map((x) => (
        <div key={x.id} className={`p-3 rounded-lg border ${x.report?.passed ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200'}`}>
          <div className="flex justify-between"><b>{x.role}</b><span className="font-semibold">{x.score}/10 {x.report?.passed ? '- passed' : '- not passed'}</span></div>
          {x.report?.notes && <p className="text-sm text-slate-600 mt-1">"{x.report.notes}"</p>}
          <div className="grid sm:grid-cols-5 gap-2 mt-2">
            {Object.entries(x.report?.expert_scores || {}).map(([k, v]) => <Bar key={k} label={k.replace('_', ' ')} value={v} max={10} right={v} />)}
          </div>
        </div>
      ))}
      {open ? (
        <div className="p-3 rounded-lg bg-sky-50 border border-sky-200 text-sm">
          Expert interview for <b>{open.role}</b> is <b>{open.status}</b>
          {open.scheduled_at && <> for {fmtDate(open.scheduled_at)} UTC</>}. An expert interviewer will record your rubric scores.
        </div>
      ) : level >= 4 ? (
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[200px]"><label className="label">Role</label><input className="input" value={role} onChange={(e) => setRole(e.target.value)} /></div>
          <button className="btn-primary" onClick={request} disabled={busy}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Request expert interview</button>
        </div>
      ) : (
        <p className="text-sm text-slate-500">Unlocks at Level 4 - score 6/10+ in an AI interview and 55+ on the resume ATS check. You are Level {level}.</p>
      )}
      <ErrorBox error={error} />
    </div>
  )
}

function Session({ id, onDone }) {
  const iv = useFetch(`/interviews/${id}`)
  const [answers, setAnswers] = useState([])
  const [i, setI] = useState(0)
  const [listening, setListening] = useState(false)
  const rec = useRef(null)
  const { busy, error, run } = useAction()
  useEffect(() => { if (iv.data) setAnswers(iv.data.questions.map((_, k) => iv.data.answers[k] || '')) }, [iv.data])
  useEffect(() => () => rec.current?.stop(), [])

  const toggleMic = () => {
    if (listening) { rec.current?.stop(); return }
    const r = new Speech()
    r.lang = 'en-US'
    r.continuous = true
    r.interimResults = false
    const idx = i
    r.onresult = (e) => {
      const text = Array.from(e.results).slice(e.resultIndex).map((x) => x[0].transcript).join(' ')
      setAnswers((a) => a.map((v, k) => (k === idx ? (v ? v + ' ' : '') + text.trim() : v)))
    }
    r.onend = () => setListening(false)
    r.onerror = () => setListening(false)
    rec.current = r
    r.start()
    setListening(true)
  }
  const submit = () => run(async () => {
    rec.current?.stop()
    const r = await api.post(`/interviews/${id}/submit`, { answers })
    iv.setData(r.data)
    onDone()
  })

  return (
    <Loadable loading={iv.loading} error={iv.error} onRetry={iv.reload}>
      {iv.data && (
        <>
          <Link to="/interview" className="text-sm text-indigo-600">&larr; All interviews</Link>
          <PageHeader title={`${iv.data.role} interview`} subtitle={`${iv.data.level} level - ${iv.data.questions.length} questions`} />
          {iv.data.status === 'completed' ? <Report iv={iv.data} /> : (
            <div className="max-w-3xl">
              <div className="flex gap-1 mb-3">
                {iv.data.questions.map((_, k) => (
                  <button key={k} onClick={() => setI(k)} className={`w-8 h-8 rounded text-xs font-semibold ${k === i ? 'bg-indigo-600 text-white' : answers[k] ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200'}`}>{k + 1}</button>
                ))}
              </div>
              <div className="card p-6">
                <div className="flex gap-2 mb-2"><Badge tone="indigo">{iv.data.questions[i].type}</Badge>{iv.data.questions[i].focus && <Badge>{iv.data.questions[i].focus}</Badge>}</div>
                <p className="text-lg font-medium text-slate-900">{iv.data.questions[i].q}</p>
                <textarea className="input mt-4 h-48" placeholder="Type your answer, or use the microphone to speak it..."
                  value={answers[i] || ''} onChange={(e) => setAnswers(answers.map((v, k) => (k === i ? e.target.value : v)))} />
                <div className="flex flex-wrap justify-between gap-2 mt-3">
                  {Speech ? (
                    <button className={listening ? 'btn bg-rose-600 text-white' : 'btn-secondary'} onClick={toggleMic}>
                      {listening ? <><MicOff className="w-4 h-4" /> Stop recording</> : <><Mic className="w-4 h-4" /> Answer by voice</>}
                    </button>
                  ) : <span className="text-xs text-slate-400">Voice input needs Chrome or Edge.</span>}
                  <div className="flex gap-2">
                    <button className="btn-secondary" disabled={i === 0} onClick={() => setI(i - 1)}>Previous</button>
                    {i < iv.data.questions.length - 1
                      ? <button className="btn-primary" onClick={() => setI(i + 1)}>Next question</button>
                      : <button className="btn-success" onClick={submit} disabled={busy}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} {busy ? 'Scoring answers...' : 'Finish & get feedback'}</button>}
                  </div>
                </div>
                <ErrorBox error={error} />
              </div>
            </div>
          )}
        </>
      )}
    </Loadable>
  )
}

function Report({ iv }) {
  const r = iv.report
  return (
    <div className="space-y-4">
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="text-sm text-slate-500">Overall score</div>
          <div className="text-5xl font-extrabold text-indigo-600">{iv.score}<span className="text-xl text-slate-400">/10</span></div>
          {r.hire_signal && <Badge tone={r.hire_signal.includes('yes') ? 'emerald' : 'amber'}>hire signal: {r.hire_signal.replace('_', ' ')}</Badge>}
          <div className="space-y-2 mt-4">
            {Object.entries(r.rubric_avg || {}).map(([k, v]) => <Bar key={k} label={RUBRIC_LABEL[k]} value={v} max={10} right={v} />)}
          </div>
        </div>
        <div className="card p-5 lg:col-span-2">
          <p className="text-slate-700">{r.summary}</p>
          <div className="grid sm:grid-cols-2 gap-4 mt-4">
            <div><div className="label">Strengths</div><ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">{r.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
            <div><div className="label">Improve next</div><ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">{r.improvements.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
          </div>
        </div>
      </div>
      {iv.questions.map((q, k) => {
        const a = r.answers[k] || {}
        return (
          <div key={k} className="card p-5">
            <div className="flex justify-between gap-2"><p className="font-medium text-slate-900">Q{k + 1}. {q.q}</p><span className="font-bold text-indigo-600 whitespace-nowrap">{a.score}/10</span></div>
            <div className="text-sm text-slate-600 bg-slate-50 rounded p-3 mt-2 whitespace-pre-wrap">{iv.answers[k] || <i>No answer</i>}</div>
            <div className="grid sm:grid-cols-5 gap-2 mt-3">
              {Object.entries(a.scores || {}).map(([c, v]) => <Bar key={c} label={RUBRIC_LABEL[c]} value={v} max={10} right={v} />)}
            </div>
            <p className="text-sm text-slate-700 mt-3"><b>Feedback:</b> {a.feedback}</p>
            {a.model_answer && <p className="text-sm text-slate-600 mt-1"><b>Model answer:</b> {a.model_answer}</p>}
            {a.nlp && (
              <div className="flex flex-wrap gap-2 mt-2 text-xs">
                <Badge tone="sky">NLP relevance {Math.round(a.nlp.relevance * 100)}%</Badge>
                <Badge>{a.nlp.words} words</Badge>
                <Badge>{a.nlp.avg_sentence_words} words/sentence</Badge>
                <Badge tone={a.nlp.fillers > 2 ? 'amber' : 'slate'}>{a.nlp.fillers} filler words</Badge>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
