import { useMemo, useState } from 'react'
import { Activity, Bot, Building2, Download, FileText, HeartPulse, Languages, Send, Sparkles } from 'lucide-react'
import api, { downloadBundle, errMsg } from '../api'
import { Badge, Button, CATEGORY_COLOR, Card, Disclaimer, ErrorBox, HOSPITAL_COLOR, RichText, Select, Spinner, fmtDate } from './ui'

export function SourcesBar({ record, personId }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const download = async () => {
    setBusy(true); setError(null)
    try { await downloadBundle(personId) } catch (e) { setError(e) } finally { setBusy(false) }
  }
  return (
    <Card title="Record sources (Master Patient Index)" icon={Building2}
      actions={<Button variant="secondary" loading={busy} onClick={download}><Download className="w-4 h-4" /> FHIR bundle</Button>}>
      <ErrorBox error={error} />
      <div className="grid sm:grid-cols-3 gap-3">
        {record.sources.map((s) => (
          <div key={s.hospital} className="rounded-lg border border-slate-200 p-3">
            <div className="flex items-center justify-between gap-2">
              <Badge color={HOSPITAL_COLOR[s.hospital]}>{s.name}</Badge>
              <span className={`text-xs ${s.status === 'online' ? 'text-emerald-600' : 'text-amber-600'}`}>{s.status === 'online' ? '● online' : '● offline'}</span>
            </div>
            <div className="mt-2 text-xs text-slate-500">Local ID <span className="font-mono text-slate-700">{s.local_id}</span></div>
            <div className="text-xs text-slate-500">Match confidence <span className="font-semibold text-slate-700">{Math.round(s.confidence * 100)}%</span></div>
            <div className="text-xs text-slate-500">{Object.values(s.counts).reduce((a, b) => a + b, 0)} FHIR resources</div>
            {s.status !== 'online' && <div className="text-xs text-amber-700 mt-1">{s.status}</div>}
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2 mt-3 text-xs">
        {Object.entries(record.counts).map(([c, n]) => <Badge key={c} color={CATEGORY_COLOR[c]}>{c}: {n}</Badge>)}
      </div>
    </Card>
  )
}

export function Timeline({ items, onExplain }) {
  const [cat, setCat] = useState('all')
  const [hosp, setHosp] = useState('all')
  const [q, setQ] = useState('')
  const [limit, setLimit] = useState(60)
  const cats = [...new Set(items.map((i) => i.category))]
  const shown = useMemo(() => items.filter((i) =>
    (cat === 'all' || i.category === cat) && (hosp === 'all' || i.hospital === hosp) &&
    (!q || `${i.title} ${i.value}`.toLowerCase().includes(q.toLowerCase()))), [items, cat, hosp, q])
  return (
    <Card title="Unified timeline" icon={Activity}>
      <div className="flex flex-wrap gap-2 mb-3">
        {['all', ...cats].map((c) => (
          <button key={c} onClick={() => setCat(c)}
            className={`rounded-full px-3 py-1 text-xs border capitalize ${cat === c ? 'bg-teal-600 text-white border-teal-600' : 'border-slate-300 text-slate-600 hover:bg-slate-50'}`}>{c}</button>
        ))}
        <select value={hosp} onChange={(e) => setHosp(e.target.value)} className="rounded-full border border-slate-300 px-2 py-1 text-xs bg-white">
          <option value="all">All hospitals</option>
          {[...new Set(items.map((i) => i.hospital))].sort().map((h) => <option key={h} value={h}>{items.find((i) => i.hospital === h).hospital_name}</option>)}
        </select>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search..." className="rounded-full border border-slate-300 px-3 py-1 text-xs flex-1 min-w-32" />
      </div>
      {shown.length === 0 && <p className="text-sm text-slate-500 py-4 text-center">No entries match.</p>}
      <ol className="divide-y divide-slate-100">
        {shown.slice(0, limit).map((i) => (
          <li key={`${i.type}-${i.id}`} className="py-2 flex flex-wrap sm:flex-nowrap gap-x-3 gap-y-1 items-start">
            <div className="w-24 shrink-0 text-xs text-slate-500 pt-0.5">{fmtDate(i.date)}</div>
            <div className="w-24 shrink-0"><Badge color={CATEGORY_COLOR[i.category]}>{i.type === 'DiagnosticReport' ? 'report' : i.category}</Badge></div>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-slate-800">{i.title || i.type}</div>
              {i.value && <div className="text-xs text-slate-500">{i.value}</div>}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {i.status && <span className="text-xs text-slate-400">{i.status}</span>}
              <Badge color={HOSPITAL_COLOR[i.hospital]}>{i.hospital_name.split(' ')[0]}</Badge>
              {onExplain && i.type === 'DiagnosticReport' && (
                <button onClick={() => onExplain(i)} className="text-xs text-teal-700 hover:underline flex items-center gap-1"><Sparkles className="w-3 h-3" />Explain</button>
              )}
            </div>
          </li>
        ))}
      </ol>
      {shown.length > limit && (
        <div className="text-center pt-3"><Button variant="ghost" onClick={() => setLimit(limit + 100)}>Show more ({shown.length - limit} left)</Button></div>
      )}
    </Card>
  )
}

function RiskGauge({ title, result }) {
  const pct = Math.round(result.probability * 100)
  const color = { high: 'bg-rose-500', moderate: 'bg-amber-500', low: 'bg-emerald-500' }[result.level]
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-slate-800">{title}</h3>
        <Badge color={{ high: 'rose', moderate: 'amber', low: 'green' }[result.level]}>{result.level} risk</Badge>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <div className="flex-1 h-2.5 rounded-full bg-slate-100 overflow-hidden"><div className={`h-full ${color}`} style={{ width: `${pct}%` }} /></div>
        <span className="text-lg font-semibold text-slate-800 w-12 text-right">{pct}%</span>
      </div>
      <div className="mt-3 text-xs font-medium text-slate-600">Top factors in this record</div>
      <ul className="mt-1 space-y-1">
        {result.top_factors.map((f) => (
          <li key={f.feature} className="text-sm flex flex-wrap justify-between gap-2">
            <span>{f.label}: <span className="font-medium">{f.value}</span> <span className="text-xs text-slate-400">{f.date ? fmtDate(f.date) : ''}</span></span>
            <span className={`text-xs ${f.impact > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>{f.direction} ({f.impact > 0 ? '+' : ''}{Math.round(f.impact * 100)} pts)</span>
          </li>
        ))}
        {result.top_factors.length === 0 && <li className="text-xs text-slate-500">No usable values in the record - population medians used.</li>}
      </ul>
      {result.inputs.some((u) => !u.from_record) && (
        <div className="text-xs text-slate-400 mt-2">Not in record (median used): {result.inputs.filter((u) => !u.from_record).map((u) => u.label).join(', ')}</div>
      )}
    </div>
  )
}

export function RiskPanel({ personId }) {
  const [state, setState] = useState({ loading: false, error: null, data: null })
  const run = async () => {
    setState({ loading: true, error: null, data: null })
    try { setState({ loading: false, error: null, data: (await api.get(`/risk/${personId}`)).data }) } catch (e) { setState({ loading: false, error: e, data: null }) }
  }
  return (
    <Card title="Health-risk prediction (Random Forest)" icon={HeartPulse}
      actions={<Button onClick={run} loading={state.loading}>{state.data ? 'Re-run' : 'Assess risk'}</Button>}>
      <ErrorBox error={state.error} />
      {!state.data && !state.loading && !state.error && <p className="text-sm text-slate-500">Scores heart-disease and diabetes risk from blood pressure, cholesterol, glucose, BMI, age and sex found in the unified record.</p>}
      {state.loading && <Spinner label="Scoring record..." />}
      {state.data && (
        <>
          <div className="grid md:grid-cols-2 gap-3">
            <RiskGauge title="Heart disease" result={state.data.heart} />
            <RiskGauge title="Type 2 diabetes" result={state.data.diabetes} />
          </div>
          <Disclaimer>{state.data.disclaimer}</Disclaimer>
        </>
      )}
    </Card>
  )
}

const LANGUAGES = ['English', 'Telugu', 'Hindi', 'Tamil', 'Kannada', 'Marathi', 'Bengali', 'Spanish', 'French']

export function AssistantPanel({ personId = 'me', report, onClearReport }) {
  const [language, setLanguage] = useState('English')
  const [question, setQuestion] = useState('')
  const [state, setState] = useState({ loading: null, error: null, data: null })
  const call = async (kind, body = {}) => {
    setState({ loading: kind, error: null, data: null })
    try {
      const r = await api.post(`/assistant/${kind}`, { person_id: personId, language, ...body })
      setState({ loading: null, error: null, data: r.data })
    } catch (e) { setState({ loading: null, error: errMsg(e), data: null }) }
  }
  return (
    <Card title="AI health assistant" icon={Bot}
      actions={<div className="flex items-center gap-1"><Languages className="w-4 h-4 text-slate-400" />
        <Select value={language} onChange={(e) => setLanguage(e.target.value)} className="w-32">{LANGUAGES.map((l) => <option key={l}>{l}</option>)}</Select></div>}>
      <div className="flex flex-wrap gap-2">
        {report ? (
          <>
            <Button loading={state.loading === 'explain'} onClick={() => call('explain', { report_id: report.id })}><FileText className="w-4 h-4" /> Explain {report.title} ({fmtDate(report.date)})</Button>
            <Button variant="ghost" onClick={onClearReport}>Clear</Button>
          </>
        ) : (
          <Button loading={state.loading === 'explain'} onClick={() => call('explain')}><FileText className="w-4 h-4" /> Explain latest lipid panel</Button>
        )}
        <Button variant="secondary" loading={state.loading === 'summary'} onClick={() => call('summary')}><Sparkles className="w-4 h-4" /> Summarise treatment</Button>
      </div>
      <form className="flex gap-2 mt-3" onSubmit={(e) => { e.preventDefault(); call('ask', { question }) }}>
        <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about your medicines, results or next steps..."
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
        <Button type="submit" loading={state.loading === 'ask'} disabled={!question.trim()}><Send className="w-4 h-4" /> Ask</Button>
      </form>
      <div className="mt-3">
        <ErrorBox error={state.error} />
        {state.loading && <Spinner label="Asking Gemini..." />}
        {state.data && (
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
            {state.data.title && <div className="text-xs text-slate-500 mb-1">{state.data.title}</div>}
            {state.data.values && <div className="flex flex-wrap gap-1 mb-2">{state.data.values.map((v) => <Badge key={v} color="teal">{v}</Badge>)}</div>}
            <RichText text={state.data.text} />
            <Disclaimer>{state.data.disclaimer}</Disclaimer>
          </div>
        )}
      </div>
    </Card>
  )
}
