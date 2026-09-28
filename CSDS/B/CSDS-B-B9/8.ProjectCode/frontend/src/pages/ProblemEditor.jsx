import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Loader2, Play, Send } from 'lucide-react'
import api from '../api'
import CodeEditor from '../components/CodeEditor'
import { Badge, DiffBadge, Empty, ErrorBox, Loadable, Verdict, fmtDate, useAction, useFetch } from '../components/ui'

function Statement({ text }) {
  // statements use **bold** labels and blank-line paragraphs
  return (
    <div className="prose-statement text-sm text-slate-700">
      {text.split(/\n\s*\n/).map((para, i) => (
        <p key={i} className="whitespace-pre-line">
          {para.split(/(\*\*[^*]+\*\*)/).map((part, j) => part.startsWith('**') ? <b key={j}>{part.slice(2, -2)}</b> : <span key={j}>{part}</span>)}
        </p>
      ))}
    </div>
  )
}

export default function ProblemEditor() {
  const { slug } = useParams()
  const [params] = useSearchParams()
  const contestId = params.get('contest')
  const prob = useFetch(`/problems/${slug}`)
  const langs = useFetch('/languages')
  const subs = useFetch(`/submissions?slug=${slug}`)
  const [lang, setLang] = useState(() => localStorage.getItem('tt_lang') || 'python')
  const [code, setCode] = useState('')
  const [result, setResult] = useState(null)
  const [tab, setTab] = useState('result')
  const { busy, error, run } = useAction()
  const [mode, setMode] = useState('')
  const key = `tt_code_${slug}_${lang}`

  useEffect(() => {
    if (!langs.data) return
    let saved = null
    try { saved = localStorage.getItem(key) } catch { /* storage unavailable */ }
    setCode(saved ?? langs.data.find((l) => l.id === lang)?.template ?? '')
  }, [key, langs.data, lang])

  const change = (v) => {
    setCode(v)
    try { localStorage.setItem(key, v) } catch { /* storage unavailable */ }
  }
  const pickLang = (l) => {
    setLang(l)
    try { localStorage.setItem('tt_lang', l) } catch { /* storage unavailable */ }
  }
  const go = (kind) => {
    setMode(kind)
    setTab('result')
    run(async () => {
      const body = { language: lang, code, contest_id: contestId ? Number(contestId) : null }
      const r = await api.post(`/problems/${slug}/${kind}`, body)
      setResult({ ...r.data, kind })
      if (kind === 'submit') subs.reload(true)
    })
  }

  return (
    <Loadable loading={prob.loading || langs.loading} error={prob.error || langs.error} onRetry={() => { prob.reload(); langs.reload() }}>
      {prob.data && (
        <div className="grid lg:grid-cols-2 gap-4 lg:h-[calc(100vh-7.5rem)]">
          <div className="card p-5 overflow-y-auto">
            <Link to={contestId ? `/contests/${contestId}` : '/problems'} className="text-sm text-indigo-600 flex items-center gap-1 mb-3">
              <ArrowLeft className="w-4 h-4" /> {contestId ? 'Back to contest' : 'All problems'}
            </Link>
            <h1 className="text-xl font-bold text-slate-900">{prob.data.id}. {prob.data.title}</h1>
            <div className="flex gap-2 mt-2 mb-4">
              <DiffBadge d={prob.data.difficulty} /><Badge>{prob.data.topic}</Badge>
              <Badge tone="sky">{prob.data.hidden_tests} hidden tests</Badge>
              {contestId && <Badge tone="amber">Contest submission</Badge>}
            </div>
            <Statement text={prob.data.statement} />
            {prob.data.samples.map((s, i) => (
              <div key={i} className="grid grid-cols-2 gap-2 mt-4">
                <div><div className="label">Sample input {i + 1}</div><pre className="bg-slate-100 rounded p-2 text-xs overflow-x-auto">{s.input}</pre></div>
                <div><div className="label">Sample output {i + 1}</div><pre className="bg-slate-100 rounded p-2 text-xs overflow-x-auto">{s.output}</pre></div>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-3 min-h-[600px]">
            <div className="flex flex-wrap items-center gap-2">
              <select className="input !w-auto" value={lang} onChange={(e) => pickLang(e.target.value)}>
                {langs.data?.map((l) => <option key={l.id} value={l.id} disabled={!l.available}>{l.name}{l.available ? '' : ' (not installed)'}</option>)}
              </select>
              <button className="btn-secondary !py-1.5 text-xs" onClick={() => change(langs.data.find((l) => l.id === lang)?.template || '')}>Reset</button>
              <div className="ml-auto flex gap-2">
                <button className="btn-secondary" onClick={() => go('run')} disabled={busy}>
                  {busy && mode === 'run' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run samples
                </button>
                <button className="btn-success" onClick={() => go('submit')} disabled={busy}>
                  {busy && mode === 'submit' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Submit
                </button>
              </div>
            </div>
            <div className="flex-1 rounded-xl overflow-hidden border border-slate-300 min-h-[320px]">
              <CodeEditor language={lang} value={code} onChange={change} />
            </div>
            <div className="card p-4 h-64 overflow-y-auto">
              <div className="flex gap-3 border-b border-slate-200 mb-3 text-sm">
                {[['result', 'Result'], ['subs', 'My submissions']].map(([k, l]) => (
                  <button key={k} onClick={() => setTab(k)} className={`pb-2 ${tab === k ? 'border-b-2 border-indigo-600 text-indigo-700 font-medium' : 'text-slate-500'}`}>{l}</button>
                ))}
              </div>
              {tab === 'result' && (
                <>
                  <ErrorBox error={error} />
                  {busy && <div className="text-sm text-slate-500 flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Judging{lang === 'cpp' ? ' (compiling C++ takes a few seconds)' : ''}...</div>}
                  {!busy && !result && !error && <Empty>Run your code on the samples, then submit to be judged on hidden tests.</Empty>}
                  {!busy && result && <ResultView r={result} />}
                </>
              )}
              {tab === 'subs' && (
                <Loadable loading={subs.loading} error={subs.error} onRetry={subs.reload}>
                  {subs.data?.length ? (
                    <table className="w-full">
                      <tbody>
                        {subs.data.map((s) => (
                          <tr key={s.id}>
                            <td className="td">{fmtDate(s.at)}</td><td className="td">{s.language}</td>
                            <td className="td"><Verdict v={s.verdict} /></td><td className="td">{s.passed}/{s.total}</td><td className="td">{s.time_ms} ms</td>
                            <td className="td">{s.contest_id ? <Badge tone="amber">contest</Badge> : null}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : <Empty>No submissions yet</Empty>}
                </Loadable>
              )}
            </div>
          </div>
        </div>
      )}
    </Loadable>
  )
}

function ResultView({ r }) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <Verdict v={r.verdict} />
        <span className="text-sm text-slate-600">{r.kind === 'run' ? 'Samples' : 'Tests'} passed: <b>{r.passed}/{r.total}</b></span>
        <span className="text-sm text-slate-600">Max time: <b>{r.time_ms} ms</b> (limit {r.time_limit_ms} ms)</span>
        {r.leveled_up && <Badge tone="emerald">Level up! Now Level {r.level}</Badge>}
      </div>
      {r.message && <pre className="text-xs bg-rose-50 text-rose-800 rounded p-2 whitespace-pre-wrap">{r.message}</pre>}
      {r.kind === 'run' && r.tests.map((t) => (
        <div key={t.test} className="border border-slate-200 rounded p-2 text-xs">
          <div className="flex gap-2 items-center mb-1"><b>Sample {t.test}</b><Verdict v={t.status} /><span>{t.time_ms} ms</span></div>
          <div className="grid grid-cols-3 gap-2">
            <div><div className="text-slate-400">Input</div><pre className="bg-slate-50 p-1 overflow-x-auto">{t.input}</pre></div>
            <div><div className="text-slate-400">Expected</div><pre className="bg-slate-50 p-1 overflow-x-auto">{t.expected}</pre></div>
            <div><div className="text-slate-400">Your output</div><pre className="bg-slate-50 p-1 overflow-x-auto">{t.output}</pre></div>
          </div>
          {t.stderr && <pre className="text-rose-700 mt-1 whitespace-pre-wrap">{t.stderr}</pre>}
        </div>
      ))}
      {r.kind === 'submit' && (
        <div className="flex flex-wrap gap-1">
          {r.tests.map((t) => (
            <span key={t.test} title={`${t.status} - ${t.time_ms} ms`}
              className={`text-xs px-2 py-1 rounded ${t.status === 'Accepted' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>#{t.test}</span>
          ))}
        </div>
      )}
    </div>
  )
}
