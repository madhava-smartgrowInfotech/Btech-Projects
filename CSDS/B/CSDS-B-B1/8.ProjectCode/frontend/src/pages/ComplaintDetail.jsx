import { ArrowLeft, Brain, Check, MapPin, MessageSquare, RefreshCw, Send, Sparkles, User, WandSparkles } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { CircleMarker, MapContainer } from 'react-leaflet'
import { Link, useParams } from 'react-router-dom'
import api, { errorMessage } from '../api.js'
import { CategoryWords, PriorityFactors, TimeFactors } from '../components/Explain.jsx'
import { BaseTiles } from '../components/MapPicker.jsx'
import { days, ErrorBox, fmtDate, Loading, pct, PriorityBadge, SampleBadge, SlaFlag, Spinner, StatusBadge } from '../components/ui.jsx'

const FIELDS = [
  { key: 'category', label: 'Category' },
  { key: 'department', label: 'Department' },
  { key: 'priority', label: 'Priority' },
]

function Section({ title, icon: Icon, children, right }) {
  return (
    <section className="card p-5">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          {Icon && <Icon className="h-4 w-4 text-brand-700" />} {title}
        </h2>
        {right}
      </div>
      {children}
    </section>
  )
}

function Extraction({ c, onDone }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const ex = c.extraction
  async function run() {
    setBusy(true)
    setError('')
    try {
      await api.post(`/complaints/${c.id}/extract`)
      onDone()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  const button = (
    <button className="btn-secondary px-2.5 py-1 text-xs" onClick={run} disabled={busy}>
      {busy ? <Spinner className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />} {c.extraction_status === 'done' ? 'Re-run' : 'Extract details'}
    </button>
  )
  return (
    <Section title="Key details (Gemini)" icon={Sparkles} right={c.extraction_status !== 'pending' && button}>
      {c.extraction_status === 'pending' ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Spinner /> Extracting details...
        </div>
      ) : c.extraction_status === 'done' ? (
        <dl className="grid gap-x-4 gap-y-2 text-sm sm:grid-cols-2">
          {[
            ['Place', ex.place],
            ['Issue', ex.issue],
            ['Affected people', ex.affected_people],
            ['Since', ex.duration],
            ['Hazards', ex.hazards?.length ? ex.hazards.join(', ') : null],
          ].map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs text-slate-500">{k}</dt>
              <dd className="text-slate-800">{v || <span className="text-slate-400">not mentioned</span>}</dd>
            </div>
          ))}
          <div className="sm:col-span-2">
            <dt className="text-xs text-slate-500">Summary</dt>
            <dd className="text-slate-800">{ex.summary_en}</dd>
          </div>
        </dl>
      ) : c.extraction_status === 'failed' ? (
        <ErrorBox message={`Extraction failed: ${ex?.error || 'unknown error'}`} />
      ) : (
        <p className="text-sm text-slate-500">Not extracted yet.</p>
      )}
      <div className="mt-2">
        <ErrorBox message={error} />
      </div>
    </Section>
  )
}

