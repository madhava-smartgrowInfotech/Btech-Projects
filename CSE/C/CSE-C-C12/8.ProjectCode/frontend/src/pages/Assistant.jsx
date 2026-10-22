import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUp, History as HistoryIcon, Sparkles } from 'lucide-react'
import { Alert, Badge, Button, Card, EmptyState, ErrorState, PageHeader, Skeleton, Textarea, useToast } from '../components/ui'
import { DISCLAIMER_TEXT, EvidenceList, Relevance } from '../components/app/Evidence'
import { chatApi, historyApi } from '../lib/api'
import { fmtDate } from '../lib/format'

const MAX = 2000
const MIN = 3
// Example prompts (drawn from the product README) so a first-time user can try it in one click.
const EXAMPLES = [
  'I have high fever, headache and body pain',
  'Dry cough, sore throat and runny nose for three days',
  'Itchy red eyes with watery discharge',
  'Frequent urination, constant thirst and tiredness',
]

function AiMessage({ data }) {
  const top = data.evidence?.[0]
  // The backend prepends the emergency notice to the answer text; it is already shown as the banner above.
  const answer = data.safety_message && data.answer.startsWith(data.safety_message) ? data.answer.slice(data.safety_message.length).trim() : data.answer
  return (
    <div className="msg msg-ai">
      <span className="msg-meta">CareLens AI · {data.generated_by || 'assistant'}</span>
      {data.safety_flag === 'emergency' && <Alert tone="error">{data.safety_message}</Alert>}
      {data.safety_flag === 'caution' && <Alert tone="warning">{data.safety_message}</Alert>}
      {answer && <div className="answer">{answer}</div>}
      {top && (
        <div className="row-between">
          <div className="row">
            <Badge tone="info">Top match</Badge>
            <strong>{data.top_condition}</strong>
            <span className="small muted">({data.relevance_label})</span>
          </div>
          <Relevance value={top.relevance} />
        </div>
      )}
      <EvidenceList items={data.evidence} />
      <p className="disclaimer">{DISCLAIMER_TEXT}</p>
      {data.consultation_id && (
        <Link to={`/history/${data.consultation_id}`} className="small" style={{ fontWeight: 700 }}>
          Saved as consultation #{data.consultation_id} - open in history
        </Link>
      )}
    </div>
  )
}

function Recent({ state, onRetry }) {
  if (state.loading) {
    return (
      <div className="stack" style={{ '--gap': '10px' }} role="status" aria-label="Loading recent consultations">
        <Skeleton height={54} />
        <Skeleton height={54} />
        <Skeleton height={54} />
      </div>
    )
  }
  if (state.error) return <ErrorState title="Could not load history" error={state.error} onRetry={onRetry} />
  if (!state.items.length) {
    return (
      <EmptyState icon={HistoryIcon} title="No consultations yet">
        Your first answer will be saved here automatically.
      </EmptyState>
    )
  }
  return (
    <div>
      {state.items.slice(0, 5).map((c) => (
        <Link key={c.id} to={`/history/${c.id}`} className="recent-item">
          <b>{c.top_condition || 'Consultation'}</b>
          <span className="tiny mono muted" style={{ display: 'block' }}>
            {fmtDate(c.created_at)}
          </span>
          <p>{c.symptom_query}</p>
        </Link>
      ))}
    </div>
  )
}

