import { Activity, Bell, ShieldAlert, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import api from '../api'
import BatchCard from '../components/scoring/BatchCard'
import LiveLog from '../components/scoring/LiveLog'
import ScoreCharts from '../components/scoring/ScoreCharts'
import ScorePanel from '../components/scoring/ScorePanel'
import { PageHeader } from '../components/ui/AppShell'
import { StatCard } from '../components/ui/display'
import { Stagger } from '../components/motion'
import { useScored } from '../lib/session'

export default function Dashboard() {
  const log = useScored()
  const [alerts, setAlerts] = useState(null)
  const attacks = log.filter((e) => e.label === 'attack').length

  // backend-wide alert count (includes alerts raised by earlier sessions / other clients)
  useEffect(() => {
    let live = true
    api.get('/alerts', { params: { limit: 1 }, silent: true }).then((r) => live && setAlerts(r.data.total)).catch(() => live && setAlerts(null))
    return () => { live = false }
  }, [log.length])

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="ThreatSense engine" title="Live scoring"
        subtitle="Score single flow records or whole CSVs against the XGBoost + 1D CNN + logistic-regression ensemble and watch the verdicts stream in." />
      <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Scored" value={log.length} icon={Activity} tone="cyan" sub="this session" live />
        <StatCard label="Attacks" value={attacks} icon={ShieldAlert} tone="alert" sub="this session" />
        <StatCard label="Normal" value={log.length - attacks} icon={ShieldCheck} tone="ok" sub="this session" />
        <StatCard label="Server alerts" value={alerts === null ? '-' : alerts} icon={Bell} tone="warn" sub="all clients, since start" />
      </Stagger>
      <div id="score" className="scroll-mt-20"><ScorePanel /></div>
      <BatchCard />
      <LiveLog />
      <ScoreCharts />
    </div>
  )
}