function Suggestion({ c, meta, onSaved }) {
  const ai = c.ai
  const decided = !!c.final.department
  const closed = ['Resolved', 'Rejected'].includes(c.status)
  const initial = () => ({
    category: c.final.category || ai.category,
    department: c.final.department || ai.department,
    priority: c.final.priority || ai.priority,
  })
  const [editing, setEditing] = useState(!decided)
  const [values, setValues] = useState(initial)
  const [reasons, setReasons] = useState({})
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setValues(initial())
    setEditing(!c.final.department)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [c.id, c.final.department])

  const options = {
    category: meta?.categories.map((x) => x.name) || [],
    department: meta?.departments.map((x) => x.name) || [],
    priority: ['Low', 'Medium', 'High', 'Critical'],
  }
  const conf = { category: ai.category_confidence, department: ai.department_confidence, priority: ai.priority_confidence }
  const alts = {
    category: ai.category_top3,
    department: ai.department_top3,
    priority: Object.entries(ai.priority_proba || {})
      .map(([label, p]) => ({ label, p }))
      .sort((a, b) => b.p - a.p),
  }
  const changed = FIELDS.filter((f) => values[f.key] !== ai[f.key])

  async function save() {
    setBusy(true)
    setError('')
    try {
      await api.post(`/complaints/${c.id}/decision`, { ...values, reasons, note })
      setReasons({})
      setNote('')
      onSaved(changed.length > 0)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Section
      title="AI suggestion & your decision"
      icon={Brain}
      right={
        decided &&
        !closed &&
        !editing && (
          <button className="btn-secondary px-2.5 py-1 text-xs" onClick={() => setEditing(true)}>
            Change decision
          </button>
        )
      }
    >
      {decided && !editing ? (
        <div className="space-y-2 text-sm">
          {FIELDS.map((f) => (
            <div key={f.key} className="flex items-center justify-between gap-2">
              <span className="text-slate-500">{f.label}</span>
              <span className="flex items-center gap-2 font-medium text-slate-900">
                {f.key === 'priority' ? <PriorityBadge priority={c.final.priority} /> : c.final[f.key]}
                {c.final[f.key] !== ai[f.key] && <span className="rounded bg-amber-50 px-1.5 text-[10px] font-semibold uppercase text-amber-800">overridden</span>}
              </span>
            </div>
          ))}
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Expected time</span>
            <span className="font-medium text-slate-900">~{days(c.final.expected_days)}</span>
          </div>
          <p className="pt-1 text-xs text-slate-500">
            Decided by {c.final.reviewed_by} · {fmtDate(c.final.reviewed_at)}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {FIELDS.map((f) => {
            const isChanged = values[f.key] !== ai[f.key]
            return (
              <div key={f.key}>
                <div className="flex items-baseline justify-between gap-2">
                  <label className="label" htmlFor={f.key}>
                    {f.label}
                  </label>
                  <span className="text-xs text-slate-500">
                    AI: <b className="text-slate-700">{ai[f.key]}</b> ({pct(conf[f.key])})
                  </span>
                </div>
                <select id={f.key} className="input" value={values[f.key]} onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}>
                  {options[f.key].map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
                <div className="mt-1 flex flex-wrap gap-x-3 text-[11px] text-slate-500">
                  {alts[f.key]?.slice(0, 3).map((a) => (
                    <span key={a.label}>
                      {a.label} {pct(a.p)}
                    </span>
                  ))}
                </div>
                {isChanged && (
                  <input
                    className="input mt-2 border-amber-300"
                    placeholder={`Why change the ${f.label.toLowerCase()}? (required - becomes a training label)`}
                    value={reasons[f.key] || ''}
                    onChange={(e) => setReasons({ ...reasons, [f.key]: e.target.value })}
                  />
                )}
              </div>
            )
          })}
          <div className="rounded-lg bg-slate-50 p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Expected time to resolve</span>
              <span className="font-semibold text-slate-900">~{days(ai.expected_days)}</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
              <span>SLA {c.current.sla_days} days</span>
              <SlaFlag risk={c.current.sla_breach_risk} breached={c.current.sla_breached && !closed} />
            </div>
            {changed.some((f) => f.key !== 'department') && <p className="mt-1 text-xs text-slate-500">Time will be re-estimated for your category / priority.</p>}
          </div>
          <input className="input" placeholder="Note for the citizen (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
          <ErrorBox message={error} />
          <div className="flex gap-2">
            <button className="btn-primary flex-1" onClick={save} disabled={busy || !meta}>
              {busy ? <Spinner /> : <Check className="h-4 w-4" />}
              {changed.length ? `Save with ${changed.length} override${changed.length > 1 ? 's' : ''}` : 'Accept & assign'}
            </button>
            {decided && (
              <button className="btn-secondary" onClick={() => setEditing(false)}>
                Cancel
              </button>
            )}
          </div>
        </div>
      )}
    </Section>
  )
}

