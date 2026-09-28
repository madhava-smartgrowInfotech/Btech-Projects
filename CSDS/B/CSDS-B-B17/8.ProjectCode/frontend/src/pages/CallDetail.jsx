import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, CheckCircle2, Flag, Loader2, RefreshCw, Sparkles, Trash2 } from 'lucide-react'
import api, { audioUrl, currentUser, errorText, fmtDate, fmtTime, label } from '../api.js'
import { EmotionTimeline } from '../components/charts.jsx'
import { EMOTION_COLOR, EmotionBadge, ErrorBox, SampleBadge, SentimentValue, Spinner, StatusBadge } from '../components/ui.jsx'

const STATUS_STYLE = {
  resolved: 'bg-green-100 text-green-800',
  partially_resolved: 'bg-yellow-100 text-yellow-800',
  unresolved: 'bg-red-100 text-red-800',
}

function Summary({ call, onUpdate }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const s = call.summary
  const regenerate = async () => {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post(`/calls/${call.id}/summary`)
      onUpdate(data)
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="h2 mb-0">Call summary</h2>
        <button className="btn-secondary px-2 py-1 text-xs" onClick={regenerate} disabled={busy} title="Regenerate with Gemini">
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />} {s ? 'Regenerate' : 'Generate'}
        </button>
      </div>
      {s ? (
        <>
          <p className="text-sm text-slate-700">{s.summary}</p>
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-xs font-medium text-slate-500">Reason for the call</dt>
              <dd>{s.reason}</dd>
            </div>
            <div>
              <dt className="flex items-center gap-2 text-xs font-medium text-slate-500">
                Resolution
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_STYLE[s.status]}`}>{label(s.status)}</span>
              </dt>
              <dd>{s.resolution}</dd>
            </div>
            {s.customer_mood && (
              <div>
                <dt className="text-xs font-medium text-slate-500">Customer mood</dt>
                <dd>{s.customer_mood}</dd>
              </div>
            )}
            <div>
              <dt className="text-xs font-medium text-slate-500">Action items</dt>
              <dd>
                {s.action_items.length ? (
                  <ul className="mt-1 space-y-1">
                    {s.action_items.map((a, i) => (
                      <li key={i} className="flex gap-2">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" />
                        <span>
                          <span className="mr-1 rounded bg-slate-100 px-1.5 text-[10px] font-semibold uppercase text-slate-600">{a.owner}</span>
                          {a.item}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-500">No follow-ups</span>
                )}
              </dd>
            </div>
          </dl>
          <p className="text-[11px] text-slate-400">Written by {s.model}</p>
        </>
      ) : (
        <ErrorBox error={call.summary_error || 'No summary yet'} />
      )}
      <ErrorBox error={error} />
    </div>
  )
}

function Scorecard({ card }) {
  if (!card) return null
  const c = card.total >= 80 ? 'text-green-700' : card.total >= 60 ? 'text-yellow-700' : 'text-red-700'
  return (
    <div className="card">
      <div className="mb-3 flex items-end justify-between">
        <h2 className="h2 mb-0">Agent scorecard</h2>
        <div className={`text-3xl font-bold ${c}`}>
          {card.total}
          <span className="text-base font-medium text-slate-400">/100</span>
        </div>
      </div>
      <div className="space-y-3">
        {card.items.map((it) => (
          <div key={it.key}>
            <div className="flex justify-between text-sm">
              <span className="font-medium">{it.label}</span>
              <span className="text-slate-600">
                {it.points} / {it.weight}
              </span>
            </div>
            <div className="my-1 h-1.5 rounded-full bg-slate-100">
              <div
                className={`h-1.5 rounded-full ${it.score >= 0.8 ? 'bg-green-500' : it.score >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${it.score * 100}%` }}
              />
            </div>
            <div className="text-xs text-slate-500">{it.evidence}</div>
          </div>
        ))}
      </div>
      <p className="mt-3 text-[11px] text-slate-400">Speakers: {card.speaker_mode}</p>
    </div>
  )
}

export default function CallDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const user = currentUser()
  const [call, setCall] = useState(null)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [busy, setBusy] = useState('')
  const [time, setTime] = useState(0)
  const [showAgent, setShowAgent] = useState(false)
  const audio = useRef(null)

  const load = useCallback(async () => {
    try {
      const { data } = await api.get(`/calls/${id}`)
      setCall(data)
      setError('')
    } catch (err) {
      setError(errorText(err))
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])
  useEffect(() => {
    if (!call || !['queued', 'processing'].includes(call.status)) return
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [call, load])

  const seek = (t) => {
    if (audio.current) {
      audio.current.currentTime = t
      audio.current.play().catch(() => {})
    }
  }
  const act = async (kind) => {
    setBusy(kind)
    setActionError('')
    try {
      if (kind === 'reprocess') {
        await api.post(`/calls/${id}/reprocess`)
        load()
      } else {
        await api.delete(`/calls/${id}`)
        nav('/calls')
      }
    } catch (err) {
      setActionError(errorText(err))
    } finally {
      setBusy('')
    }
  }

  if (error) return <ErrorBox error={error} onRetry={load} />
  if (!call) return <Spinner />
  const running = ['queued', 'processing'].includes(call.status)
  const cust = call.segments.filter((s) => s.speaker === 'customer')

  return (
    <div className="space-y-5">
      <div>
        <Link to="/calls" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800">
          <ArrowLeft className="h-4 w-4" /> Calls
        </Link>
        <div className="mt-1 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="flex flex-wrap items-center gap-2 text-2xl font-semibold">
              {call.title.replace('[Sample] ', '')} {call.is_sample && <SampleBadge />}
            </h1>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-slate-500">
              <span>Agent: {call.agent || 'unassigned'}</span>
              <span>{fmtDate(call.recorded_at)}</span>
              <span>{fmtTime(call.duration)}</span>
              <StatusBadge status={call.status} stage={call.stage} />
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={() => act('reprocess')} disabled={running || !!busy}>
              {busy === 'reprocess' ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} Re-run analysis
            </button>
            {(user.role === 'supervisor' || call.agent_id === user.id) && (
              <button className="btn-danger" onClick={() => act('delete')} disabled={running || !!busy}>
                {busy === 'delete' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />} Delete
              </button>
            )}
          </div>
        </div>
      </div>
      <ErrorBox error={actionError} />

      <div className="card p-3">
        <audio ref={audio} controls preload="metadata" src={audioUrl(call.id)} className="w-full" onTimeUpdate={(e) => setTime(e.target.currentTime)} />
      </div>

      {running && (
        <div className="card flex items-center gap-3 text-sm text-slate-600">
          <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
          <div>
            <div className="font-medium text-slate-800">Analysing this call - {call.stage || 'waiting in the queue'}</div>
            Transcription, emotion and scoring run on the CPU and usually take about as long as the call itself.
          </div>
        </div>
      )}
      {call.status === 'failed' && <ErrorBox error={`Analysis failed: ${call.error}`} />}

      {call.status === 'done' && (
        <div className="grid gap-5 lg:grid-cols-[1fr_380px]">
          <div className="space-y-5">
            <div className="card">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h2 className="h2 mb-0">Emotion timeline</h2>
                <label className="flex items-center gap-1.5 text-xs text-slate-600">
                  <input type="checkbox" checked={showAgent} onChange={(e) => setShowAgent(e.target.checked)} /> show agent
                </label>
              </div>
              <EmotionTimeline segments={call.segments} flags={call.flags} duration={call.duration} showAgent={showAgent} onSeek={seek} current={time} />
              <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
                {Object.entries(EMOTION_COLOR).map(([k, v]) => (
                  <span key={k} className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: v }} /> {k}
                  </span>
                ))}
                <span className="text-slate-400">| line = customer valence (text sentiment + voice emotion); ⚑ = flag</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-1 text-xs">
                <span className="mr-1 text-slate-500">Customer journey:</span>
                {cust.map((s, i) => (
                  <span key={i} className="flex items-center gap-1">
                    {i > 0 && <span className="text-slate-300">→</span>}
                    <EmotionBadge emotion={s.emotion} />
                  </span>
                ))}
              </div>
            </div>

            {call.flags.length > 0 && (
              <div className="card">
                <h2 className="h2">Escalation flags</h2>
                <ul className="space-y-1.5 text-sm">
                  {call.flags.map((f, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Flag className={`mt-0.5 h-4 w-4 shrink-0 ${f.severity === 'high' ? 'text-red-600' : 'text-amber-500'}`} />
                      <button className="font-mono text-xs text-indigo-700 hover:underline" onClick={() => seek(f.t)}>{fmtTime(f.t)}</button>
                      <span>{f.text}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="card">
              <h2 className="h2">Transcript</h2>
              <div className="space-y-2">
                {call.segments.map((s, i) => {
                  const active = time >= s.start && time <= s.end + 0.3
                  const agent = s.speaker === 'agent'
                  return (
                    <div key={i} className={`flex ${agent ? '' : 'flex-row-reverse'}`}>
                      <div
                        className={`max-w-[85%] rounded-xl border px-3 py-2 text-sm ${agent ? 'border-indigo-100 bg-indigo-50' : 'border-orange-100 bg-orange-50'} ${active ? 'ring-2 ring-indigo-400' : ''}`}
                      >
                        <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                          <button className="font-mono text-indigo-700 hover:underline" onClick={() => seek(s.start)}>{fmtTime(s.start)}</button>
                          <span className="font-semibold uppercase">{s.speaker}</span>
                          <EmotionBadge emotion={s.emotion} />
                          <span title="text sentiment score">text <SentimentValue value={s.sentiment.score} /></span>
                          {s.voice && (
                            <span title="voice emotion (wav2vec2)">
                              voice: {Object.entries(s.voice).sort((a, b) => b[1] - a[1])[0][0]}
                            </span>
                          )}
                        </div>
                        {s.text}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <Summary call={call} onUpdate={setCall} />
            <div className="card space-y-3 text-sm">
              <h2 className="h2 mb-0">Intent & topic</h2>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-indigo-700 px-2.5 py-1 font-semibold text-white">{call.intent}</span>
                <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-slate-700">topic: {call.topic}</span>
                <span className="text-xs text-slate-500">{Math.round((call.intent_confidence || 0) * 100)}% confidence</span>
              </div>
              {call.intent_evidence && <p className="text-xs italic text-slate-600">“{call.intent_evidence}”</p>}
              <div className="text-xs text-slate-500">
                Runners-up: {call.intent_top.slice(1).map((t) => `${label(t.intent)} (${Math.round(t.score * 100)}%)`).join(', ')}
              </div>
              {call.reference?.intent && (
                <div className="text-xs text-slate-500">
                  Script intent (sample ground truth): <b>{call.reference.intent}</b>{' '}
                  {call.reference.intent === call.intent ? '✓' : '✗'}
                </div>
              )}
              <div>
                <div className="mb-1 text-xs font-medium text-slate-500">Keywords</div>
                <div className="flex flex-wrap gap-1.5">
                  {call.keywords.map((k) => (
                    <span key={k} className="rounded-full border border-slate-200 px-2 py-0.5 text-xs">{k}</span>
                  ))}
                </div>
              </div>
              <div className="text-xs text-slate-500">
                Average customer sentiment <SentimentValue value={call.sentiment} />, change{' '}
                <SentimentValue value={call.sentiment_change} />
              </div>
            </div>
            <Scorecard card={call.scorecard} />
          </div>
        </div>
      )}
    </div>
  )
}
