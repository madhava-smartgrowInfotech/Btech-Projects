import { useCallback, useEffect, useRef, useState } from 'react'
import { Download, Hand, Loader2, Mic, MicOff, Save, Sparkles, Trash2, Volume2, X } from 'lucide-react'
import api, { errorText } from '../api'
import CameraView from '../components/CameraView.jsx'
import { ErrorBox } from '../components/ui.jsx'
import useSignRecognizer from '../hooks/useSignRecognizer.js'
import useSubtitles from '../hooks/useSubtitles.js'

const AUTO_SENTENCE_MS = 3000

export async function speak(text) {
  const res = await api.post('/tts', { text }, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const audio = new Audio(url)
  audio.onended = () => URL.revokeObjectURL(url)
  await audio.play()
  return Number(res.headers['x-latency-ms'] || 0)
}

export function transcriptText(title, messages) {
  const lines = messages.map((m) => `[${new Date(m.created_at || m.at).toLocaleTimeString()}] ${m.side === 'signer' ? 'Signer' : 'Speaker'}: ${m.text}`)
  return `${title}\n${'='.repeat(title.length)}\n\n${lines.join('\n')}\n`
}

export function downloadText(name, text) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain' }))
  a.download = name
  a.click()
  URL.revokeObjectURL(a.href)
}

