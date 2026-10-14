import { Activity, Crosshair, Gauge, Target } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts'
import { useApi } from '../api'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../components/ui/charts'
import { Card, KeyValueList, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { fixed, num, pct } from '../format'

const ROLE = { circular_trading: 'Circular trading', shell_entity: 'Shell entities', fake_invoice_buyer: 'Fake-invoice buyers', itc_spike: 'ITC spikes' }

function CompareBars({ rows, label }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  const h = Math.max(150, rows.length * 46 + 30)
  return (
    <>
      <ChartFrame height={h} label={label}>
        {({ width, height }) => (
          <BarChart layout="vertical" width={width} height={height} data={rows} margin={{ top: 4, right: 12, bottom: 0, left: 4 }} barGap={2} barCategoryGap="28%">
            <CartesianGrid {...grid} horizontal={false} />
            <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} {...axis} />
            <YAxis type="category" dataKey="label" {...axis} width={112} />
            <Tooltip cursor={false} isAnimationActive={false} content={<MonoTooltip valueFormat={(v) => fixed(v, 3)} />} />
            <Bar dataKey="model" name="TaxSentinel" fill={tokens.ok} radius={[0, 2, 2, 0]} isAnimationActive={animate} maxBarSize={12} />
            <Bar dataKey="baseline" name="Rule baseline" fill={tokens.dim} radius={[0, 2, 2, 0]} isAnimationActive={animate} maxBarSize={12} />
          </BarChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'TaxSentinel', color: 'var(--ok)' }, { label: 'Rule baseline', color: 'var(--dim)' }]} />
    </>
  )
}

function LossCurve({ h }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  const rows = h.map((v, i) => ({ epoch: i + 1, loss: v }))
  return (
    <ChartFrame height={200} label="JEPA training loss per epoch">
      {({ width, height }) => (
        <LineChart width={width} height={height} data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid {...grid} />
          <XAxis dataKey="epoch" {...axis} minTickGap={20} />
          <YAxis {...axis} width={46} tickFormatter={(v) => v.toFixed(2)} />
          <Tooltip cursor={false} isAnimationActive={false} content={<MonoTooltip labelFormat={(l) => `epoch ${l}`} valueFormat={(v) => fixed(v, 4)} />} />
          <Line type="monotone" dataKey="loss" name="loss" stroke={tokens.ok} strokeWidth={1.4} dot={false} isAnimationActive={animate} />
        </LineChart>
      )}
    </ChartFrame>
  )
}

