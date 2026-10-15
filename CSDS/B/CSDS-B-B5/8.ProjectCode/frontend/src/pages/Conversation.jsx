import { Download, Hand, Mic, MicOff, Save, Sparkles, Trash2, Volume2, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { describeError } from '../api'
import CameraView from '../components/CameraView'
import { SlideUp } from '../components/motion'
import { Button, IconButton, Input, Select, Switch } from '../components/ui/controls'
import { Badge, Card, StatusDot } from '../components/ui/display'
import { PageHeader } from '../components/ui/AppShell'
import { EmptyState, ErrorState, ProgressBar, useToast } from '../components/ui/feedback'
import useSignRecognizer from '../hooks/useSignRecognizer'
import useSubtitles from '../hooks/useSubtitles'
import { downloadText, label as pretty, transcriptText } from '../format'
import { logEvent } from '../lib/activity'
import { useHealth } from '../lib/health'
import { speak } from '../lib/speech'

const AUTO_SENTENCE_MS = 3000
const LANGS = [['en', 'English'], ['hi', 'Hindi'], ['auto', 'Auto-detect']]

export default function Conversation() {
  const toast = useToast()
  const { health } = useHealth()
  const [mode, setMode] = useState('words')
  const [glosses, setGlosses] = useState([]) // {gloss, text, confidence}
  const [lastSignAt, setLastSignAt] = useState(0)
  const [autoSentence, setAutoSentence] = useState(true)
  const [autoSpeak, setAutoSpeak] = useState(true)
  const [useGemini, setUseGemini] = useState(true)
  const [building, setBuilding] = useState(false)
  const [signError, setSignError] = useState(null)
  const [lastSentence, setLastSentence] = useState(null)
  const [messages, setMessages] = useState([])
  const [language, setLanguage] = useState('en')
  const [subtitle, setSubtitle] = useState('')
  const [title, setTitle] = useState(() => `Conversation ${new Date().toLocaleDateString()}`)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(null)
  const [saveError, setSaveError] = useState(null)
  const transcriptEnd = useRef(null)
  const savedTo = useRef({ id: null, count: 0 })

  const onEvent = useCallback((ev) => {
    if (ev.type === 'sign') {
      setGlosses((g) => [...g, { gloss: ev.gloss, text: ev.text, confidence: ev.confidence }])
      setLastSignAt(Date.now())
    }
  }, [])
  const rec = useSignRecognizer({ mode, onEvent })

  const addMessage = (m) => { setMessages((ms) => [...ms, { ...m, at: new Date().toISOString() }]); setSaved(null) }

  const sub = useSubtitles({
    language,
    onFinal: (text, data) => {
      setSubtitle(text)
      addMessage({ side: 'hearing', text, latency_ms: data.latency_ms, source: 'whisper' })
    },
  })

  const buildSentence = useCallback(async () => {
    if (!glosses.length || building) return
    setBuilding(true)
    setSignError(null)
    const used = glosses
    try {
      const { data } = await api.post('/sentence', { glosses: used.map((g) => g.gloss), use_gemini: useGemini })
      const conf = used.reduce((s, g) => s + g.confidence, 0) / used.length
      setLastSentence(data)
      setGlosses((g) => g.slice(used.length))
      addMessage({ side: 'signer', text: data.sentence, gloss: used.map((g) => g.gloss), confidence: conf, source: data.source, latency_ms: data.latency_ms })
      if (autoSpeak) speak(data.sentence).catch((e) => setSignError(describeError(e)))
    } catch (e) {
      setSignError(describeError(e))
    } finally {
      setBuilding(false)
    }
  }, [glosses, building, useGemini, autoSpeak])

  // a pause after the last sign closes the sentence
  useEffect(() => {
    if (!autoSentence || !glosses.length) return
    const t = setTimeout(buildSentence, Math.max(0, AUTO_SENTENCE_MS - (Date.now() - lastSignAt)))
    return () => clearTimeout(t)
  }, [glosses, lastSignAt, autoSentence, buildSentence])

  useEffect(() => { transcriptEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [messages])

  const save = async () => {
    setSaving(true)
    setSaveError(null)
    try {
      const clean = messages.map(({ at, ...m }) => m)
      if (savedTo.current.id) { // already saved: append only the new messages
        for (const m of clean.slice(savedTo.current.count)) await api.post(`/conversations/${savedTo.current.id}/messages`, m)
      } else {
        savedTo.current.id = (await api.post('/conversations', { title, messages: clean })).data.id
      }
      savedTo.current.count = clean.length
      setSaved(savedTo.current.id)
      logEvent('history', `saved “${title}” (${clean.length} messages)`)
      toast({ tone: 'ok', title: 'Saved to History', body: `${clean.length} messages in “${title}”.` })
    } catch (e) {
      setSaveError(describeError(e))
    } finally {
      setSaving(false)
    }
  }

  const clearTranscript = () => { setMessages([]); setSaved(null); savedTo.current = { id: null, count: 0 } }
  const speechLoading = health && !health.speech_ready

  return (
    <>
      <PageHeader eyebrow="conversation" title="Live conversation"
        subtitle="Signs become text and speech on the left; the hearing person's voice becomes live subtitles on the right. Everything runs on this computer." />
      <SlideUp>
        <div className="grid gap-6 xl:grid-cols-2">
          {/* ---------- signer ---------- */}
          <section className="min-w-0 space-y-4" aria-label="Signer">
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.14em] text-muted">
              <Hand size={15} className="text-ok" aria-hidden="true" /> Signer <span className="text-dim">· signs → text → speech</span>
            </div>
            <CameraView rec={rec} mode={mode} setMode={setMode} />

            <Card title="recognised signs" bodyClass="p-4 space-y-4"
              action={glosses.length > 0 ? <Button size="sm" variant="ghost" onClick={() => setGlosses([])}>Clear</Button> : null}>
              <ul className="flex min-h-9 flex-wrap items-center gap-2" aria-label="Recognised signs">
                {glosses.length === 0 && <li className="font-mono text-xs text-dim">signs appear here as you make them…</li>}
                {glosses.map((g, i) => (
                  <li key={i} className="inline-flex items-center gap-2 rounded-[4px] border border-ok/40 bg-ok/10 py-1 pl-2.5 pr-1 font-mono text-xs uppercase text-ok">
                    {pretty(g.gloss)} <span className="text-dim">{Math.round(g.confidence * 100)}%</span>
                    <button type="button" aria-label={`Remove ${pretty(g.gloss)}`} onClick={() => setGlosses((gs) => gs.filter((_, k) => k !== i))}
                      className="rounded p-0.5 text-dim hover:text-alert"><X size={12} /></button>
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
                <Button icon={Sparkles} loading={building} disabled={!glosses.length} onClick={buildSentence}>Make sentence</Button>
                <Switch checked={autoSentence} onChange={setAutoSentence} label="auto after pause" />
                <Switch checked={autoSpeak} onChange={setAutoSpeak} label="speak aloud" />
                <Switch checked={useGemini} onChange={setUseGemini} label="polish online" />
              </div>
              {lastSentence && (
                <div className="rounded-[6px] border border-line-strong bg-panel-2 p-3">
                  <div className="flex items-start gap-2">
                    <p className="flex-1 text-xl font-medium leading-snug text-fg" aria-live="polite">{lastSentence.sentence}</p>
                    <IconButton icon={Volume2} label="Speak again" onClick={() => speak(lastSentence.sentence).catch((e) => setSignError(describeError(e)))} />
                  </div>
                  <p className="mt-1.5 flex flex-wrap items-center gap-2 font-mono text-[11px] text-dim">
                    <Badge tone={lastSentence.source === 'gemini' ? 'info' : 'ok'}>{lastSentence.source === 'gemini' ? 'polished online' : 'built offline by rules'}</Badge>
                    {lastSentence.latency_ms} ms
                    {lastSentence.source === 'gemini' && lastSentence.draft !== lastSentence.sentence && <span>rule draft: “{lastSentence.draft}”</span>}
                  </p>
                </div>
              )}
              {signError && <ErrorState compact title="Sentence / speech" error={signError} />}
            </Card>
          </section>

          {/* ---------- hearing person ---------- */}
          <section className="min-w-0 space-y-4" aria-label="Hearing person">
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.14em] text-muted">
              <Mic size={15} className="text-cyan" aria-hidden="true" /> Hearing person <span className="text-dim">· speech → live subtitles</span>
            </div>
            <Card title="subtitles.live" bodyClass="p-0"
              action={<StatusDot tone={sub.listening ? 'ok' : 'warn'} blink={sub.listening} label={sub.listening ? 'listening' : 'idle'} />}>
              <div className="flex min-h-44 flex-col justify-between gap-6 p-5">
                <p className="font-mono text-2xl leading-snug text-fg sm:text-3xl" aria-live="polite">
                  {sub.partial || subtitle || <span className="text-lg text-dim">Subtitles for the signer appear here.</span>}
                </p>
                <div className="space-y-3">
                  {sub.listening && <ProgressBar value={sub.level * 100} label="microphone level" segments={32} tone="cyan" />}
                  <div className="flex flex-wrap items-end gap-3">
                    <Button variant={sub.listening ? 'danger' : 'primary'} icon={sub.listening ? MicOff : Mic}
                      disabled={!sub.listening && speechLoading} onClick={sub.listening ? sub.stop : sub.start}>
                      {sub.listening ? 'Stop listening' : 'Start listening'}
                    </Button>
                    <Select srLabel="Speech language" className="w-40" value={language} onChange={(e) => setLanguage(e.target.value)} options={LANGS} />
                    {sub.lastLatency && <span className="pb-2 font-mono text-xs text-dim">{sub.lastLatency} ms</span>}
                  </div>
                  {speechLoading && <p className="font-mono text-xs text-warn">The offline speech model ({health.speech_model}) is still loading; listening unlocks when it is ready.</p>}
                </div>
              </div>
            </Card>
            {sub.error && <ErrorState compact title="Microphone / speech" error={{ message: sub.error, hint: 'Allow microphone access in the browser, or retry once the speech model is ready.' }} />}

            <Card title="transcript" eyebrow={`${messages.length} messages`} bodyClass="p-4 space-y-4"
              action={(
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" icon={Download} disabled={!messages.length}
                    onClick={() => downloadText('signbridge-transcript.txt', transcriptText(title, messages))}>.txt</Button>
                  <Button size="sm" variant="secondary" icon={Trash2} disabled={!messages.length} onClick={clearTranscript}>Clear</Button>
                </div>
              )}>
              <div className="max-h-80 space-y-2 overflow-y-auto pr-1" role="log" aria-label="Transcript">
                {messages.length === 0 && (
                  <EmptyState icon={Mic} title="No messages yet" body="Make a sign and let the sentence close, or start listening and speak. Both sides are recorded here." />
                )}
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.side === 'signer' ? 'justify-start' : 'justify-end'}`}>
                    <div className={`max-w-[88%] rounded-[6px] border px-3 py-2 ${m.side === 'signer' ? 'border-ok/30 bg-ok/[0.07]' : 'border-cyan/30 bg-cyan/[0.07]'}`}>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-dim">
                        {m.side === 'signer' ? 'Signer' : 'Speaker'} · {new Date(m.at).toLocaleTimeString()}{m.gloss && <> · {m.gloss.map(pretty).join(' ')}</>}
                      </div>
                      <div className="text-sm text-fg">{m.text}</div>
                    </div>
                  </div>
                ))}
                <div ref={transcriptEnd} />
              </div>
              <div className="flex flex-wrap items-end gap-2">
                <Input label="Title" className="min-w-0 flex-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Conversation title" />
                <Button icon={Save} loading={saving} disabled={!messages.length || !title.trim()} onClick={save}>{saved ? 'Saved' : 'Save'}</Button>
              </div>
              {saved && <p className="font-mono text-xs text-ok">Saved to History. <Link className="underline hover:text-fg" to="/app/history">Open History</Link></p>}
              {saveError && <ErrorState compact title="Save failed" error={saveError} onRetry={save} />}
            </Card>
          </section>
        </div>
      </SlideUp>
    </>
  )
}