export default function Assistant() {
  const toast = useToast()
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [recent, setRecent] = useState({ loading: true, error: null, items: [] })
  const logRef = useRef(null)
  const inputRef = useRef(null)
  const abortRef = useRef(null)

  const loadRecent = useCallback(() => {
    setRecent((r) => ({ ...r, loading: true, error: null }))
    historyApi
      .list()
      .then((items) => setRecent({ loading: false, error: null, items }))
      .catch((e) => setRecent({ loading: false, error: e, items: [] }))
  }, [])

  useEffect(() => {
    document.title = 'Symptom assistant - CareLens AI'
    loadRecent()
    return () => abortRef.current?.abort()
  }, [loadRecent])

  // New answers are long: bring the start of the newest message into view (typing indicator: bottom).
  useEffect(() => {
    const el = logRef.current
    if (!el) return
    const msgs = el.querySelectorAll('.msg')
    const last = msgs[msgs.length - 1]
    const top = busy || !last || last.classList.contains('msg-user') ? el.scrollHeight : last.offsetTop - 12
    el.scrollTo({ top, behavior: 'smooth' })
  }, [messages, busy])

  const tooShort = text.trim().length < MIN
  const tooLong = text.length > MAX

  const send = async (raw) => {
    const q = (raw ?? text).trim()
    if (q.length < MIN || q.length > MAX || busy) return
    setText('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    setBusy(true)
    const ctl = new AbortController()
    abortRef.current = ctl
    try {
      const data = await chatApi.ask(q, ctl.signal)
      setMessages((m) => [...m, { role: 'ai', data }])
      toast.success(`Answer saved as consultation #${data.consultation_id}.`)
      loadRecent()
    } catch (e) {
      if (e.name === 'AbortError') return
      if (e.status === 401) {
        toast.error('Your session expired. Please sign in again.')
        return
      }
      setMessages((m) => [...m, { role: 'error', text: e.message, query: q }])
    } finally {
      setBusy(false)
      inputRef.current?.focus()
    }
  }

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Symptom assistant"
        title="Tell us how you feel"
        description="Describe your symptoms in everyday language. CareLens AI retrieves matching medical information and explains it with evidence and safety guidance."
      />
      <div className="assistant-grid">
        <Card className="chat-card" flat={false}>
          <div className="chat-log" ref={logRef} role="log" aria-live="polite" aria-label="Conversation" data-lenis-prevent>
            {messages.length === 0 && (
              <EmptyState
                icon={Sparkles}
                title="Start with your symptoms"
                action={
                  <div className="chips" aria-label="Example symptom descriptions">
                    {EXAMPLES.map((ex) => (
                      <button key={ex} type="button" className="chip" onClick={() => send(ex)} disabled={busy}>
                        {ex}
                      </button>
                    ))}
                  </div>
                }
              >
                Type below, or tap an example. Nothing leaves this machine - consultations are stored locally.
              </EmptyState>
            )}
            {messages.map((m, i) =>
              m.role === 'user' ? (
                <div key={i} className="msg msg-user">
                  {m.text}
                </div>
              ) : m.role === 'ai' ? (
                <AiMessage key={i} data={m.data} />
              ) : (
                <div key={i} className="msg msg-ai">
                  <Alert
                    tone="error"
                    action={
                      <Button size="sm" onClick={() => send(m.query)} disabled={busy}>
                        Retry
                      </Button>
                    }
                  >
                    {m.text} {m.text.startsWith('Cannot reach') ? 'Start the backend with run.bat, then retry.' : 'You can retry or rephrase your symptoms.'}
                  </Alert>
                </div>
              ),
            )}
            {busy && (
              <div className="msg msg-ai" role="status" aria-label="CareLens AI is reviewing medical information">
                <span className="msg-meta">CareLens AI is reviewing medical information</span>
                <span className="typing" aria-hidden="true">
                  <i />
                  <i />
                  <i />
                </span>
                <Skeleton height={64} />
              </div>
            )}
          </div>
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault()
              send()
            }}
          >
            <div className="composer-row">
              <Textarea
                ref={inputRef}
                label="Describe your symptoms"
                placeholder="e.g. I have high fever, headache and body pain since yesterday"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={onKey}
                maxLength={MAX + 200}
                rows={3}
                error={tooLong ? `Too long - the limit is ${MAX} characters.` : undefined}
                hint="Enter to send · Shift+Enter for a new line"
              />
              <Button type="submit" variant="primary" icon={ArrowUp} loading={busy} disabled={tooShort || tooLong}>
                Send
              </Button>
            </div>
            <div className="row-between">
              <span className="small muted">Not a diagnosis. In an emergency call your local emergency number.</span>
              <span className={`char-count ${tooLong ? 'over' : ''}`}>
                {text.length}/{MAX}
              </span>
            </div>
          </form>
        </Card>

        <Card title="Recent consultations" actions={<Button size="sm" variant="ghost" to="/history">View all</Button>}>
          <Recent state={recent} onRetry={loadRecent} />
        </Card>
      </div>
    </>
  )
}
