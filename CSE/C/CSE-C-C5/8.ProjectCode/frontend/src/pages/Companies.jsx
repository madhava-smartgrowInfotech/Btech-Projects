import { Building2, Target } from 'lucide-react'
import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageHeader } from '../components/ui/AppShell'
import { Button, SearchField, Select } from '../components/ui/controls'
import { Badge, Card } from '../components/ui/display'
import { EmptyState, ErrorState } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { lpa, pct, TIER_TONE } from '../format'
import { useData } from '../lib/data'

const COLS = [
  { key: 'Company', label: 'Company', sortable: true, defaultDir: 'asc', render: (r) => <span className="font-medium text-fg">{r.Company}</span> },
  { key: 'Tier', label: 'Tier', sortable: true, defaultDir: 'asc', render: (r) => <Badge tone={TIER_TONE[r.Tier]}>tier {r.Tier}</Badge> },
  { key: 'Company_Type', label: 'Type', sortable: true, defaultDir: 'asc' },
  { key: 'CGPA_Cutoff', label: 'CGPA cut', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => r.CGPA_Cutoff.toFixed(1) },
  { key: 'Apt_Cutoff', label: 'Apt cut', sortable: true, align: 'right', className: 'font-mono tabular-nums' },
  { key: 'Tech_Cutoff', label: 'Tech cut', sortable: true, align: 'right', className: 'font-mono tabular-nums' },
  { key: 'Package_LPA', label: 'Package', sortable: true, align: 'right', className: 'font-mono tabular-nums text-fg', render: (r) => lpa(r.Package_LPA) },
  { key: 'Location', label: 'Location', sortable: true, defaultDir: 'asc' },
  { key: 'Hiring_Rate', label: 'Hiring rate', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => pct(r.Hiring_Rate, 0) },
  { key: 'act', label: '', align: 'right', render: (r) => (
    <Link to={`/predict?company=${encodeURIComponent(r.Company)}`} className="inline-flex items-center gap-1 font-mono text-[11px] uppercase text-ok hover:underline" aria-label={`Check eligibility for ${r.Company}`}>
      <Target size={12} aria-hidden="true" />check
    </Link>
  ) },
]

function CompanyCard({ r }) {
  return (
    <div className="panel p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium text-fg">{r.Company}</div>
          <div className="text-xs text-muted">{r.Location} · {r.Company_Type}</div>
        </div>
        <Badge tone={TIER_TONE[r.Tier]}>tier {r.Tier}</Badge>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-xs text-muted">
        <span>package <b className="text-fg">{lpa(r.Package_LPA)}</b></span><span>hiring {pct(r.Hiring_Rate, 0)}</span>
        <span>CGPA ≥ {r.CGPA_Cutoff.toFixed(1)}</span><span>apt ≥ {r.Apt_Cutoff} · tech ≥ {r.Tech_Cutoff}</span>
      </div>
      <Link to={`/predict?company=${encodeURIComponent(r.Company)}`} className="mt-2 inline-flex items-center gap-1 font-mono text-[11px] uppercase text-ok"><Target size={12} aria-hidden="true" />check eligibility</Link>
    </div>
  )
}

export default function Companies() {
  const { companies, error, reload } = useData()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') || ''
  const tier = params.get('tier') || ''
  const update = (k, v) => setParams((p) => { const n = new URLSearchParams(p); v ? n.set(k, v) : n.delete(k); return n }, { replace: true })

  const rows = useMemo(() => {
    if (!companies) return null
    const t = q.trim().toLowerCase()
    return companies.filter((c) => (!tier || String(c.Tier) === tier) && (!t || `${c.Company} ${c.Location} ${c.Company_Type}`.toLowerCase().includes(t)))
  }, [companies, q, tier])

  return (
    <div>
      <PageHeader eyebrow="Recruiting companies" title="Companies"
        subtitle="Every company the model knows: tier, eligibility cutoffs, package, location and historic hiring rate." />
      {error && !companies ? <ErrorState error={error} onRetry={reload} title="Could not load companies" /> : (
        <Card bodyClass="p-4">
          <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_180px]">
            <SearchField value={q} onChange={(v) => update('q', v)} placeholder="Search company, city or type" label="Search companies" shortcut="" />
            <Select srLabel="Filter by tier" value={tier} onChange={(e) => update('tier', e.target.value)} options={[['', 'All tiers'], ['1', 'Tier 1'], ['2', 'Tier 2'], ['3', 'Tier 3']]} />
          </div>
          <div aria-live="polite">
            <Table columns={COLS} rows={rows} loading={!companies} rowKey={(r) => r.Company} caption="Recruiting companies" pageSize={12}
              cards={(r) => <CompanyCard r={r} />} initialSort={{ key: 'Package_LPA', dir: 'desc' }}
              footer={rows ? `${rows.length} of ${companies.length} companies` : undefined}
              empty={<EmptyState icon={Building2} title="No company matches" body={`Nothing matches “${q}”${tier ? ` in tier ${tier}` : ''}. Clear the filters to see all companies.`}
                action={<Button variant="secondary" onClick={() => setParams({}, { replace: true })}>Clear filters</Button>} />} />
          </div>
        </Card>
      )}
    </div>
  )
}
