import { CheckCircle2, Dices, Target, XCircle } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api, { describeError } from '../api'
import CameraView from '../components/CameraView'
import { SlideUp } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button, IconButton, Select } from '../components/ui/controls'
import { Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import useSignRecognizer from '../hooks/useSignRecognizer'
import { label as pretty } from '../format'

export default function Practice() {
  const [params] = useSearchParams()
  const wanted = params.get('target')
  const [vocab, setVocab] = useState(null)
  const [error, setError] = useState(null)
  const [mode, setMode] = useState('words')
  const [target, setTarget] = useState('HELLO')
  const [attempts, setAttempts] = useState([]) // {target, got, ok, confidence, at}
  const [flash, setFlash] = useState(null)

  const load = () => { setError(null); api.get('/vocab').then((r) => setVocab(r.data)).catch((e) => setError(describeError(e))) }
  useEffect(load, [])

  // /app/practice?target=HELLO (from the command palette) preselects a sign or letter
  useEffect(() => {
    if (!vocab || !wanted) return
    if (vocab.letters.includes(wanted)) { setMode('letters'); setTarget(wanted) }
    else if (vocab.words.some((w) => w.gloss === wanted)) { setMode('words'); setTarget(wanted) }
  }, [vocab, wanted])

  const options = useMemo(() => {
    if (!vocab) return []
    return mode === 'words'
      ? vocab.words.map((w) => [w.gloss, `${pretty(w.gloss)} (${w.category})`])
      : vocab.letters.map((l) => [l, l])
  }, [vocab, mode])

  useEffect(() => { if (options.length && !options.find(([v]) => v === target)) setTarget(options[0][0]) }, [options, target])

  const onEvent = useCallback((ev) => {
    let got = null, confidence = 0
    if (mode === 'words' && ev.type === 'sign' && !ev.fingerspelled) { got = ev.gloss; confidence = ev.confidence }
    if (mode === 'words' && ev.type === 'rejected') { got = '(unclear)'; confidence = ev.top?.[0]?.confidence ?? 0 }
    if (mode === 'letters' && ev.type === 'letter') { got = ev.letter; confidence = ev.confidence }
    if (!got) return
    const ok = got === target
    setAttempts((a) => [{ target, got, ok, confidence, at: Date.now() }, ...a].slice(0, 50))
    setFlash(ok ? 'ok' : 'bad')
    setTimeout(() => setFlash(null), 1200)
  }, [mode, target])

  const rec = useSignRecognizer({ mode, onEvent })
  const latest = attempts.find((a) => a.target === target)
  const correct = attempts.filter((a) => a.ok).length
  const score = attempts.length ? Math.round((correct / attempts.length) * 100) : null
  const random = () => { if (options.length) setTarget(options[Math.floor(Math.random() * options.length)][0]) }

  return (
    <>
      <PageHeader eyebrow="practice" title="Practice signs"
        subtitle="Pick a sign or letter, perform it on camera and get instant right / wrong feedback with the model's confidence." />
      <SlideUp>
        <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <section className="min-w-0" aria-label="Camera">
            <CameraView rec={rec} mode={mode} setMode={(m) => { setMode(m); setAttempts([]) }} tabsId="practice-mode" />
          </section>
          <section className="min-w-0 space-y-4" aria-label="Exercise">
            {error && <ErrorState title="Vocabulary" error={error} onRetry={load} />}
            {!vocab && !error && <><Skeleton className="h-56" /><Skeleton className="h-40" /></>}
            {vocab && (
              <>
                <div className={`rounded-[6px] transition-shadow duration-300 ${flash === 'ok' ? 'shadow-[0_0_0_2px_var(--ok)]' : flash === 'bad' ? 'shadow-[0_0_0_2px_var(--alert)]' : ''}`}>
                  <Card title="sign this" bodyClass="p-5">
                    <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.16em] text-dim"><Target size={13} aria-hidden="true" /> target</div>
                    <div className="my-3 break-words font-mono text-4xl font-semibold tracking-tight text-ok" aria-live="polite">{pretty(target)}</div>
                    <div className="flex items-end gap-2">
                      <Select label="Choose a sign" className="min-w-0 flex-1" value={target} onChange={(e) => setTarget(e.target.value)} options={options} />
                      <IconButton icon={Dices} label="Random sign" variant="secondary" onClick={random} />
                    </div>
                    <p className="mt-3 text-xs text-muted">
                      {mode === 'words'
                        ? 'Raise your hands, make the sign, then lower your hands. SignBridge checks what it recognised.'
                        : 'Hold the letter shape steady for about a second.'}
                    </p>
                    {latest && (
                      <div role="status" className={`mt-4 flex items-center gap-2 rounded-[6px] border px-3 py-2 text-sm ${latest.ok ? 'border-ok/40 bg-ok/10 text-ok' : 'border-alert/40 bg-alert/10 text-alert'}`}>
                        {latest.ok ? <CheckCircle2 size={16} aria-hidden="true" /> : <XCircle size={16} aria-hidden="true" />}
                        {latest.ok ? 'Correct!' : <>Recognised as <b className="font-mono">{pretty(latest.got)}</b></>} · {Math.round(latest.confidence * 100)}% confidence
                      </div>
                    )}
                  </Card>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <StatCard label="Score" value={score ?? '-'} format={(v) => `${Math.round(v)}%`} tone="ok" />
                  <StatCard label="Correct" value={correct} tone="ok" />
                  <StatCard label="Attempts" value={attempts.length} tone="cyan" />
                </div>

                <Card title="this session" action={attempts.length > 0 ? <Button size="sm" variant="ghost" onClick={() => setAttempts([])}>Reset</Button> : null} bodyClass="p-4">
                  {attempts.length === 0 ? (
                    <EmptyState icon={Target} title="No attempts yet" body="Start the camera and perform the target sign. Each recognised attempt is scored here."
                      />
                  ) : (
                    <ul className="max-h-60 space-y-1 overflow-y-auto font-mono text-xs">
                      {attempts.map((a) => (
                        <li key={a.at} className="flex items-center gap-2 border-b border-dashed border-line py-1.5 last:border-0">
                          {a.ok ? <CheckCircle2 size={14} className="shrink-0 text-ok" aria-label="correct" /> : <XCircle size={14} className="shrink-0 text-alert" aria-label="wrong" />}
                          <span className="text-fg">{pretty(a.target)}</span>
                          <span className="text-dim">→ {pretty(a.got)} ({Math.round(a.confidence * 100)}%)</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </>
            )}
          </section>
        </div>
      </SlideUp>
    </>
  )
}
