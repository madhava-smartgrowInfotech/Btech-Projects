import { FileSearch, RefreshCw, Sparkles, UserRound } from 'lucide-react'
import { lazy, Suspense, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { describeError, useApi } from '../api'
import { EvidenceTimeline, TaxpayerHeader } from '../components/domain/blocks'
import Markdown from '../components/domain/Markdown'
import { FadeIn } from '../components/motion'
import { Button } from '../components/ui/controls'
import { Badge, Card, KeyValueList } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton, Skeleton, useToast } from '../components/ui/feedback'
import { Breadcrumbs } from '../components/ui/nav'
import Typewriter from '../components/ui/Typewriter'
import { pct, stamp } from '../format'
import { logEvent } from '../lib/activity'

const GraphView = lazy(() => import('../components/domain/GraphView'))

function Quality({ q }) {
  return (
    <div className="mt-5 border-t border-line pt-3">
      <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.14em] text-dim">Grounding checks</div>
      <KeyValueList cols={2} items={[
        ['Citations', q.citations],
        ['Invalid citations', <span key="i" className={q.invalid_citations ? 'text-alert' : 'text-ok'}>{q.invalid_citations}</span>],
        ['Evidence covered', q.evidence_coverage === null ? '-' : pct(q.evidence_coverage)],
        ['High-severity covered', q.high_severity_coverage === null ? '-' : pct(q.high_severity_coverage)],
        ['Numbers traced to evidence', `${q.numbers_grounded}/${q.numbers}`],
        ['All three sections', q.has_sections ? 'yes' : <span key="s" className="text-warn">no</span>],
      ]} />
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
  const toast = useToast()

  useEffect(() => { if (data) setExpl(data.explanation) }, [data])

  async function generate() {
    setBusy(true)
    setExplError(null)
    logEvent('ui', `requesting case note for ${gstin}`)
    try {
      const r = await api.post(`/explanations/${gstin}`)
      setExpl(r.data)
      toast({ tone: 'ok', title: 'Case note written', body: `${r.data.model} · ${r.data.quality.citations} citations, ${r.data.quality.invalid_citations} invalid` })
    } catch (e) {
      const d = describeError(e)
      setExplError(d)
      toast({ tone: 'alert', title: 'Explanation failed', body: d.message })
    } finally {
      setBusy(false)
    }
  }
  function cite(id) {
    setActive(id)
    document.getElementById(`case-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  const crumbs = [{ label: 'Taxpayers', to: '/app/taxpayers' }, { label: data?.taxpayer.legal_name || gstin, to: `/app/taxpayers/${gstin}` }, { label: 'Case' }]
  if (error) return <div className="space-y-4"><Breadcrumbs items={crumbs} /><ErrorState error={error} onRetry={reload} title={`Could not load the case for ${gstin}`} /></div>
  if (loading && !data) return <PageSkeleton />
  const t = data.taxpayer
  const noEvidence = data.evidence.length === 0

  return (
    <div className="space-y-5">
      <Breadcrumbs items={crumbs} />
      <TaxpayerHeader t={t}>
        <Link to={`/app/taxpayers/${gstin}`} className="inline-flex h-9 items-center gap-2 rounded-[6px] border border-line-strong bg-panel-2 px-3.5 text-sm text-fg hover:border-ok/60 hover:text-ok">
          <UserRound size={16} /> Profile
        </Link>
      </TaxpayerHeader>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-5">
        <Card title="Written explanation" className="xl:col-span-3"
          action={expl && <Button variant="secondary" size="sm" icon={RefreshCw} loading={busy} onClick={generate}>Regenerate</Button>}>
          {busy && !expl && (
            <div className="space-y-3" aria-live="polite">
              <Typewriter text="> gemini is writing the case note from the evidence list…" className="font-mono text-xs text-ok" keepCaret />
              {['w-1/3', 'w-full', 'w-11/12', 'w-1/4', 'w-full', 'w-5/6', 'w-10/12'].map((w, i) => <Skeleton key={i} className={`h-3.5 ${w}`} />)}
            </div>
          )}
          {!expl && !busy && (
            <EmptyState icon={FileSearch} title={noEvidence ? 'Nothing to explain' : 'No case note yet'}
              body={noEvidence ? 'No evidence was recorded for this taxpayer, so there is nothing to cite.'
                : `Turn the ${data.evidence.length} evidence items into an investigator-style case note. Every claim cites its evidence ID.`}
              action={!noEvidence && <Button icon={Sparkles} onClick={generate}>Write explanation</Button>} />
          )}
          {explError && <div className="mt-3"><ErrorState error={explError} title="Gemini request failed" onRetry={generate} /></div>}
          {expl && (
            <FadeIn key={expl.created_at} className={busy ? 'opacity-50 transition-opacity' : ''}>
              <Markdown text={expl.text} onCite={cite} />
              <Quality q={expl.quality} />
              <p className="mt-3 flex flex-wrap items-center gap-2 font-mono text-[10px] text-dim">
                <Badge tone="info">{expl.model}</Badge> written {stamp(expl.created_at)} from the evidence list only · a risk indication for review, not a finding
              </p>
            </FadeIn>
          )}
        </Card>
        <Card title={`Evidence (${data.evidence.length})`} className="xl:col-span-2" bodyClass="p-4 xl:max-h-[720px] xl:overflow-y-auto">
          <EvidenceTimeline evidence={data.evidence} active={active} idPrefix="case" />
        </Card>
      </div>

      <Card title="Network evidence">
        {graph.error ? <ErrorState error={graph.error} onRetry={graph.reload} title="Could not load the network" />
          : !graph.data ? <Skeleton className="h-[420px]" />
            : <Suspense fallback={<Skeleton className="h-[420px]" />}><GraphView data={graph.data} height={420} /></Suspense>}
      </Card>
    </div>
  )
}
