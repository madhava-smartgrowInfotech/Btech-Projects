import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { CheckCircle2, Flag, FileText, Gauge, MessagesSquare, RefreshCw, Sparkles, Tags, Trash2 } from 'lucide-react'
import api, { audioUrl, errorText } from '../api'
import { useAuth } from '../lib/auth'
import { cleanTitle, EMOTION_COLOR, fmtDate, fmtTime, label } from '../lib/format'
import {
  Alert, Badge, Breadcrumbs, Button, Card, Checkbox, EmptyState, ErrorState, KeyValueList, Modal, PageHeader, ProgressBar, SkeletonBlock, StatusBadge, Tabs, useToast,
} from '../components/ui'
import { EmotionBadge, SampleBadge, SentimentValue } from '../components/app/Bits'
import EmotionTimeline from '../components/app/EmotionTimeline'

const RESOLUTION_TONE = { resolved: 'pass', partially_resolved: 'medium', unresolved: 'blocked' }

function SummaryTab({ call, onUpdate }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const s = call.summary
  const regenerate = async () => {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post(`/calls/${call.id}/summary`)
      onUpdate(data)
      toast.success('Summary regenerated.')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }
  return (
    <Card
      title="Call summary"
      actions={
        <Button size="sm" icon={Sparkles} onClick={regenerate} loading={busy}>
          {s ? 'Regenerate' : 'Generate'}
        </Button>
      }
    >
      {s ? (
        <div className="stack">
          <p className="lead" style={{ maxWidth: '70ch' }}>
            {s.summary}
          </p>
          <KeyValueList
            items={[
              { label: 'Reason', value: s.reason },
              {
                label: 'Resolution',
                value: (
                  <div className="stack" style={{ '--gap': '6px' }}>
                    <div>
                      <Badge tone={RESOLUTION_TONE[s.status]}>{label(s.status)}</Badge>
                    </div>
                    <span>{s.resolution}</span>
                  </div>
                ),
              },
              s.customer_mood ? { label: 'Customer mood', value: s.customer_mood } : undefined,
              {
                label: 'Action items',
                value: s.action_items.length ? (
                  <ul className="action-list">
                    {s.action_items.map((a, i) => (
                      <li key={i}>
                        <CheckCircle2 size={18} aria-hidden="true" style={{ flex: 'none', marginTop: 2 }} />
                        <span>
                          <Badge tone="info">{a.owner}</Badge> {a.item}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="muted">No follow-ups</span>
                ),
              },
            ].filter(Boolean)}
          />
          <p className="tiny mono muted">Written by {s.model}</p>
        </div>
      ) : (
        <Alert tone="warning">{call.summary_error || 'No summary yet. Press Generate to write one with Gemini.'}</Alert>
      )}
      {error && (
        <div style={{ marginTop: 12 }}>
          <Alert tone="error">{error}</Alert>
        </div>
      )}
    </Card>
  )
}

function IntentTab({ call }) {
  const runners = (call.intent_top || []).slice(1)
  return (
    <Card title="Intent and topic">
      <div className="stack">
        <div className="row">
          <Badge tone="live">{label(call.intent)}</Badge>
          <Badge>topic: {label(call.topic)}</Badge>
          <span className="small mono">{Math.round((call.intent_confidence || 0) * 100)}% confidence</span>
        </div>
        {call.intent_evidence && <p className="small" style={{ fontStyle: 'italic' }}>“{call.intent_evidence}”</p>}
        <KeyValueList
          items={[
            { label: 'Runners-up', value: runners.length ? runners.map((t) => `${label(t.intent)} (${Math.round(t.score * 100)}%)`).join(', ') : null },
            call.reference?.intent
              ? {
                  label: 'Script intent',
                  value: (
                    <span>
                      {label(call.reference.intent)} — sample ground truth{' '}
                      <Badge tone={call.reference.intent === call.intent ? 'pass' : 'blocked'}>{call.reference.intent === call.intent ? 'match' : 'miss'}</Badge>
                    </span>
                  ),
                }
              : undefined,
            {
              label: 'Keywords',
              value: call.keywords.length ? (
                <div className="row" style={{ '--gap': '6px' }}>
                  {call.keywords.map((k) => (
                    <Badge key={k}>{k}</Badge>
                  ))}
                </div>
              ) : null,
            },
            {
              label: 'Customer sentiment',
              value: (
                <span>
                  average <SentimentValue value={call.sentiment} />, change <SentimentValue value={call.sentiment_change} />
                </span>
              ),
            },
          ].filter(Boolean)}
        />
      </div>
    </Card>
  )
}

function ScoreTab({ card }) {
  if (!card) return <EmptyState icon={Gauge} title="No scorecard">This call has no scorecard yet. Re-run the analysis.</EmptyState>
  return (
    <Card
      title="Agent scorecard"
      actions={
        <div className="score-big" aria-label={`Total score ${card.total} out of 100`}>
          {card.total}
          <small>/100</small>
        </div>
      }
    >
      <div>
        {card.items.map((it) => (
          <div key={it.key} className="criterion">
            <div className="row-between">
              <strong>{it.label}</strong>
              <span className="mono small">
                {it.points} / {it.weight}
              </span>
            </div>
            <div style={{ margin: '8px 0' }}>
              <ProgressBar value={it.score} max={1} label={it.label} tone={it.score >= 0.8 ? '' : it.score >= 0.5 ? 'amber' : 'coral'} />
            </div>
            <p className="small muted">{it.evidence}</p>
          </div>
        ))}
      </div>
      <p className="tiny mono muted" style={{ marginTop: 12 }}>
        Speakers: {card.speaker_mode}
      </p>
    </Card>
  )
}

function TranscriptTab({ call, time, seek }) {
  return (
    <Card title="Transcript">
      <div className="transcript">
        {call.segments.map((s, i) => {
          const active = time >= s.start && time <= s.end + 0.3
          return (
            <div key={i} className={`bubble-row ${s.speaker}`}>
              <div className={`bubble ${active ? 'active' : ''}`} aria-current={active || undefined}>
                <div className="bubble-meta">
                  <button className="linkish" onClick={() => seek(s.start)} aria-label={`Play from ${fmtTime(s.start)}`}>
                    {fmtTime(s.start)}
                  </button>
                  <strong>{s.speaker}</strong>
                  <EmotionBadge emotion={s.emotion} />
                  <span title="text sentiment score" className="muted">
                    text <SentimentValue value={s.sentiment?.score} />
                  </span>
                  {s.voice && (
                    <span title="voice emotion (wav2vec2)" className="muted">
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
    </Card>
  )
}

export default function CallDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const { user } = useAuth()
  const [call, setCall] = useState(null)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [busy, setBusy] = useState('')
  const [time, setTime] = useState(0)
  const [showAgent, setShowAgent] = useState(false)
  const [tab, setTab] = useState('transcript')
  const [confirmDelete, setConfirmDelete] = useState(false)
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
    setCall(null)
    load()
  }, [load])
  useEffect(() => {
    if (!call || !['queued', 'processing'].includes(call.status)) return undefined
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [call, load])

  const seek = (t) => {
    if (audio.current) {
      audio.current.currentTime = t
      audio.current.play().catch(() => {})
    }
  }

  const reprocess = async () => {
    setBusy('reprocess')
    setActionError('')
    try {
      await api.post(`/calls/${id}/reprocess`)
      toast.success('Analysis restarted.')
      load()
    } catch (err) {
      setActionError(errorText(err))
    } finally {
      setBusy('')
    }
  }
  const remove = async () => {
    setBusy('delete')
    setActionError('')
    try {
      await api.delete(`/calls/${id}`)
      toast.success('Call deleted.')
      nav('/calls')
    } catch (err) {
      setConfirmDelete(false)
      setActionError(errorText(err))
    } finally {
      setBusy('')
    }
  }

  const crumbs = <Breadcrumbs items={[{ label: 'Calls', to: '/calls' }, { label: call ? cleanTitle(call.title) : `Call ${id}` }]} />

  if (error && !call) {
    return (
      <>
        {crumbs}
        <ErrorState title="Could not load this call" error={error} hint="It may have been deleted, or it belongs to another agent. Go back to Calls and pick another." onRetry={load} />
      </>
    )
  }
  if (!call) {
    return (
      <>
        {crumbs}
        <SkeletonBlock rows={6} label="Loading call" />
      </>
    )
  }

  const running = ['queued', 'processing'].includes(call.status)
  const cust = call.segments.filter((s) => s.speaker === 'customer')
  const canDelete = user?.role === 'supervisor' || call.agent_id === user?.id
  const tabs = [
    { id: 'transcript', label: 'Transcript', icon: MessagesSquare, count: call.segments.length },
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'intent', label: 'Intent', icon: Tags },
    { id: 'score', label: 'Scorecard', icon: Gauge },
  ]

  return (
    <>
      <PageHeader
        crumbs={crumbs}
        title={
          <>
            {cleanTitle(call.title)} {call.is_sample && <SampleBadge />}
          </>
        }
        description={
          <span className="row" style={{ '--gap': '14px' }}>
            <span>Agent: {call.agent || 'unassigned'}</span>
            <span>{fmtDate(call.recorded_at)}</span>
            <span>{fmtTime(call.duration)}</span>
            <StatusBadge status={call.status} stage={call.stage} />
          </span>
        }
        actions={
          <>
            <Button icon={RefreshCw} onClick={reprocess} disabled={running || !!busy} loading={busy === 'reprocess'}>
              Re-run analysis
            </Button>
            {canDelete && (
              <Button variant="danger" icon={Trash2} onClick={() => setConfirmDelete(true)} disabled={running || !!busy}>
                Delete
              </Button>
            )}
          </>
        }
      />
      <div className="stack" style={{ '--gap': '20px' }}>
        {actionError && <Alert tone="error">{actionError}</Alert>}

        <Card className="audio-card" flat>
          <audio
            ref={audio}
            controls
            preload="metadata"
            src={audioUrl(call.id)}
            aria-label="Call recording"
            onTimeUpdate={(e) => setTime(e.target.currentTime)}
          />
        </Card>

        {running && (
          <Card tone="lime" aria-live="polite">
            <div className="stack" style={{ '--gap': '10px' }}>
              <strong>Analysing this call — {call.stage || 'waiting in the queue'}</strong>
              <ProgressBar value={call.status === 'queued' ? 0.08 : 0.55} label="Analysis in progress" />
              <p className="small">Transcription, emotion and scoring run on the CPU and usually take about as long as the call itself. This page updates by itself.</p>
            </div>
          </Card>
        )}
        {call.status === 'failed' && (
          <Alert tone="error" action={<Button size="sm" onClick={reprocess} loading={busy === 'reprocess'}>Try again</Button>}>
            Analysis failed: {call.error || 'unknown error'}. Check the audio file and try again.
          </Alert>
        )}

        {call.status === 'done' && (
          <>
            <Card
              title="Emotion timeline"
              actions={
                <Checkbox label="Show agent" checked={showAgent} onChange={setShowAgent} />
              }
            >
              <div className="stack">
                <EmotionTimeline segments={call.segments} flags={call.flags} duration={call.duration} showAgent={showAgent} onSeek={seek} current={time} />
                <div className="emo-key" aria-label="Emotion colours">
                  {Object.entries(EMOTION_COLOR).map(([k, v]) => (
                    <span key={k} className="row" style={{ '--gap': '6px' }}>
                      <i style={{ width: 14, height: 14, background: v, border: '2px solid var(--line)', display: 'inline-block' }} /> {k}
                    </span>
                  ))}
                </div>
                <p className="tiny muted">Line = customer valence (text sentiment + voice emotion). ⚑ = escalation flag. Click a square to jump to that moment.</p>
                <div className="journey">
                  <span className="small muted">Customer journey:</span>
                  {cust.map((s, i) => (
                    <span key={i} className="row" style={{ '--gap': '6px' }}>
                      {i > 0 && <span className="arrow" aria-hidden="true">→</span>}
                      <EmotionBadge emotion={s.emotion} />
                    </span>
                  ))}
                </div>
              </div>
            </Card>

            {call.flags.length > 0 && (
              <Card title="Escalation flags">
                <ul className="flag-list">
                  {call.flags.map((f, i) => (
                    <li key={i}>
                      <Flag size={16} aria-hidden="true" style={{ color: f.severity === 'high' ? 'var(--coral)' : 'var(--fg)' }} />
                      <Badge tone={f.severity === 'high' ? 'high' : 'medium'}>{f.severity}</Badge>
                      <button className="linkish" onClick={() => seek(f.t)} aria-label={`Play from ${fmtTime(f.t)}`}>
                        {fmtTime(f.t)}
                      </button>
                      <span>{f.text}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            <div>
              <Tabs tabs={tabs} value={tab} onChange={setTab} label="Call analysis" />
              {tab === 'transcript' && <TranscriptTab call={call} time={time} seek={seek} />}
              {tab === 'summary' && <SummaryTab call={call} onUpdate={setCall} />}
              {tab === 'intent' && <IntentTab call={call} />}
              {tab === 'score' && <ScoreTab card={call.scorecard} />}
            </div>
          </>
        )}
      </div>

      <Modal
        open={confirmDelete}
        onClose={() => !busy && setConfirmDelete(false)}
        title="Delete this call?"
        footer={
          <>
            <Button onClick={() => setConfirmDelete(false)} disabled={busy === 'delete'}>
              Keep it
            </Button>
            <Button variant="danger" icon={Trash2} onClick={remove} loading={busy === 'delete'}>
              Delete call
            </Button>
          </>
        }
      >
        <p>
          “{cleanTitle(call.title)}” and its recording, transcript, summary and scorecard will be removed. This cannot be undone.
        </p>
      </Modal>
    </>
  )
}
