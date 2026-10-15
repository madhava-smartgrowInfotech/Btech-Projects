import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Bot, FileText, Send } from 'lucide-react'
import api, { errorMessage } from '../api.js'
import { PageHeader } from '../components/ui/Layout.jsx'
import { Alert, Button, Card, Input, KeyValueList, Select, SkeletonBlock, ErrorState, StatCard } from '../components/ui/index.js'
import { BarBlocks, PALETTE } from '../components/ui/Charts.jsx'
import { useToast } from '../components/ui/Toast.jsx'
import AuthImage from '../components/AuthImage.jsx'
import { ModalityBadge, SeverityBadge } from '../components/Badges.jsx'
import { useAuth } from '../lib/auth.jsx'
import { failure, fmtDate, pct } from '../lib/product.js'

// Doctor-only: follow-up questions about this scan. History is kept per scan on the server.
function Assistant({ scanId }) {
  const toast = useToast()
  const [messages, setMessages] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [question, setQuestion] = useState('')
  const [lang, setLang] = useState('en')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const end = useRef(null)

  const loadHistory = () => {
    setLoadError(null)
    api
      .get(`/scans/${scanId}/assistant`)
      .then((r) => setMessages(r.data))
      .catch(async (e) => setLoadError(await failure(e)))
  }
  useEffect(loadHistory, [scanId])
  useEffect(() => {
    end.current?.scrollIntoView?.({ block: 'nearest' })
  }, [messages])

  const ask = async (q) => {
    const text = (q ?? question).trim()
    if (!text || busy) return
    setBusy(true)
    setError('')
    setMessages((m) => [...(m || []), { role: 'user', content: text }])
    setQuestion('')
    try {
      const { data } = await api.post(`/scans/${scanId}/assistant`, { question: text, lang })
      setMessages((m) => [...m, { role: 'assistant', content: data.answer, model: data.model }])
    } catch (err) {
      setError(await errorMessage(err))
      setMessages((m) => m.slice(0, -1))
      setQuestion(text)
      toast.error('The assistant did not answer. Your question is still in the box.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Clinical assistant">
      <div className="stack" style={{ '--gap': '14px' }}>
        <div style={{ maxWidth: 240 }}>
          <Select id="assistant-lang" label="Answer language" value={lang} onChange={(e) => setLang(e.target.value)}>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="te">Telugu</option>
          </Select>
        </div>

        <div className="chat" role="log" aria-label="Conversation with the assistant" aria-live="polite">
          {loadError && (
            <Alert tone="error" action={<Button size="sm" onClick={loadHistory}>Retry</Button>}>
              {loadError.message}
            </Alert>
          )}
          {!messages && !loadError && <SkeletonBlock rows={2} label="Loading conversation" />}
          {messages?.length === 0 && (
            <div className="row" style={{ '--gap': '8px' }}>
              {['Explain this finding', 'What should happen next?', 'What are the limitations of this result?'].map((s) => (
                <Button key={s} variant="ghost" size="sm" onClick={() => ask(s)} disabled={busy}>
                  {s}
                </Button>
              ))}
            </div>
          )}
          {messages?.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>
              {m.content}
              {m.model && <div className="tiny muted" style={{ marginTop: 6 }}>{m.model}</div>}
            </div>
          ))}
          {busy && <p className="small muted" role="status">Thinking…</p>}
          <div ref={end} />
        </div>

        {error && <Alert tone="error">{error}</Alert>}

        <form className="row" style={{ '--gap': '8px' }} onSubmit={(e) => { e.preventDefault(); ask() }}>
          <div style={{ flex: '1 1 220px', minWidth: 0 }}>
            <Input id="assistant-question" label="Ask about this result" value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={1000} placeholder="e.g. What should happen next?" />
          </div>
          <Button type="submit" variant="primary" icon={Send} loading={busy} disabled={!question.trim()}>
            Send
          </Button>
        </form>
        <p className="tiny muted">The assistant supports clinical review. It does not diagnose, and it does not replace the reviewing clinician.</p>
      </div>
    </Card>
  )
}