export default function Conversation() {
  const [mode, setMode] = useState('words')
  const [glosses, setGlosses] = useState([]) // {gloss, text, confidence}
  const [lastSignAt, setLastSignAt] = useState(0)
  const [autoSentence, setAutoSentence] = useState(true)
  const [autoSpeak, setAutoSpeak] = useState(true)
  const [useGemini, setUseGemini] = useState(true)
  const [building, setBuilding] = useState(false)
  const [signError, setSignError] = useState('')
  const [lastSentence, setLastSentence] = useState(null)
  const [messages, setMessages] = useState([])
  const [language, setLanguage] = useState('en')
  const [subtitle, setSubtitle] = useState('')
  const [title, setTitle] = useState(`Conversation ${new Date().toLocaleDateString()}`)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(null)
  const [saveError, setSaveError] = useState('')
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
    setSignError('')
    const used = glosses
    try {
      const { data } = await api.post('/sentence', { glosses: used.map((g) => g.gloss), use_gemini: useGemini })
      const conf = used.reduce((s, g) => s + g.confidence, 0) / used.length
      setLastSentence(data)
      setGlosses((g) => g.slice(used.length))
      addMessage({ side: 'signer', text: data.sentence, gloss: used.map((g) => g.gloss), confidence: conf, source: data.source, latency_ms: data.latency_ms })
      if (autoSpeak) speak(data.sentence).catch((e) => setSignError(`Speech output failed: ${errorText(e)}`))
    } catch (e) {
      setSignError(errorText(e))
    } finally {
      setBuilding(false)
    }
  }, [glosses, building, useGemini, autoSpeak])

  // sliding window: a pause after the last sign closes the sentence
  useEffect(() => {
    if (!autoSentence || !glosses.length) return
    const t = setTimeout(buildSentence, Math.max(0, AUTO_SENTENCE_MS - (Date.now() - lastSignAt)))
    return () => clearTimeout(t)
  }, [glosses, lastSignAt, autoSentence, buildSentence])

  useEffect(() => { transcriptEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [messages])

  const save = async () => {
    setSaving(true)
    setSaveError('')
    try {
      const clean = messages.map(({ at, ...m }) => m)
      if (savedTo.current.id) {  // already saved: append only the new messages
        for (const m of clean.slice(savedTo.current.count)) await api.post(`/conversations/${savedTo.current.id}/messages`, m)
      } else {
        savedTo.current.id = (await api.post('/conversations', { title, messages: clean })).data.id
      }
      savedTo.current.count = clean.length
      setSaved(savedTo.current.id)
    } catch (e) {
      setSaveError(errorText(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* signer side */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Hand className="text-indigo-600" size={20} />
          <h2 className="font-semibold text-lg">Signer</h2>
          <span className="text-sm text-slate-500">signs → text → speech</span>
        </div>
        <CameraView rec={rec} mode={mode} setMode={setMode} />
        <div className="card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recognised signs</div>
            {glosses.length > 0 && <button className="text-xs text-slate-500 hover:text-rose-600" onClick={() => setGlosses([])}>Clear</button>}
          </div>
          <div className="flex flex-wrap gap-2 min-h-9">
            {glosses.length === 0 && <span className="text-sm text-slate-400">Signs appear here as you make them.</span>}
            {glosses.map((g, i) => (
              <span key={i} className="chip bg-indigo-50 text-indigo-700 !text-sm !py-1">
                {g.gloss.replaceAll('_', ' ')} <span className="text-indigo-400 text-xs">{Math.round(g.confidence * 100)}%</span>
                <button onClick={() => setGlosses((gs) => gs.filter((_, k) => k !== i))} title="Remove"><X size={12} /></button>
              </span>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button className="btn-primary" onClick={buildSentence} disabled={!glosses.length || building}>
              {building ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />} Make sentence
            </button>
            <label className="flex items-center gap-1.5 text-sm text-slate-600"><input type="checkbox" checked={autoSentence} onChange={(e) => setAutoSentence(e.target.checked)} /> Auto after pause</label>
            <label className="flex items-center gap-1.5 text-sm text-slate-600"><input type="checkbox" checked={autoSpeak} onChange={(e) => setAutoSpeak(e.target.checked)} /> Speak aloud</label>
            <label className="flex items-center gap-1.5 text-sm text-slate-600"><input type="checkbox" checked={useGemini} onChange={(e) => setUseGemini(e.target.checked)} /> Polish online</label>
          </div>
          {lastSentence && (
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
              <div className="flex items-start gap-2">
                <p className="text-xl font-medium text-slate-900 flex-1">{lastSentence.sentence}</p>
                <button className="btn-secondary !px-2" title="Speak again" onClick={() => speak(lastSentence.sentence).catch((e) => setSignError(errorText(e)))}><Volume2 size={16} /></button>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {lastSentence.source === 'gemini' ? 'Polished online' : 'Built offline by rules'} · {lastSentence.latency_ms} ms
                {lastSentence.source === 'gemini' && lastSentence.draft !== lastSentence.sentence && <> · rule draft: “{lastSentence.draft}”</>}
              </p>
            </div>
          )}
          <ErrorBox error={signError} />
        </div>
      </section>

      {/* hearing side + transcript */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Mic className="text-teal-600" size={20} />
          <h2 className="font-semibold text-lg">Hearing person</h2>
          <span className="text-sm text-slate-500">speech → live subtitles</span>
        </div>
        <div className="rounded-2xl bg-slate-900 text-white p-6 min-h-44 flex flex-col justify-between">
          <p className="text-3xl leading-snug font-medium" aria-live="polite">
            {sub.partial || subtitle || <span className="text-slate-500 text-xl">Subtitles for the signer appear here.</span>}
          </p>
          <div className="flex items-center gap-3 mt-4">
            <button className={sub.listening ? 'btn-danger' : 'btn bg-teal-500 text-white hover:bg-teal-600'} onClick={sub.listening ? sub.stop : sub.start}>
              {sub.listening ? <><MicOff size={16} /> Stop listening</> : <><Mic size={16} /> Start listening</>}
            </button>
            <select className="rounded-lg bg-slate-800 text-sm px-2 py-1.5 border border-slate-700" value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="auto">Auto-detect</option>
            </select>
            {sub.listening && <div className="flex-1 h-2 bg-slate-700 rounded-full"><div className="h-2 bg-teal-400 rounded-full transition-all" style={{ width: `${sub.level * 100}%` }} /></div>}
            {sub.lastLatency && <span className="text-xs text-slate-400">{sub.lastLatency} ms</span>}
          </div>
        </div>
        <ErrorBox error={sub.error} />

        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 flex-1">Transcript</div>
            <button className="btn-secondary !py-1 !px-2 !text-xs" disabled={!messages.length} onClick={() => downloadText('signbridge-transcript.txt', transcriptText(title, messages))}><Download size={14} /> .txt</button>
            <button className="btn-secondary !py-1 !px-2 !text-xs" disabled={!messages.length} onClick={() => { setMessages([]); setSaved(null); savedTo.current = { id: null, count: 0 } }}><Trash2 size={14} /> Clear</button>
          </div>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {messages.length === 0 && <p className="text-sm text-slate-400 py-4 text-center">Both sides of the conversation are recorded here.</p>}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.side === 'signer' ? 'justify-start' : 'justify-end'}`}>
                <div className={`max-w-[85%] rounded-2xl px-3 py-2 ${m.side === 'signer' ? 'bg-indigo-50 text-indigo-900' : 'bg-teal-50 text-teal-900'}`}>
                  <div className="text-[11px] opacity-70">{m.side === 'signer' ? 'Signer' : 'Speaker'} · {new Date(m.at).toLocaleTimeString()}{m.gloss && <> · {m.gloss.join(' ')}</>}</div>
                  <div>{m.text}</div>
                </div>
              </div>
            ))}
            <div ref={transcriptEnd} />
          </div>
          <div className="flex gap-2 mt-3">
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Conversation title" />
            <button className="btn-primary whitespace-nowrap" onClick={save} disabled={!messages.length || saving || !title.trim()}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} {saved ? 'Saved' : 'Save'}
            </button>
          </div>
          {saved && <p className="text-xs text-emerald-600 mt-2">Saved to History.</p>}
          <div className="mt-2"><ErrorBox error={saveError} /></div>
        </div>
      </section>
    </div>
  )
}
