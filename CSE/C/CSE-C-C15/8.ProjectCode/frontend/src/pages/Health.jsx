import { Cpu, HardDrive, MemoryStick, Network } from 'lucide-react'
import { useMemo } from 'react'
import { HealthChart, ThroughputChart } from '../components/app/Charts'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton, ProgressBar } from '../components/ui/feedback'
import { bytes, fmt } from '../format'
import { useLive } from '../lib/live'

export default function Health() {
  const { loaded, error, refresh, health } = useLive()
  const rows = useMemo(() => {
    const src = health?.recent?.length ? health.recent : [...(health?.history || [])].reverse()
    return src.map((r, i) => {
      const prev = src[i - 1]
      const dt = prev ? Math.max(r.timestamp - prev.timestamp, 1) : 0
      return {
        t: r.timestamp, cpu: r.cpu_percent, mem: r.memory_percent,
        inRate: prev ? Math.max(r.bytes_recv - prev.bytes_recv, 0) / dt : 0,
        outRate: prev ? Math.max(r.bytes_sent - prev.bytes_sent, 0) / dt : 0,
      }
    }).slice(1)
  }, [health])

  if (!loaded) return <PageSkeleton />
  const cur = health?.current
  const last = rows[rows.length - 1]

  return (
    <div className="space-y-5">
      <PageHeader eyebrow="console / network health" title="Network health"
        subtitle="Host CPU, memory and interface counters sampled by the backend every 5 seconds (psutil)." />
      {error && <ErrorState error={error} title="Backend unreachable" onRetry={refresh} />}
      {!cur ? (
        <Card title="Host health"><EmptyState icon={Cpu} title="No health samples yet" body="The backend samples the host every 5 seconds; the first sample should appear in a moment." /></Card>
      ) : (
        <>
          <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard label="CPU" icon={Cpu} live tone={cur.cpu_percent > 85 ? 'alert' : 'ok'} value={cur.cpu_percent} format={(v) => `${v.toFixed(1)}%`} />
            <StatCard label="Memory" icon={MemoryStick} tone={cur.memory_percent > 90 ? 'alert' : cur.memory_percent > 75 ? 'warn' : 'ok'} value={cur.memory_percent} format={(v) => `${v.toFixed(1)}%`} />
            <StatCard label="Received" icon={Network} tone="cyan" value={bytes(cur.bytes_recv)} sub={`${fmt(cur.packets_recv)} packets · ${last ? bytes(last.inRate) : '-'}/s`} />
            <StatCard label="Sent" icon={HardDrive} tone="warn" value={bytes(cur.bytes_sent)} sub={`${fmt(cur.packets_sent)} packets · ${last ? bytes(last.outRate) : '-'}/s`} />
          </Stagger>
          <div className="grid gap-5 lg:grid-cols-2">
            <Card title="CPU and memory"><HealthChart rows={rows} /></Card>
            <Card title="Throughput"><ThroughputChart rows={rows} /></Card>
          </div>
          <Card title="Current load">
            <div className="grid gap-5 sm:grid-cols-2">
              <ProgressBar label="CPU" value={cur.cpu_percent} tone={cur.cpu_percent > 85 ? 'alert' : 'ok'} />
              <ProgressBar label="Memory" value={cur.memory_percent} tone={cur.memory_percent > 90 ? 'alert' : cur.memory_percent > 75 ? 'warn' : 'ok'} />
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