export default function Performance() {
  const { data, error, loading, reload } = useApi('/metrics')
  if (error) return <ErrorState error={error} onRetry={reload} title="Could not load the evaluation" />
  if (loading && !data) return <PageSkeleton />
  const ev = data.current.evaluation
  const tp = ev.taxpayer
  const ks = ev.ks.map(String)
  const kMax = ks[ks.length - 1]
  const tr = data.current.train_info || {}
  const report = data.eval_report
  const kSeries = ks.map((k) => ({ k, p: tp.model.precision_at_k[k], r: tp.model.recall_at_k[k] }))
  const patterns = Object.entries(ev.per_pattern).map(([k, v]) => ({ label: `${ROLE[k] || k} (${v.count})`, model: v.model_recall, baseline: v.baseline_recall }))
  const methods = [
    { name: 'TaxSentinel (all layers)', r: tp.model, strong: true },
    { name: 'Rule baseline (any of R1-R5)', r: tp.rule_baseline },
    { name: 'Ablation: JEPA only', r: tp.ablation.jepa_only },
    { name: 'Ablation: graph + invoice only', r: tp.ablation.graph_and_invoice_only },
    { name: 'Ablation: without invoice layer', r: tp.ablation.without_invoice_layer },
  ]
  const m3 = (v) => <span className="font-mono text-xs tabular-nums">{v === null || v === undefined ? '-' : v.toFixed(3)}</span>
  const methodCols = [
    { key: 'name', label: 'Method', render: (m) => <span className={m.strong ? 'font-medium text-ok' : 'text-fg'}>{m.name}</span> },
    { key: 'p', label: 'Precision', align: 'right', sortable: true, sortValue: (m) => m.r.at_threshold?.precision ?? -1, render: (m) => m3(m.r.at_threshold?.precision) },
    { key: 'rc', label: 'Recall', align: 'right', sortable: true, sortValue: (m) => m.r.at_threshold?.recall ?? -1, render: (m) => m3(m.r.at_threshold?.recall) },
    { key: 'f1', label: 'F1', align: 'right', sortable: true, sortValue: (m) => m.r.at_threshold?.f1 ?? -1, render: (m) => m3(m.r.at_threshold?.f1) },
    { key: 'auc', label: 'ROC-AUC', align: 'right', sortable: true, sortValue: (m) => m.r.roc_auc ?? -1, render: (m) => m3(m.r.roc_auc) },
    { key: 'ap', label: 'Avg precision', align: 'right', sortable: true, sortValue: (m) => m.r.average_precision ?? -1, render: (m) => m3(m.r.average_precision) },
  ]
  const ia = ev.invoice.model.at_threshold, ib = ev.invoice.rule_baseline.at_threshold
  return (
    <div className="space-y-5">
      <PageHeader eyebrow="// evaluation" title="Model performance"
        subtitle={`Current ecosystem (seed ${data.current.seed}): ${ev.n_fraud} injected-fraud taxpayers of ${ev.n_taxpayers}. Scored against generator labels; the model never sees them.`} />
      <Stagger className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Target} label={`Precision@${kMax}`} value={tp.model.precision_at_k[kMax]} format={(v) => pct(v, 1)} sub={`rules ${pct(tp.rule_baseline.precision_at_k[kMax], 1)}`} spark={kSeries} sparkKey="p" sparkLabel={`precision @ k = ${ks.join(' / ')}`} />
        <StatCard icon={Crosshair} label={`Recall@${kMax}`} value={tp.model.recall_at_k[kMax]} format={(v) => pct(v, 1)} sub={`rules ${pct(tp.rule_baseline.recall_at_k[kMax], 1)}`} spark={kSeries} sparkKey="r" sparkLabel={`recall @ k = ${ks.join(' / ')}`} tone="cyan" />
        <StatCard icon={Gauge} label="F1 at threshold" value={tp.model.at_threshold.f1} format={(v) => v.toFixed(3)} sub={`rules ${tp.rule_baseline.at_threshold.f1.toFixed(3)} · ROC-AUC ${fixed(tp.model.roc_auc, 3)}`} spark={patterns} sparkKey="model" sparkLabel="recall per fraud pattern" tone="info" />
        <StatCard icon={Activity} label="JEPA final loss" value={tr.final_loss ?? null} format={(v) => v.toFixed(4)} sub={`${num(tr.samples)} taxpayer-months · ${tr.epochs} epochs`} spark={(tr.loss_history || []).map((v, i) => ({ i, v }))} sparkKey="v" sparkLabel="training loss / epoch" tone="warn" />
      </Stagger>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Card title="Precision@k · how many of the top-k are real fraud">
          <CompareBars label="Precision at k" rows={ks.map((k) => ({ label: `Top ${k}`, model: tp.model.precision_at_k[k], baseline: tp.rule_baseline.precision_at_k[k] }))} />
        </Card>
        <Card title="Recall@k · share of all fraud found in the top-k">
          <CompareBars label="Recall at k" rows={ks.map((k) => ({ label: `Top ${k}`, model: tp.model.recall_at_k[k], baseline: tp.rule_baseline.recall_at_k[k] }))} />
        </Card>
      </div>
      <Card title="Taxpayer-level detection">
        <Table columns={methodCols} rows={methods} rowKey={(m) => m.name} caption="Detection metrics by method" />
        <p className="mt-3 font-mono text-[11px] text-muted">
          model flags at risk ≥ {data.config.flag_threshold}: {tp.model.at_threshold.flagged} flagged ({tp.model.at_threshold.tp} true, {tp.model.at_threshold.fp} false) ·
          rule baseline flags {tp.rule_baseline.at_threshold.flagged} ({tp.rule_baseline.at_threshold.fp} false alarms)
        </p>
      </Card>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Card title="Recall by fraud pattern (at threshold)"><CompareBars label="Recall per fraud pattern" rows={patterns} /></Card>
        <Card title="Invoices, rings and chains">
          <KeyValueList items={[
            ['Invoice flags: precision / recall / F1', `${ia.precision.toFixed(2)} / ${ia.recall.toFixed(2)} / ${ia.f1.toFixed(2)}`],
            ['Rule "not in supplier GSTR-1": P / R / F1', `${ib.precision.toFixed(2)} / ${ib.recall.toFixed(2)} / ${ib.f1.toFixed(2)}`],
            ['Invoice ROC-AUC', fixed(ev.invoice.model.roc_auc, 4)],
            ['Injected rings recovered', `${ev.rings.recovered} / ${ev.rings.injected}`],
            ['Loops detected (with / without fraud members)', `${ev.rings.detected_with_fraud_members} / ${ev.rings.detected_without_fraud_members}`],
            ['Top-10 invoice chains that are fraud', pct(ev.chains.precision_top10)],
          ]} />
        </Card>
      </div>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Card title="JEPA encoder training">
          <p className="mb-3 font-mono text-[11px] text-muted">{num(tr.samples)} taxpayer-months · {tr.epochs} epochs · window {tr.window} months · {tr.train_seconds}s on CPU · final loss {tr.final_loss}</p>
          {tr.loss_history ? <LossCurve h={tr.loss_history} /> : <EmptyState title="No loss history" body="The loaded model was not trained in this run." />}
        </Card>
        <Card title="Explanation quality · evaluation report">
          {report?.explanations?.evaluated ? (
            <KeyValueList items={Object.entries(report.explanations.summary).map(([k, v]) => [k.replace(/_/g, ' '), typeof v === 'number' ? v.toFixed(3) : String(v)])} />
          ) : <EmptyState title="No explanation report" body={report?.explanations?.note || 'Run python -m ml.eval to produce the evaluation report.'} />}
          {report?.paysim && (
            <p className="mt-3 rounded-[6px] border border-line bg-panel-2 p-2.5 font-mono text-[11px] text-muted">
              PaySim transfer check ({num(report.paysim.rows)} transactions): JEPA ROC-AUC <span className="text-ok">{report.paysim.roc_auc}</span>, precision@100 {report.paysim.precision_at_k?.['100']}
            </p>
          )}
        </Card>
      </div>
    </div>
  )
}
