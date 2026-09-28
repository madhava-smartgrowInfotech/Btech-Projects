import { ArrowLeft, Loader2, RefreshCw, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { errorMessage, useApi } from '../api'
import GraphView from '../components/GraphView'
import Markdown from '../components/Markdown'
import { Button, Card, ErrorBox, Loading, Severity } from '../components/ui'
import { TaxpayerHeader } from './TaxpayerProfile'

function Quality({ q }) {
  const items = [
    ['Citations', q.citations],
    ['Invalid citations', q.invalid_citations],
    ['Evidence covered', q.evidence_coverage === null ? '-' : `${Math.round(q.evidence_coverage * 100)}%`],
    ['High-severity covered', q.high_severity_coverage === null ? '-' : `${Math.round(q.high_severity_coverage * 100)}%`],
    ['Numbers traced to evidence', `${q.numbers_grounded}/${q.numbers}`],
  ]
  return (
    <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 border-t border-slate-100 pt-3 text-xs text-slate-500">
      {items.map(([k, v]) => <span key={k}>{k}: <b className="text-slate-700">{v}</b></span>)}
    </div>
  )
}

export default function CaseDetail() {
  const { gstin } = useParams()
  const { data, error, loading, reload } = useApi(`/taxpayers/${gstin}`)
  const graph = useApi(`/graph?focus=${gstin}`)
  const [expl, setExpl] = useState(null)
  const [busy, setBusy] = useState(false)
  const [explError, setExplError] = useState(null)
  const [active, setActive] = useState(null)

  useEffect(() => { if (data) setExpl(data.explanation) }, [data])

  async function generate() {
    setBusy(true)
    setExplError(null)
    try {
      const r = await api.post(`/explanations/${gstin}`)
      setExpl(r.data)
    } catch (e) {
      setExplError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  function cite(id) {
    setActive(id)
    document.getElementById(`ev-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  if (loading && !data) return <Loading />
  if (error) return <ErrorBox error={error} onRetry={reload} />
  const t = data.taxpayer
  return (
    <div className="space-y-5">
      <Link to={`/app/taxpayers/${gstin}`} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"><ArrowLeft size={15} /> Profile</Link>
      <TaxpayerHeader t={t} />
      <div className="grid lg:grid-cols-5 gap-5">
        <Card title="Written explanation" className="lg:col-span-3"
          action={expl && <Button variant="secondary" onClick={generate} disabled={busy}>{busy ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} Regenerate</Button>}>
          {busy && !expl && <Loading label="Gemini is writing the case note…" />}
          {!expl && !busy && (
            <div className="py-6 text-center">
              <p className="text-sm text-slate-600 mb-3">Turn the {data.evidence.length} evidence items into an investigator-style case note. Every claim cites its evidence ID.</p>
              <Button onClick={generate}><Sparkles size={16} /> Write explanation</Button>
            </div>
          )}
          <ErrorBox error={explError} />
          {expl && (
            <div className={busy ? 'opacity-50' : ''}>
              <Markdown text={expl.text} onCite={cite} />
              <Quality q={expl.quality} />
              <p className="mt-1 text-[11px] text-slate-400">Written by {expl.model} on {new Date(expl.created_at).toLocaleString()} from the evidence list only. A risk indication for review, not a finding.</p>
            </div>
          )}
        </Card>
        <Card title="Evidence" className="lg:col-span-2">
          <ul className="space-y-2">
            {data.evidence.map((e) => (
              <li key={e.id} id={`ev-${e.id}`}
                className={`rounded-lg border p-3 text-sm transition-colors ${active === e.id ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200'}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-indigo-700">{e.id}</span>
                  <span className="font-medium text-slate-800">{e.title}</span>
                  <Severity s={e.severity} />
                  <span className="text-[11px] text-slate-400">{e.layer} layer</span>
                </div>
                <p className="mt-1 text-xs text-slate-600">{e.detail}</p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <Card title="Network evidence">
        {graph.loading && !graph.data ? <Loading /> : graph.error ? <ErrorBox error={graph.error} onRetry={graph.reload} /> : <GraphView data={graph.data} height={420} />}
      </Card>
    </div>
  )
}
