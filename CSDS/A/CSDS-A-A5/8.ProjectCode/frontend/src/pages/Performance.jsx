import { useApi } from '../api'
import { Card, ErrorBox, Loading, PageHeader } from '../components/ui'
import { pct } from '../format'

const ROLE = { circular_trading: 'Circular trading', shell_entity: 'Shell entities', fake_invoice_buyer: 'Fake-invoice buyers', itc_spike: 'ITC spikes' }

function Bars({ rows }) {
  // rows: [{label, model, baseline}]
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div key={r.label}>
          <div className="text-xs text-slate-600 mb-1">{r.label}</div>
          {[['TaxSentinel', r.model, 'bg-indigo-600'], ['Rule baseline', r.baseline, 'bg-slate-400']].map(([n, v, c]) => (
            <div key={n} className="flex items-center gap-2 text-xs">
              <span className="w-24 text-slate-500">{n}</span>
              <div className="flex-1 h-3 rounded bg-slate-100"><div className={`h-3 rounded ${c}`} style={{ width: `${(v ?? 0) * 100}%` }} /></div>
              <span className="w-12 text-right font-mono">{v === null || v === undefined ? '-' : v.toFixed(2)}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function Row({ name, r }) {
  return (
    <tr className="border-t border-slate-100">
      <td className="py-1.5 pr-3">{name}</td>
      <td className="py-1.5 pr-3 text-right font-mono">{r.at_threshold?.precision?.toFixed(3) ?? '-'}</td>
      <td className="py-1.5 pr-3 text-right font-mono">{r.at_threshold?.recall?.toFixed(3) ?? '-'}</td>
      <td className="py-1.5 pr-3 text-right font-mono">{r.at_threshold?.f1?.toFixed(3) ?? '-'}</td>
      <td className="py-1.5 pr-3 text-right font-mono">{r.roc_auc?.toFixed(3) ?? '-'}</td>
      <td className="py-1.5 text-right font-mono">{r.average_precision?.toFixed(3) ?? '-'}</td>
    </tr>
  )
}

export default function Performance() {
  const { data, error, loading, reload } = useApi('/metrics')
  if (loading && !data) return <Loading />
  if (error) return <ErrorBox error={error} onRetry={reload} />
  const ev = data.current.evaluation
  const tp = ev.taxpayer
  const ks = ev.ks.map(String)
  const tr = data.current.train_info || {}
  const report = data.eval_report
  return (
    <div className="space-y-5">
      <PageHeader title="Model performance"
        subtitle={`Current ecosystem (seed ${data.current.seed}): ${ev.n_fraud} injected-fraud taxpayers of ${ev.n_taxpayers}. Scored against generator labels; the model never sees them.`} />
      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Precision@k: how many of the top-k ranked are real fraud">
          <Bars rows={ks.map((k) => ({ label: `Top ${k}`, model: tp.model.precision_at_k[k], baseline: tp.rule_baseline.precision_at_k[k] }))} />
        </Card>
        <Card title="Recall@k: share of all fraud found in the top-k">
          <Bars rows={ks.map((k) => ({ label: `Top ${k}`, model: tp.model.recall_at_k[k], baseline: tp.rule_baseline.recall_at_k[k] }))} />
        </Card>
      </div>
      <Card title="Taxpayer-level detection">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-slate-500"><th className="pb-2 pr-3">Method</th><th className="pb-2 pr-3 text-right">Precision</th><th className="pb-2 pr-3 text-right">Recall</th><th className="pb-2 pr-3 text-right">F1</th><th className="pb-2 pr-3 text-right">ROC-AUC</th><th className="pb-2 text-right">Avg precision</th></tr></thead>
            <tbody>
              <Row name={<b>TaxSentinel (all layers)</b>} r={tp.model} />
              <Row name="Rule baseline (any rule R1-R5)" r={tp.rule_baseline} />
              <Row name="Ablation: JEPA only" r={tp.ablation.jepa_only} />
              <Row name="Ablation: graph + invoice only" r={tp.ablation.graph_and_invoice_only} />
              <Row name="Ablation: without invoice layer" r={tp.ablation.without_invoice_layer} />
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Model flags at risk ≥ {data.config.flag_threshold}: {tp.model.at_threshold.flagged} flagged ({tp.model.at_threshold.tp} true, {tp.model.at_threshold.fp} false).
          Rule baseline flags {tp.rule_baseline.at_threshold.flagged} ({tp.rule_baseline.at_threshold.fp} false alarms).
        </p>
      </Card>
      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Recall by fraud pattern (at threshold)">
          <Bars rows={Object.entries(ev.per_pattern).map(([k, v]) => ({ label: `${ROLE[k] || k} (${v.count})`, model: v.model_recall, baseline: v.baseline_recall }))} />
        </Card>
        <Card title="Invoices, rings and chains">
          <table className="w-full text-sm">
            <tbody>
              <tr><td className="py-1 text-slate-600">Invoice flags: precision / recall / F1</td><td className="py-1 text-right font-mono">{ev.invoice.model.at_threshold.precision.toFixed(2)} / {ev.invoice.model.at_threshold.recall.toFixed(2)} / {ev.invoice.model.at_threshold.f1.toFixed(2)}</td></tr>
              <tr><td className="py-1 text-slate-600">Rule "not in supplier GSTR-1": P / R / F1</td><td className="py-1 text-right font-mono">{ev.invoice.rule_baseline.at_threshold.precision.toFixed(2)} / {ev.invoice.rule_baseline.at_threshold.recall.toFixed(2)} / {ev.invoice.rule_baseline.at_threshold.f1.toFixed(2)}</td></tr>
              <tr><td className="py-1 text-slate-600">Invoice ROC-AUC</td><td className="py-1 text-right font-mono">{ev.invoice.model.roc_auc}</td></tr>
              <tr><td className="py-1 text-slate-600">Injected rings recovered</td><td className="py-1 text-right font-mono">{ev.rings.recovered}/{ev.rings.injected}</td></tr>
              <tr><td className="py-1 text-slate-600">Loops detected (with / without fraud members)</td><td className="py-1 text-right font-mono">{ev.rings.detected_with_fraud_members} / {ev.rings.detected_without_fraud_members}</td></tr>
              <tr><td className="py-1 text-slate-600">Top-10 invoice chains that are fraud</td><td className="py-1 text-right font-mono">{pct(ev.chains.precision_top10)}</td></tr>
            </tbody>
          </table>
        </Card>
      </div>
      <div className="grid lg:grid-cols-2 gap-5">
        <Card title="JEPA encoder training">
          <p className="text-sm text-slate-600">{tr.samples} taxpayer-months · {tr.epochs} epochs · window {tr.window} months · {tr.train_seconds}s on CPU · final loss {tr.final_loss}</p>
          {tr.loss_history && <LossCurve h={tr.loss_history} />}
        </Card>
        <Card title="Explanation quality (evaluation report)">
          {report?.explanations?.evaluated ? (
            <table className="w-full text-sm"><tbody>
              {Object.entries(report.explanations.summary).map(([k, v]) => (
                <tr key={k}><td className="py-1 text-slate-600">{k.replace(/_/g, ' ')}</td><td className="py-1 text-right font-mono">{typeof v === 'number' ? v.toFixed(3) : String(v)}</td></tr>
              ))}
            </tbody></table>
          ) : <p className="text-sm text-slate-500">{report?.explanations?.note || 'Run python -m ml.eval to produce the evaluation report.'}</p>}
          {report?.paysim && <p className="mt-3 text-xs text-slate-500">Transfer check on PaySim sample ({report.paysim.rows} transactions): JEPA ROC-AUC {report.paysim.roc_auc}, precision@100 {report.paysim.precision_at_k?.['100']}.</p>}
        </Card>
      </div>
    </div>
  )
}

function LossCurve({ h }) {
  const W = 400, H = 120, max = Math.max(...h), min = Math.min(...h)
  const pts = h.map((v, i) => `${(i / (h.length - 1)) * W},${H - 8 - ((v - min) / (max - min || 1)) * (H - 16)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full mt-3" role="img" aria-label="Training loss">
      <polyline points={pts} fill="none" stroke="#4f46e5" strokeWidth="2" />
      <text x="2" y="12" fontSize="10" fill="#64748b">loss {max.toFixed(3)}</text>
      <text x={W - 2} y={H - 2} fontSize="10" fill="#64748b" textAnchor="end">{min.toFixed(3)} (epoch {h.length})</text>
    </svg>
  )
}
