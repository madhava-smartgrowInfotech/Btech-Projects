import { useCallback, useEffect, useMemo, useState } from 'react'
import { CheckCircle2, RefreshCw, Target, XCircle } from 'lucide-react'
import api, { errorText } from '../api'
import CameraView from '../components/CameraView.jsx'
import { ErrorBox, Spinner } from '../components/ui.jsx'
import useSignRecognizer from '../hooks/useSignRecognizer.js'

export default function Practice() {
  const [vocab, setVocab] = useState(null)
  const [error, setError] = useState('')
  const [mode, setMode] = useState('words')
  const [target, setTarget] = useState('HELLO')
  const [attempts, setAttempts] = useState([]) // {target, got, ok, confidence}
  const [flash, setFlash] = useState(null)

  const load = () => { setError(''); api.get('/vocab').then((r) => setVocab(r.data)).catch((e) => setError(errorText(e))) }
  useEffect(load, [])

  const options = useMemo(() => {
    if (!vocab) return []
    return mode === 'words' ? vocab.words.map((w) => ({ value: w.gloss, label: `${w.gloss.replaceAll('_', ' ')} (${w.category})` }))
      : vocab.letters.map((l) => ({ value: l, label: l }))
  }, [vocab, mode])

  useEffect(() => { if (options.length && !options.find((o) => o.value === target)) setTarget(options[0].value) }, [options, target])

  const onEvent = useCallback((ev) => {
    let got = null, confidence = 0
    if (mode === 'words' && ev.type === 'sign' && !ev.fingerspelled) { got = ev.gloss; confidence = ev.confidence }
    if (mode === 'words' && ev.type === 'rejected') { got = '(unclear)'; confidence = ev.top[0].confidence }
    if (mode === 'letters' && ev.type === 'letter') { got = ev.letter; confidence = ev.confidence }
    if (!got) return
    const ok = got === target
    setAttempts((a) => [{ target, got, ok, confidence, at: Date.now() }, ...a].slice(0, 50))
    setFlash(ok ? 'ok' : 'bad')
    setTimeout(() => setFlash(null), 1200)
  }, [mode, target])

  const rec = useSignRecognizer({ mode, onEvent })
  const mine = attempts.filter((a) => a.target === target)
  const score = attempts.length ? Math.round((attempts.filter((a) => a.ok).length / attempts.length) * 100) : null

  const random = () => { if (options.length) setTarget(options[Math.floor(Math.random() * options.length)].value) }

  if (!vocab && !error) return <Spinner label="Loading vocabulary..." />
  return (
    <div className="grid lg:grid-cols-[1.2fr_1fr] gap-6">
      <section className="space-y-3">
        <h2 className="font-semibold text-lg">Practice</h2>
        <CameraView rec={rec} mode={mode} setMode={(m) => { setMode(m); setAttempts([]) }} />
      </section>
      <section className="space-y-4">
        <ErrorBox error={error} onRetry={load} />
        <div className={`card p-5 transition ${flash === 'ok' ? 'ring-4 ring-emerald-300' : flash === 'bad' ? 'ring-4 ring-rose-200' : ''}`}>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500"><Target size={14} /> Sign this</div>
          <div className="text-4xl font-bold text-slate-900 my-3">{target.replaceAll('_', ' ')}</div>
          <div className="flex gap-2">
            <select className="input" value={target} onChange={(e) => setTarget(e.target.value)}>
              {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <button className="btn-secondary" onClick={random} title="Random sign"><RefreshCw size={16} /></button>
          </div>
          <p className="text-xs text-slate-500 mt-3">
            {mode === 'words' ? 'Raise your hands, make the sign, then lower your hands. SignBridge checks what it recognised.'
              : 'Hold the letter shape steady for about a second.'}
          </p>
          {mine[0] && (
            <div className={`mt-4 flex items-center gap-2 rounded-xl px-3 py-2 text-sm ${mine[0].ok ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
              {mine[0].ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
              {mine[0].ok ? 'Correct!' : <>Recognised as <b>{mine[0].got.replaceAll('_', ' ')}</b></>} · {Math.round(mine[0].confidence * 100)}% confidence
            </div>
          )}
        </div>
        <div className="card p-5">
          <div className="flex justify-between items-center">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">This session</div>
            {attempts.length > 0 && <button className="text-xs text-slate-500" onClick={() => setAttempts([])}>Reset</button>}
          </div>
          <div className="text-3xl font-semibold mt-2">{score === null ? '-' : `${score}%`}</div>
          <div className="text-xs text-slate-500">{attempts.filter((a) => a.ok).length} correct of {attempts.length} attempts</div>
          <ul className="mt-3 space-y-1 max-h-60 overflow-y-auto text-sm">
            {attempts.map((a) => (
              <li key={a.at} className="flex items-center gap-2">
                {a.ok ? <CheckCircle2 size={14} className="text-emerald-500" /> : <XCircle size={14} className="text-rose-500" />}
                <span className="font-medium">{a.target.replaceAll('_', ' ')}</span>
                <span className="text-slate-400">→ {a.got.replaceAll('_', ' ')} ({Math.round(a.confidence * 100)}%)</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  )
}