function StatusActions({ c, onSaved }) {
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  if (['Resolved', 'Rejected'].includes(c.status)) return null
  async function set(status) {
    setBusy(status)
    setError('')
    try {
      await api.post(`/complaints/${c.id}/status`, { status, note })
      setNote('')
      onSaved()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }
  const decided = !!c.final.department
  return (
    <Section title="Update status" icon={RefreshCw}>
      <textarea className="input min-h-16" placeholder="Update for the citizen (optional; required to reject)" value={note} onChange={(e) => setNote(e.target.value)} />
      <div className="mt-3 flex flex-wrap gap-2">
        {c.status !== 'In Progress' && (
          <button className="btn-secondary" disabled={!decided || !!busy} onClick={() => set('In Progress')}>
            {busy === 'In Progress' && <Spinner />} In progress
          </button>
        )}
        <button className="btn-primary" disabled={!decided || !!busy} onClick={() => set('Resolved')}>
          {busy === 'Resolved' && <Spinner />} Mark resolved
        </button>
        <button className="btn-danger" disabled={!!busy} onClick={() => set('Rejected')}>
          {busy === 'Rejected' && <Spinner />} Reject
        </button>
      </div>
      {!decided && <p className="mt-2 text-xs text-slate-500">Accept or override the AI suggestion first.</p>}
      <div className="mt-2">
        <ErrorBox message={error} />
      </div>
    </Section>
  )
}

function ReplyBox({ c, onSent }) {
  const [note, setNote] = useState('')
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [sent, setSent] = useState(false)
  async function makeDraft() {
    setBusy('draft')
    setError('')
    setSent(false)
    try {
      setDraft((await api.post(`/complaints/${c.id}/draft-reply`, { note })).data.draft)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }
  async function send() {
    setBusy('send')
    setError('')
    try {
      await api.post(`/complaints/${c.id}/reply`, { message: draft })
      setDraft('')
      setNote('')
      setSent(true)
      onSent()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }
  return (
    <Section title={`Reply to citizen (${c.language})`} icon={MessageSquare}>
      <div className="flex gap-2">
        <input className="input" placeholder="What should the reply mention? (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
        <button className="btn-secondary shrink-0" onClick={makeDraft} disabled={!!busy}>
          {busy === 'draft' ? <Spinner /> : <WandSparkles className="h-4 w-4" />} Draft with Gemini
        </button>
      </div>
      <textarea className="input mt-3 min-h-32" placeholder="Write a reply or generate a draft, then edit it before sending." value={draft} onChange={(e) => setDraft(e.target.value)} />
      <div className="mt-2 flex items-center justify-between gap-2">
        <span className="text-xs text-slate-500">{sent ? 'Sent - the citizen can see it on their status page.' : 'The citizen sees this on their status page.'}</span>
        <button className="btn-primary" onClick={send} disabled={!!busy || draft.trim().length < 5}>
          {busy === 'send' ? <Spinner /> : <Send className="h-4 w-4" />} Send
        </button>
      </div>
      <div className="mt-2">
        <ErrorBox message={error} />
      </div>
    </Section>
  )
}

export function RetrainPanel({ highlight, compact }) {
  const [info, setInfo] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const load = useCallback(() => {
    api
      .get('/model/metrics')
      .then((r) => setInfo(r.data))
      .catch((err) => setError(errorMessage(err)))
  }, [])
  useEffect(load, [load, highlight])
  async function retrain() {
    setBusy(true)
    setError('')
    try {
      setResult((await api.post('/model/retrain')).data)
      load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  const rows = result && [
    ['Category accuracy', result.before?.category.test.accuracy, result.after.category.test.accuracy],
    ['Department accuracy', result.before?.department.test.accuracy, result.after.department.test.accuracy],
    ['Priority accuracy', result.before?.priority.test.accuracy, result.after.priority.test.accuracy],
    ['Agrees with officers (department)', result.after.feedback.officer_agreement_before?.department, result.after.feedback.officer_agreement_after?.department],
    ['Agrees with officers (category)', result.after.feedback.officer_agreement_before?.category, result.after.feedback.officer_agreement_after?.category],
  ]
  return (
    <Section title="Learn from officer decisions" icon={RefreshCw}>
      <p className="text-sm text-slate-600">
        Model v{info?.model_version ?? '-'} · {info?.total_officer_labels ?? '-'} officer-reviewed complaints · {info?.new_labels_since_last_run ?? '-'} new overrides since the last run
      </p>
      {highlight && !result && <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">Your override was saved as a training label. Retrain to teach the model.</p>}
      <button className="btn-primary mt-3 w-full" onClick={retrain} disabled={busy}>
        {busy ? <Spinner /> : <RefreshCw className="h-4 w-4" />} {busy ? 'Retraining (about a minute)...' : 'Retrain model now'}
      </button>
      <div className="mt-2">
        <ErrorBox message={error} />
      </div>
      {result && (
        <div className="mt-3">
          <div className="text-xs font-semibold text-slate-700">
            v{result.before?.version} → v{result.after.version} · {result.after.feedback.labels_used} officer labels · {result.after.train_seconds}s
          </div>
          <table className="mt-2 w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="py-1 font-medium">Held-out metric</th>
                <th className="py-1 text-right font-medium">Before</th>
                <th className="py-1 text-right font-medium">After</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {rows.map(([k, a, b]) => (
                <tr key={k} className="border-t border-slate-100">
                  <td className="py-1 text-slate-700">{k}</td>
                  <td className="py-1 text-right">{pct(a)}</td>
                  <td className="py-1 text-right font-semibold text-slate-900">{pct(b)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {compact || !info?.runs?.length ? null : (
        <p className="mt-2 text-xs text-slate-500">Last run: v{info.runs[0].version} with {info.runs[0].labels_used} labels.</p>
      )}
    </Section>
  )
}

export default function ComplaintDetail() {
  const { id } = useParams()
  const [c, setC] = useState(null)
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState('')
  const [overrode, setOverrode] = useState(false)

  const load = useCallback(async () => {
    try {
      setError('')
      setC((await api.get(`/complaints/${id}`)).data)
    } catch (err) {
      setError(errorMessage(err))
    }
  }, [id])

  useEffect(() => {
    setC(null)
    setOverrode(false)
    load()
  }, [load])
  useEffect(() => {
    api.get('/meta').then((r) => setMeta(r.data)).catch(() => {})
  }, [])
  // poll while the Gemini extraction is running
  useEffect(() => {
    if (c?.extraction_status !== 'pending') return
    const t = setTimeout(load, 2500)
    return () => clearTimeout(t)
  }, [c, load])

  if (error && !c) return <ErrorBox message={error} onRetry={load} />
  if (!c) return <Loading label="Loading complaint and explanations..." />
  const ex = c.ai.explanations || {}

  return (
    <div>
      <Link to="/queue" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to queue
      </Link>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <h1 className="font-mono text-xl font-semibold text-slate-900">{c.tracking_id}</h1>
        <StatusBadge status={c.status} />
        <PriorityBadge priority={c.current.priority} />
        <SampleBadge show={c.is_sample} />
      </div>
      <div className="mt-2">
        <ErrorBox message={error} onRetry={load} />
      </div>

      <div className="mt-4 grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div className="space-y-5">
          <Section title="Complaint" icon={User}>
            <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
              <span>{c.citizen}</span>
              <span>{fmtDate(c.created_at)}</span>
              <span>{c.language}</span>
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" /> {c.ward || 'No location'}
              </span>
            </div>
            <p className="whitespace-pre-line text-[15px] leading-relaxed text-slate-800">{c.text}</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {c.photo_url && <img src={c.photo_url} alt="Complaint" className="h-44 w-full rounded-lg border border-slate-200 object-cover" />}
              {c.lat != null && (
                <div className="h-44 overflow-hidden rounded-lg border border-slate-200">
                  <MapContainer center={[c.lat, c.lng]} zoom={15} className="h-full w-full" scrollWheelZoom={false}>
                    <BaseTiles />
                    <CircleMarker center={[c.lat, c.lng]} radius={8} pathOptions={{ color: '#fff', weight: 2, fillColor: '#d03b3b', fillOpacity: 1 }} />
                  </MapContainer>
                </div>
              )}
            </div>
          </Section>

          <Extraction c={c} onDone={load} />

          <Section title="Why the AI suggested this" icon={Brain} right={<span className="text-xs text-slate-400">model v{c.ai.explained_with_version || c.ai.model_version}</span>}>
            <div className="space-y-6">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Words that drove the category (LIME)</h3>
                <p className="mb-2 text-xs text-slate-500">
                  Suggested <b className="text-slate-700">{c.ai.category}</b> ({pct(c.ai.category_confidence)})
                </p>
                <CategoryWords words={ex.category_words} category={c.ai.category} />
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Factors behind the priority (SHAP)</h3>
                <p className="mb-2 text-xs text-slate-500">
                  Suggested <b className="text-slate-700">{c.ai.priority}</b> ({pct(c.ai.priority_confidence)})
                </p>
                <PriorityFactors data={ex.priority_factors} />
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Factors behind the time estimate (SHAP)</h3>
                <p className="mb-2 text-xs text-slate-500">
                  Expected <b className="text-slate-700">~{days(c.ai.expected_days)}</b>, learned from real service-request resolution times
                </p>
                <TimeFactors data={ex.time_factors} />
              </div>
            </div>
          </Section>

          <Section title="Activity" icon={RefreshCw}>
            <ol className="space-y-3 text-sm">
              {c.events.map((e, i) => (
                <li key={i} className="flex gap-3">
                  <span className="w-28 shrink-0 text-xs text-slate-400">{fmtDate(e.at)}</span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      {e.kind === 'status' ? <StatusBadge status={e.status} /> : <span className="font-semibold capitalize text-slate-700">{e.kind}</span>}
                      {!e.public && <span className="rounded bg-slate-100 px-1.5 text-[10px] uppercase text-slate-500">internal</span>}
                      {e.actor && <span className="text-slate-500">{e.actor}</span>}
                    </div>
                    {e.message && <p className="mt-0.5 whitespace-pre-line text-slate-700">{e.message}</p>}
                  </div>
                </li>
              ))}
            </ol>
          </Section>
        </div>

        <div className="space-y-5">
          <Suggestion
            c={c}
            meta={meta}
            onSaved={(hadOverride) => {
              if (hadOverride) setOverrode(true)
              load()
            }}
          />
          <StatusActions c={c} onSaved={load} />
          <ReplyBox c={c} onSent={load} />
          <RetrainPanel highlight={overrode} compact />
        </div>
      </div>
    </div>
  )
}
