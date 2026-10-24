import { FEATURE_LABEL, dateTime, fmt, mitLabel, pct, rate } from '../../format'
import { KeyValueList, Prediction, ScoreBar, Severity } from '../ui/display'

function Block({ title, children }) {
  return (
    <section className="border-b border-line px-4 py-4 last:border-0">
      <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.16em] text-ok">{title}</h3>
      {children}
    </section>
  )
}

const COMPONENT_LABEL = {
  source_diversity: 'Source diversity',
  destination_diversity: 'Destination diversity',
  packet_rate_pressure: 'Packet-rate pressure',
  baseline_deviation: 'Baseline deviation',
}

// Everything the backend recorded for one monitoring window: prediction, risk, severity factors, actions, features.
export default function ThreatDetail({ d }) {
  const det = d.detail || {}
  const dist = det.distributed || {}
  const sev = det.severity || {}
  const ctx = det.context || {}
  const feats = det.features || {}
  const proto = Object.entries(ctx.protocol_distribution || {})
  const protoTotal = proto.reduce((a, [, v]) => a + v, 0) || 1
  return (
    <div>
      <Block title="Verdict">
        <div className="flex flex-wrap items-center gap-2">
          <Prediction p={d.prediction} />
          <Severity s={d.severity} />
          <span className="font-mono text-xs text-muted">window #{d.id} · {dateTime(d.timestamp)}</span>
        </div>
        <KeyValueList items={[
          ['Model confidence', pct(d.confidence)],
          ['Severity score', sev.severity_score ?? '-'],
          ['Source', `${d.source} · ${d.interface}`],
          ['Mitigation', mitLabel(d.mitigation_status)],
        ]} />
      </Block>
      <Block title="Measured traffic">
        <KeyValueList items={[
          ['Packet rate', rate(d.packet_rate, 'pkt/s')], ['Byte rate', rate(d.byte_rate, 'B/s')],
          ['Unique sources', fmt(d.source_count)], ['Unique destinations', fmt(d.destination_count)],
        ]} />
      </Block>
      {dist.explanation && (
        <Block title="Distributed-traffic risk">
          <p className="mb-3 text-sm text-muted">{dist.explanation}</p>
          <div className="space-y-3">
            <ScoreBar value={Math.min(1, dist.distributed_risk_score ?? d.distributed_risk ?? 0)} label={`Overall risk (${dist.distributed_risk_level})`} />
            {Object.entries(dist.components || {}).map(([k, v]) => <ScoreBar key={k} value={Math.min(1, v)} label={COMPONENT_LABEL[k] || k} segments={18} />)}
          </div>
        </Block>
      )}
      {sev.factors?.length > 0 && (
        <Block title="Severity factors">
          <ul className="space-y-1.5 text-sm text-fg">
            {sev.factors.map((f) => <li key={f} className="flex gap-2"><span className="font-mono text-ok">›</span><span>{f}</span></li>)}
          </ul>
          {sev.recommendation && <p className="mt-3 rounded-[6px] border border-line-strong bg-panel-2 p-3 text-sm text-muted"><b className="text-fg">Recommended: </b>{sev.recommendation}</p>}
        </Block>
      )}
      {det.actions?.length > 0 && (
        <Block title="Actions taken">
          <ul className="space-y-1 font-mono text-xs text-muted">
            {det.actions.map((a, i) => (
              <li key={i}>{mitLabel(a.action)} · {a.target}{a.duration ? ` · ${a.duration}s` : ''}</li>
            ))}
          </ul>
        </Block>
      )}
      {(ctx.top_sources?.length > 0 || ctx.top_destinations?.length > 0) && (
        <Block title="Top talkers">
          <div className="grid gap-4 sm:grid-cols-2">
            {[['Sources', ctx.top_sources], ['Destinations', ctx.top_destinations]].map(([t, list]) => (
              <div key={t}>
                <div className="mb-1 text-xs text-dim">{t}</div>
                <ul className="space-y-1 font-mono text-xs">
                  {(list || []).slice(0, 6).map((x) => <li key={x.ip} className="flex justify-between gap-3"><span className="truncate text-fg">{x.ip}</span><span className="tabular-nums text-muted">{fmt(x.packets)} pkts</span></li>)}
                </ul>
              </div>
            ))}
          </div>
        </Block>
      )}
      {proto.length > 0 && (
        <Block title="Protocol mix">
          <div className="space-y-1.5">
            {proto.map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 font-mono text-xs">
                <span className="w-12 text-muted">{k}</span>
                <span className="h-2 flex-1 rounded-[2px] bg-line-strong"><span className="block h-full rounded-[2px] bg-ok" style={{ width: `${(v / protoTotal) * 100}%` }} /></span>
                <span className="w-16 text-right tabular-nums text-fg">{fmt(v)}</span>
              </div>
            ))}
          </div>
        </Block>
      )}
      {Object.keys(feats).length > 0 && (
        <Block title="Model input features">
          <KeyValueList items={Object.entries(feats).map(([k, v]) => [FEATURE_LABEL[k] || k, fmt(v, 1)])} />
        </Block>
      )}
    </div>
  )
}