export default function Result() {
  const { id } = useParams()
  const { user } = useAuth()
  const [scan, setScan] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    setScan(null)
    api
      .get(`/scans/${id}`)
      .then((r) => setScan(r.data))
      .catch(async (e) => setError(await failure(e)))
  }
  useEffect(load, [id])

  if (error) {
    return (
      <ErrorState
        title="This result could not be opened"
        error={error.message}
        hint={error.status === 404 ? 'The scan may have been removed. Go back to the patient list and pick it again.' : undefined}
        onRetry={load}
      />
    )
  }
  if (!scan) return <SkeletonBlock rows={5} label="Loading result" />

  const d = scan.details || {}
  const steps = d.preprocessing || []
  const chart = Object.entries(scan.probabilities)
    .sort((a, b) => b[1] - a[1])
    .map(([c, p], i) => ({ class: c, pct: Number((p * 100).toFixed(1)), top: i === 0 }))

  return (
    <div className="page">
      <PageHeader
        eyebrow={`Scan #${scan.id}`}
        title={scan.prediction}
        description={
          <>
            <Link to={`/patients/${scan.patient_id}`}>
              {scan.patient_code} · {scan.patient_name}
            </Link>{' '}
            · {scan.filename} · {fmtDate(scan.created_at)}
          </>
        }
        actions={
          user?.role === 'doctor' ? (
            <Button variant="primary" icon={FileText} to={`/scans/${scan.id}/report`}>
              Report
            </Button>
          ) : null
        }
      />

      <div className="split">
        <Card title="AI finding">
          <div className="stack" style={{ '--gap': '18px' }}>
            <div className="row" style={{ '--gap': '8px' }}>
              <ModalityBadge value={scan.modality} />
              <span className="tiny muted">Modality match {d.modality_scores?.[scan.modality] ?? '—'}</span>
            </div>
            <div className="stat-grid">
              <StatCard label="Confidence" value={pct(scan.confidence)} hint="temperature-calibrated" />
              <StatCard label="Affected area" value={`${scan.affected_pct}%`} hint="high Grad-CAM activation" />
            </div>
            <div className="row" style={{ '--gap': '10px' }}>
              <span className="field-label">Severity</span>
              <SeverityBadge value={scan.severity} />
            </div>
            <div>
              <h3 className="card-subtitle">Class probabilities</h3>
              <BarBlocks data={chart} xKey="class" yKey="pct" name="Probability (%)" height={260} colorFn={(row) => (row.top ? PALETTE.lime : PALETTE.sky)} />
            </div>
            <Alert tone="warning">{scan.disclaimer}</Alert>
          </div>
        </Card>

        <Card title="Evidence">
          <div className="grid grid-2" style={{ '--gap': '16px' }}>
            <figure className="figure">
              <AuthImage className="fig-img" src={`/scans/${scan.id}/image/mask`} alt="Lung mask" />
              <figcaption className="tiny muted">
                Lung mask · {d.mask_method} ({d.lung_area_pct}% of the image)
              </figcaption>
            </figure>
            <figure className="figure">
              <AuthImage className="fig-img" src={`/scans/${scan.id}/image/heatmap`} alt="Grad-CAM heatmap" />
              <figcaption className="tiny muted">
                Grad-CAM for “{scan.prediction}”. Red shows the strongest evidence.
              </figcaption>
            </figure>
          </div>
        </Card>
      </div>

      <Card title="Preprocessing">
        <div className="grid grid-4" style={{ '--gap': '16px' }}>
          <figure className="figure">
            <AuthImage className="fig-img" src={`/scans/${scan.id}/image/original`} alt="Original scan" />
            <figcaption className="tiny">
              <strong>Original</strong>
              <br />
              <span className="muted">
                {d.input?.format}
                {d.input?.width ? `, ${d.input.width}×${d.input.height}` : ''}
              </span>
            </figcaption>
          </figure>
          {steps
            .filter((s) => s.image)
            .map((s) => (
              <figure className="figure" key={s.step}>
                <AuthImage className="fig-img" src={`/scans/${scan.id}/image/${s.image}`} alt={s.step} />
                <figcaption className="tiny">
                  <strong>{s.step}</strong>
                  <br />
                  <span className="muted">{s.detail}</span>
                </figcaption>
              </figure>
            ))}
        </div>
        {steps.some((s) => !s.image) && (
          <div style={{ marginTop: 18 }}>
            <KeyValueList items={steps.filter((s) => !s.image).map((s) => ({ label: s.step, value: s.detail }))} />
          </div>
        )}
      </Card>

      {user?.role === 'doctor' ? (
        <Assistant scanId={scan.id} />
      ) : (
        <Alert tone="info">The clinical assistant and PDF reports are available to doctors.</Alert>
      )}
    </div>
  )
}
