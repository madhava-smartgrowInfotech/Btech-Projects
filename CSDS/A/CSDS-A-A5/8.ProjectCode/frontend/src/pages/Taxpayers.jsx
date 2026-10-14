import { FilterX, SearchX } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useApi } from '../api'
import { TaxpayerLink } from '../components/domain/blocks'
import { PageHeader } from '../components/ui/AppShell'
import { Button, SearchField, Select } from '../components/ui/controls'
import { Card, PatternTag, RiskBadge } from '../components/ui/display'
import { EmptyState, ErrorState } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { inr, num, PATTERN_LABELS, riskVar, SECTORS } from '../format'

const PAGE = 25
const SORTS = [['risk', 'Sort: risk'], ['jepa', 'Sort: JEPA deviation'], ['network', 'Sort: network'], ['invoice', 'Sort: invoice'], ['itc', 'Sort: ITC at risk'], ['name', 'Sort: name']]
const score = (v) => <span className="font-mono text-xs tabular-nums" style={{ color: riskVar(v) }}>{v.toFixed(2)}</span>

export default function Taxpayers() {
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState(params.get('q') || '')
  const pattern = params.get('pattern') || ''
  const sector = params.get('sector') || ''
  const flagged = params.get('flagged') || ''
  const sort = params.get('sort') || 'risk'
  const page = Number(params.get('page') || 0)
  const set = (k, v) => {
    const p = new URLSearchParams(params)
    v ? p.set(k, v) : p.delete(k)
    if (k !== 'page') p.delete('page')
    setParams(p)
  }
  useEffect(() => {
    const t = setTimeout(() => { if ((params.get('q') || '') !== q) set('q', q) }, 350)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q])
  const qs = new URLSearchParams({ q: params.get('q') || '', pattern, sector, sort, limit: PAGE, offset: page * PAGE })
  if (flagged) qs.set('flagged', flagged)
  const { data, error, loading, reload } = useApi(`/taxpayers?${qs}`)
  const filtered = !!(params.get('q') || pattern || sector || flagged)
  const clear = () => { setQ(''); setParams(sort !== 'risk' ? { sort } : {}) }

  const columns = [
    { key: 'rank', label: '#', render: (t) => <span className="font-mono text-xs text-dim">{t.rank}</span> },
    { key: 'name', label: 'Taxpayer', sortable: true, render: (t) => <TaxpayerLink gstin={t.gstin} name={t.legal_name} /> },
    { key: 'sector', label: 'Sector', render: (t) => <span className="whitespace-nowrap text-xs text-muted">{SECTORS[t.sector]}</span> },
    { key: 'patterns', label: 'Patterns', render: (t) => <div className="flex flex-wrap gap-1">{t.patterns.map((p) => <PatternTag key={p} p={p} />)}</div> },
    { key: 'jepa', label: 'JEPA', align: 'right', sortable: true, render: (t) => score(Math.max(t.jepa, t.behaviour)) },
    { key: 'network', label: 'Network', align: 'right', sortable: true, render: (t) => score(t.network) },
    { key: 'invoice', label: 'Invoice', align: 'right', sortable: true, render: (t) => score(t.invoice) },
    { key: 'itc', label: 'ITC at risk', align: 'right', sortable: true, render: (t) => <span className="whitespace-nowrap font-mono text-xs">{inr(t.itc_at_risk)}</span> },
    { key: 'risk', label: 'Risk', align: 'right', sortable: true, render: (t) => <RiskBadge risk={t.risk} /> },
  ]
  // The API sorts one way per key (scores high→low, name A→Z)
  const activeSort = { key: sort, dir: sort === 'name' ? 'asc' : 'desc' }

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="// risk ranking" title="Taxpayers"
        subtitle="Ranked by combined risk from the JEPA deviation, network and invoice layers. Filters live in the URL, so a view can be shared." />
      <Card title={data ? `${num(data.total)} taxpayers${filtered ? ' match' : ''}` : 'Ranking'}
        action={filtered && <Button variant="ghost" size="sm" icon={FilterX} onClick={clear}>Clear filters</Button>}>
        <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_1fr_1fr]">
          <SearchField value={q} onChange={setQ} placeholder="Search name or GSTIN" label="Search taxpayers by name or GSTIN" className="sm:col-span-2 lg:col-span-1" />
          <Select srLabel="Pattern" value={pattern} onChange={(e) => set('pattern', e.target.value)} options={[['', 'All patterns'], ...Object.entries(PATTERN_LABELS)]} />
          <Select srLabel="Sector" value={sector} onChange={(e) => set('sector', e.target.value)} options={[['', 'All sectors'], ...Object.entries(SECTORS)]} />
          <Select srLabel="Flag status" value={flagged} onChange={(e) => set('flagged', e.target.value)} options={[['', 'Flagged + clear'], ['true', 'Flagged only'], ['false', 'Not flagged']]} />
          <Select srLabel="Sort by" value={sort} onChange={(e) => set('sort', e.target.value === 'risk' ? '' : e.target.value)} options={SORTS} />
        </div>
        {error ? <ErrorState error={error} onRetry={reload} title="Could not load the ranking" /> : (
          <Table columns={columns} rows={data?.items} rowKey={(t) => t.gstin} loading={loading} caption="Taxpayers ranked by risk"
            sort={activeSort} onSort={(k) => set('sort', k === 'risk' ? '' : k)}
            page={page} pageSize={PAGE} total={data?.total || 0} onPage={(p) => set('page', p ? String(p) : '')}
            footer={data && `showing ${data.total ? page * PAGE + 1 : 0}-${Math.min(data.total, (page + 1) * PAGE)} of ${num(data.total)}`}
            empty={<EmptyState icon={SearchX} title="No taxpayers match these filters" body="Try a shorter search or widen the pattern / sector filters." action={<Button variant="secondary" size="sm" icon={FilterX} onClick={clear}>Clear filters</Button>} />}
            cards={(t) => (
              <div className="rounded-[6px] border border-line bg-panel-2 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex min-w-0 gap-2"><span className="pt-0.5 font-mono text-xs text-dim">{t.rank}</span><TaxpayerLink gstin={t.gstin} name={t.legal_name} /></div>
                  <RiskBadge risk={t.risk} />
                </div>
                <div className="mt-2 flex flex-wrap gap-1">{t.patterns.map((p) => <PatternTag key={p} p={p} />)}</div>
                <div className="mt-2 grid grid-cols-4 gap-1 font-mono text-[10px] uppercase text-dim">
                  <span>jepa {score(Math.max(t.jepa, t.behaviour))}</span><span>net {score(t.network)}</span><span>inv {score(t.invoice)}</span>
                  <span className="text-right normal-case text-muted">{inr(t.itc_at_risk)}</span>
                </div>
              </div>
            )} />
        )}
      </Card>
    </div>
  )
}
