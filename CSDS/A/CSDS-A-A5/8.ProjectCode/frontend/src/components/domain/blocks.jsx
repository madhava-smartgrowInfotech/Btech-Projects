import { ArrowRight, FileCheck2, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { inr, SECTORS } from '../../format'
import { Badge, Card, PatternTag, RiskBadge, Severity, Timeline } from '../ui/display'
import { EmptyState } from '../ui/feedback'
import Table from '../ui/Table'
import Typewriter from '../ui/Typewriter'

export function TaxpayerLink({ gstin, name, sub = true }) {
  return (
    <span className="block min-w-0">
      <Link to={`/app/taxpayers/${gstin}`} className="block truncate font-medium text-fg hover:text-ok">{name}</Link>
      {sub && <span className="block font-mono text-[11px] text-dim">{gstin}</span>}
    </span>
  )
}

export function TaxpayerHeader({ t, children }) {
  return (
    <div className="panel scan p-5">
      <div className="relative z-[1] flex flex-wrap items-start justify-between gap-5">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            {t.flagged ? <Badge tone="alert" dot>Flagged</Badge> : <Badge tone="ok" dot>Not flagged</Badge>}
            <Badge>rank #{t.rank}</Badge>
            {t.patterns.map((p) => <PatternTag key={p} p={p} />)}
          </div>
          <Typewriter as="h1" text={t.legal_name} className="mt-2 text-xl font-semibold tracking-tight text-fg sm:text-2xl" />
          <div className="mt-1 font-mono text-sm text-ok">{t.gstin}</div>
          <div className="mt-2 text-sm text-muted">{SECTORS[t.sector] || t.sector} · {t.constitution} · {t.state} · registered {t.registration_date}</div>
          <div className="mt-0.5 font-mono text-[11px] text-dim">{t.address} · contact {t.contact_id}</div>
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-dim">Combined risk</div>
          <RiskBadge risk={t.risk} size="lg" />
          {children && <div className="mt-1 flex flex-wrap gap-2">{children}</div>}
        </div>
      </div>
    </div>
  )
}

const yes = (v) => (v ? <span className="text-muted">yes</span> : <span className="text-alert">no</span>)

export function InvoiceTable({ title, rows, footer }) {
  const columns = [
    { key: 'invoice_no', label: 'Invoice', render: (r) => <span className="font-mono text-xs text-fg">{r.invoice_no}</span>, sortable: true },
    { key: 'invoice_date', label: 'Date', sortable: true, defaultDir: 'asc', render: (r) => <span className="whitespace-nowrap font-mono text-xs">{r.invoice_date}</span> },
    {
      key: 'route', label: 'Seller → Buyer', render: (r) => (
        <span className="text-xs">
          <Link className="hover:text-ok" to={`/app/taxpayers/${r.seller_gstin}`}>{r.seller_name}</Link>
          <span className="mx-1 text-dim">→</span>
          <Link className="hover:text-ok" to={`/app/taxpayers/${r.buyer_gstin}`}>{r.buyer_name}</Link>
        </span>
      ),
    },
    { key: 'taxable_value', label: 'Value', align: 'right', sortable: true, render: (r) => <span className="whitespace-nowrap font-mono text-xs">{inr(r.taxable_value)}</span> },
    { key: 'tax_amount', label: 'Tax', align: 'right', sortable: true, render: (r) => <span className="whitespace-nowrap font-mono text-xs">{inr(r.tax_amount)}</span> },
    { key: 'eway_bill', label: 'E-way', render: (r) => <span className="font-mono text-xs">{yes(r.eway_bill)}</span> },
    { key: 'seller_reported', label: 'In GSTR-1', render: (r) => <span className="font-mono text-xs">{yes(r.seller_reported)}</span> },
    { key: 'flags', label: 'Signals', render: (r) => <span className="text-xs text-muted">{r.flags.map((f) => f.replace(/_/g, ' ')).join(', ') || '-'}</span> },
    { key: 'anomaly', label: 'Score', align: 'right', sortable: true, render: (r) => <RiskBadge risk={r.anomaly} /> },
  ]
  return (
    <Card title={title}>
      <Table columns={columns} rows={rows} rowKey={(r) => r.id} pageSize={15} dense footer={footer}
        empty={<EmptyState icon={FileCheck2} title="No anomalous invoices" body="None of this taxpayer's invoices scored above the invoice flag threshold." />}
        cards={(r) => (
          <div className="rounded-[6px] border border-line bg-panel-2 p-3 text-xs">
            <div className="flex items-center justify-between gap-2"><span className="font-mono text-fg">{r.invoice_no}</span><RiskBadge risk={r.anomaly} /></div>
            <div className="mt-1 text-muted">{r.seller_name} → {r.buyer_name}</div>
            <div className="mt-1 flex flex-wrap gap-x-3 font-mono text-dim">
              <span>{r.invoice_date}</span><span>{inr(r.taxable_value)}</span><span>tax {inr(r.tax_amount)}</span>
              <span>e-way {r.eway_bill ? 'yes' : 'no'}</span><span>GSTR-1 {r.seller_reported ? 'yes' : 'no'}</span>
            </div>
            {r.flags.length > 0 && <div className="mt-1 text-muted">{r.flags.map((f) => f.replace(/_/g, ' ')).join(', ')}</div>}
          </div>
        )} />
    </Card>
  )
}

export function ChainItem({ c }) {
  return (
    <Link to={`/app/chains/${c.id}`} className="group block rounded-[6px] border border-line bg-panel-2/60 p-3 transition-colors hover:border-ok/50">
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="font-mono text-sm text-fg group-hover:text-ok">{c.id}</span>
          <PatternTag p={c.type === 'circular_trading' ? 'circular_trading' : 'shell_entity'} />
        </div>
        <RiskBadge risk={c.score} />
      </div>
      <div className="mt-1.5 font-mono text-[11px] text-dim">{c.summary} · {inr(c.value)} · ITC {inr(c.itc)}</div>
      <div className="mt-1 flex items-center gap-1 truncate text-xs text-muted">
        <span className="truncate">{c.path.map((p) => p.legal_name).join(' → ')}</span>
        <ArrowRight size={12} className="shrink-0 text-dim group-hover:text-ok" aria-hidden="true" />
      </div>
    </Link>
  )
}

export function EvidenceTimeline({ evidence, active, idPrefix = 'ev' }) {
  if (!evidence.length) return <EmptyState icon={ShieldAlert} title="No evidence recorded" body="Nothing about this taxpayer crossed an evidence threshold in the current ecosystem." />
  return (
    <Timeline items={evidence.map((e) => ({
      id: e.id, anchor: `${idPrefix}-${e.id}`, tone: { high: 'alert', medium: 'warn', low: 'dim' }[e.severity],
      time: e.id, title: e.title,
      meta: <><Severity s={e.severity} /><Badge>{e.layer} layer</Badge></>,
      body: e.detail,
      className: active === e.id ? 'rounded-[6px] bg-ok/[0.07] ring-1 ring-ok/50 transition-colors' : 'transition-colors',
    }))} />
  )
}
