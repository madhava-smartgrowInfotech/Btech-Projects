import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, Clock, Loader2, Sparkles, XCircle } from 'lucide-react'
import api, { errMsg } from '../api'
import { Badge, Bar, DiffBadge, Empty, ErrorBox, Loadable, PageHeader, fmtDate, useAction, useFetch } from '../components/ui'

export default function Practice() {
  const [kind, setKind] = useState('aptitude')
  const [test, setTest] = useState(null)
  const [result, setResult] = useState(null)
  const history = useFetch('/practice/history')

  const finish = (r) => {
    setTest(null)
    setResult(r)
    history.reload(true)
  }

  if (test) return <Runner test={test} onDone={finish} />
  return (
    <>
      <PageHeader title="Aptitude & technical practice" subtitle="Timed tests with automatic scoring and explanations">
        <div className="grid grid-cols-2 gap-1 bg-slate-200 rounded-lg p-1">
          {[['aptitude', 'Aptitude'], ['technical', 'Technical MCQs']].map(([k, l]) => (
            <button key={k} onClick={() => { setKind(k); setResult(null) }}
              className={`px-3 py-1.5 rounded-md text-sm font-medium ${kind === k ? 'bg-white shadow' : 'text-slate-600'}`}>{l}</button>
          ))}
        </div>
      </PageHeader>
      {result && <Result r={result} onClose={() => setResult(null)} />}
      {!result && <Setup kind={kind} onStart={setTest} />}
      <div className="card p-5 mt-6">
        <div className="text-sm font-semibold text-slate-500 mb-3">Test history</div>
        <Loadable loading={history.loading} error={history.error} onRetry={history.reload}>
          {history.data?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr><th className="th">When</th><th className="th">Type</th><th className="th">Topic</th><th className="th">Difficulty</th><th className="th">Score</th></tr></thead>
                <tbody>
                  {history.data.map((h) => (
                    <tr key={h.id}>
                      <td className="td">{fmtDate(h.at)}</td><td className="td capitalize">{h.kind}</td><td className="td">{h.topic}</td>
                      <td className="td">{h.difficulty}</td><td className="td font-semibold">{h.correct}/{h.total} ({h.score}%)</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <Empty>No tests taken yet</Empty>}
        </Loadable>
      </div>
    </>
  )
}

function Setup({ kind, onStart }) {
  const topics = useFetch(`/practice/topics?kind=${kind}`)
  const [topic, setTopic] = useState('All')
  const [difficulty, setDifficulty] = useState('Any')
  const [count, setCount] = useState(10)
  const { busy, error, run } = useAction()
  useEffect(() => setTopic('All'), [kind])
  const start = () => run(async () => {
    const r = await api.post('/practice/start', { kind, topic, difficulty, count: Number(count) })
    onStart(r.data)
  })
  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <div className="card p-5 lg:col-span-2">
        <div className="text-sm font-semibold text-slate-500 mb-3">Question bank by topic</div>
        <Loadable loading={topics.loading} error={topics.error} onRetry={topics.reload}>
          <div className="grid sm:grid-cols-2 gap-2">
            {topics.data?.map((t) => (
              <button key={t.topic} onClick={() => setTopic(t.topic)}
                className={`text-left p-3 rounded-lg border ${topic === t.topic ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:bg-slate-50'}`}>
                <div className="font-medium text-slate-800">{t.topic}</div>
                <div className="text-xs text-slate-500 mt-1 flex gap-2 flex-wrap">
                  <span>{t.total} questions</span>
                  {Object.entries(t.by_difficulty).map(([d, n]) => <span key={d}>{d}: {n}</span>)}
                </div>
              </button>
            ))}
          </div>
        </Loadable>
      </div>
      <div className="card p-5 space-y-4 h-fit">
        <div>
          <label className="label">Topic</label>
          <select className="input" value={topic} onChange={(e) => setTopic(e.target.value)}>
            <option>All</option>
            {topics.data?.map((t) => <option key={t.topic}>{t.topic}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Difficulty</label>
          <select className="input" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            {['Any', 'Easy', 'Medium', 'Hard'].map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Questions</label>
          <select className="input" value={count} onChange={(e) => setCount(e.target.value)}>
            {[5, 10, 15, 20].map((n) => <option key={n}>{n}</option>)}
          </select>
          <p className="text-xs text-slate-400 mt-1">{kind === 'aptitude' ? '60' : '45'} seconds per question. Level 2/3 need a 10+ question test.</p>
        </div>
        <ErrorBox error={error} />
        <button className="btn-primary w-full" onClick={start} disabled={busy}>
          {busy && <Loader2 className="w-4 h-4 animate-spin" />} Start timed test
        </button>
      </div>
    </div>
  )
}

function Runner({ test, onDone }) {
  const [answers, setAnswers] = useState({})
  const [i, setI] = useState(0)
  const [left, setLeft] = useState(test.time_limit_sec)
  const { busy, error, run } = useAction()
  const submitted = useRef(false)
  const q = test.questions[i]

  const submit = () => {
    if (submitted.current) return
    submitted.current = true
    run(async () => {
      const r = await api.post(`/practice/${test.attempt_id}/submit`, { answers })
      onDone(r.data)
    }).then((r) => { if (r === undefined) submitted.current = false })
  }
  useEffect(() => {
    const t = setInterval(() => setLeft((s) => s - 1), 1000)
    return () => clearInterval(t)
  }, [])
  useEffect(() => {
    if (left <= 0) submit()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [left])

  const mm = String(Math.max(0, Math.floor(left / 60))).padStart(2, '0')
  const ss = String(Math.max(0, left % 60)).padStart(2, '0')
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-slate-500">Question {i + 1} of {test.questions.length}</div>
        <div className={`flex items-center gap-1 font-mono font-bold ${left < 30 ? 'text-rose-600' : 'text-slate-800'}`}>
          <Clock className="w-4 h-4" /> {mm}:{ss}
        </div>
      </div>
      <div className="card p-6">
        <div className="flex gap-2 mb-3"><Badge tone="indigo">{q.topic}</Badge><DiffBadge d={q.difficulty} /></div>
        <p className="text-slate-900 font-medium whitespace-pre-wrap">{q.text}</p>
        <div className="space-y-2 mt-5">
          {q.options.map((o, k) => (
            <label key={k} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer ${answers[q.id] === k ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:bg-slate-50'}`}>
              <input type="radio" name={`q${q.id}`} checked={answers[q.id] === k} onChange={() => setAnswers({ ...answers, [q.id]: k })} />
              <span className="font-semibold text-slate-500">{'ABCD'[k]}</span>
              <span className="text-slate-800">{o}</span>
            </label>
          ))}
        </div>
      </div>
      <div className="flex flex-wrap gap-1 mt-4">
        {test.questions.map((x, k) => (
          <button key={x.id} onClick={() => setI(k)}
            className={`w-8 h-8 rounded text-xs font-semibold ${k === i ? 'bg-indigo-600 text-white' : answers[x.id] !== undefined ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-600'}`}>{k + 1}</button>
        ))}
      </div>
      <ErrorBox error={error} />
      <div className="flex justify-between mt-4">
        <button className="btn-secondary" disabled={i === 0} onClick={() => setI(i - 1)}>Previous</button>
        <div className="flex gap-2">
          {i < test.questions.length - 1 && <button className="btn-secondary" onClick={() => setI(i + 1)}>Next</button>}
          <button className="btn-primary" onClick={submit} disabled={busy}>
            {busy && <Loader2 className="w-4 h-4 animate-spin" />} Submit test ({Object.keys(answers).length}/{test.questions.length} answered)
          </button>
        </div>
      </div>
    </div>
  )
}

function Result({ r, onClose }) {
  const [ai, setAi] = useState({})
  const [aiErr, setAiErr] = useState({})
  const explain = async (id) => {
    setAi({ ...ai, [id]: 'loading' })
    try {
      const x = await api.post(`/practice/explain/${id}`)
      setAi((s) => ({ ...s, [id]: x.data.ai_explanation }))
    } catch (e) {
      setAi((s) => ({ ...s, [id]: null }))
      setAiErr((s) => ({ ...s, [id]: errMsg(e) }))
    }
  }
  return (
    <div className="space-y-4">
      <div className="card p-5 flex flex-wrap items-center gap-6">
        <div>
          <div className="text-sm text-slate-500">Score</div>
          <div className="text-4xl font-extrabold text-indigo-600">{r.score_pct}%</div>
          <div className="text-sm text-slate-500">{r.correct} of {r.total} correct in {Math.floor(r.duration_sec / 60)}m {r.duration_sec % 60}s</div>
          {r.late && <div className="text-xs text-rose-600 mt-1">Submitted after the time limit - answers were not counted.</div>}
          {r.leveled_up && <Badge tone="emerald">Level up! You are now Level {r.level}</Badge>}
        </div>
        <div className="flex-1 min-w-[220px] space-y-2">
          {r.by_topic.map((t) => <Bar key={t.topic} label={t.topic} value={t.correct} max={t.total} right={`${t.correct}/${t.total}`} />)}
        </div>
        <button className="btn-secondary" onClick={onClose}>New test</button>
      </div>
      {r.review.map((q, k) => (
        <div key={q.id} className="card p-5">
          <div className="flex items-start gap-2">
            {q.correct ? <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" /> : <XCircle className="w-5 h-5 text-rose-600 shrink-0" />}
            <div className="flex-1">
              <div className="text-xs text-slate-400">Q{k + 1} - {q.topic}</div>
              <p className="text-slate-900 font-medium whitespace-pre-wrap">{q.text}</p>
              <div className="grid sm:grid-cols-2 gap-2 mt-3">
                {q.options.map((o, j) => (
                  <div key={j} className={`text-sm p-2 rounded border ${j === q.answer ? 'border-emerald-400 bg-emerald-50' : j === q.chosen ? 'border-rose-300 bg-rose-50' : 'border-slate-200'}`}>
                    <b className="text-slate-500">{'ABCD'[j]}.</b> {o}
                  </div>
                ))}
              </div>
              {q.chosen === -1 && <div className="text-xs text-slate-500 mt-2">Not answered</div>}
              <div className="text-sm text-slate-600 mt-3 bg-slate-50 rounded p-3">{q.explanation}</div>
              {(q.ai_explanation || (ai[q.id] && ai[q.id] !== 'loading')) && (
                <div className="text-sm text-indigo-900 mt-2 bg-indigo-50 rounded p-3 whitespace-pre-wrap">
                  <Sparkles className="w-4 h-4 inline mr-1" />{q.ai_explanation || ai[q.id]}
                </div>
              )}
              {!q.ai_explanation && !(ai[q.id] && ai[q.id] !== 'loading') && (
                <button className="btn-secondary !py-1 text-xs mt-2" onClick={() => explain(q.id)} disabled={ai[q.id] === 'loading'}>
                  {ai[q.id] === 'loading' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />} Explain step by step (AI)
                </button>
              )}
              {aiErr[q.id] && <div className="mt-2"><ErrorBox error={aiErr[q.id]} /></div>}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
