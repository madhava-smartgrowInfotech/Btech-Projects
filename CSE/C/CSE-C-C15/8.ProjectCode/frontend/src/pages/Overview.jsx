import { Activity, Gauge, Network, ShieldAlert, ShieldCheck, Target } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { RateChart } from '../components/app/Charts'
import SessionBar from '../components/app/SessionBar'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import ActivityLog from '../components/ui/ActivityLog'
import { Button } from '../components/ui/controls'
import { Card, Prediction, Severity, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton } from '../components/ui/feedback'
import { clock, fmt, mitLabel, pct } from '../format'
import { useLive } from '../lib/live'

export default function Overview() {
  const { loaded, error, refresh, detections, status, mitigations, busy, startSim } = useLive()

  const latest = detections[0] || null
  const series = useMemo(() => detections.slice(0, 40).reverse().map((d) => ({
    t: d.timestamp, rate: d.packet_rate, attack: d.prediction === 'Attack', conf: d.confidence, risk: d.distributed_risk, src: d.source_count,
  })), [detections])

  if (!loaded) return <PageSkeleton />

  const dist = latest?.detail?.distributed
  const active = mitigations?.active?.length ?? status?.active_mitigations ?? 0
  const attack = latest?.prediction === 'Attack'

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="console / overview" title="Threat overview"
        subtitle="Live status of the current monitoring session, scored window by window by the Random Forest model." />
      {error && <ErrorState error={error} title="Backend unreachable" onRetry={refresh} />}
      <SessionBar />

      {!latest ? (
        <Card title="Latest window">
          <EmptyState icon={Activity} title="No windows scored yet"
            body="Start a simulation to push synthetic traffic windows through the real model, or start a live capture if you have capture rights."
            action={<Button icon={Activity} loading={busy === 'sim'} disabled={status?.monitoring || !!error} onClick={() => startSim(5)}>Start simulation</Button>} />
        </Card>
      ) : (
        <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
          <StatCard label="Threat status" icon={attack ? ShieldAlert : ShieldCheck} tone={attack ? 'alert' : 'ok'} live={status?.monitoring}
            value={latest.prediction} sub={`${latest.source} · ${clock(latest.timestamp)}`} />
          <StatCard label="Severity" icon={Gauge} tone={{ Low: 'ok', Medium: 'warn', High: 'hot', Critical: 'alert' }[latest.severity]}
            value={latest.severity} sub={dist ? `risk ${dist.distributed_risk_score} (${dist.distributed_risk_level})` : 'risk -'} />
          <StatCard label="ML confidence" icon={Target} tone="cyan" value={latest.confidence * 100} format={(v) => `${v.toFixed(1)}%`} sub="Random Forest" />
          <StatCard label="Packets / sec" icon={Activity} value={latest.packet_rate} format={(v) => fmt(v)} sub={`${fmt(latest.byte_rate)} bytes/s`}
            spark={series} sparkKey="rate" sparkLabel="last windows" />
          <StatCard label="Sources / dests" icon={Network} tone="info" value={`${fmt(latest.source_count)} / ${fmt(latest.destination_count)}`} sub="unique per window" />
          <StatCard label="Active mitigations" icon={ShieldAlert} tone={active ? 'alert' : 'ok'} value={active}
            sub={`mode: ${status?.mode || 'stopped'}`} />
        </Stagger>
      )}

      {latest && (
        <div className="grid gap-5 xl:grid-cols-3">
          <Card title="Packet rate per window" className="xl:col-span-2"
            action={<span className="font-mono text-[11px] text-dim">last {series.length} windows</span>}>
            <RateChart rows={series} />
          </Card>
          <Card title="Latest windows" bodyClass="p-0"
            action={<Link to="/app/detections" className="font-mono text-[11px] uppercase tracking-wider text-ok hover:underline">all</Link>}>
            <ul className="divide-y divide-line">
              {detections.slice(0, 7).map((d) => (
                <li key={d.id}>
                  <Link to={`/app/detections?id=${d.id}`} className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-ok/[0.04]">
                    <span className="font-mono text-[11px] text-dim">{clock(d.timestamp)}</span>
                    <Prediction p={d.prediction} />
                    <span className="min-w-0 flex-1 truncate text-right font-mono text-[11px] text-muted">{pct(d.confidence)} · {mitLabel(d.mitigation_status)}</span>
                    <Severity s={d.severity} />
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      <ActivityLog height={240} title="activity.log" />
    </div>
  )
}
