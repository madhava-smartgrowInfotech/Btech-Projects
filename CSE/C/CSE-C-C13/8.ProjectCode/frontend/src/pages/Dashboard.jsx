import { useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Files, HardDrive, Share2, ShieldCheck, Upload, UserRoundCheck } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useAsync } from '../lib/useAsync'
import { actionLabel, ago, bytes, dayKey } from '../lib/format'
import { AreaTrend, ChartCard, DonutChart, useChartColors } from '../components/charts'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, PageHeader, Skeleton, StatCard, Timeline } from '../components/ui'
import { Stagger, SlideUp } from '../components/motion'
import VerifyChain from '../features/VerifyChain'

async function load() {
  const [owned, shared, audit] = await Promise.all([api.files(), api.shared(), api.audit(300)])
  return { owned, shared, audit }
}

function lastDays(events, n = 14) {
  const counts = new Map()
  for (const e of events) {
    const k = dayKey(e.timestamp_utc)
    if (k) counts.set(k, (counts.get(k) || 0) + 1)
  }
  const out = []
  const today = new Date()
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const k = d.toISOString().slice(0, 10)
    out.push({ day: k, events: counts.get(k) || 0 })
  }
  return out
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const c = useChartColors()
  const { data, error, loading, reload } = useAsync(load, [])

  const trend = useMemo(() => (data ? lastDays(data.audit) : []), [data])
  const roles = useMemo(() => {
    if (!data) return []
    const all = [...data.owned, ...data.shared]
    const count = (r) => all.filter((f) => f.effective_role === r).length
    return [
      { name: 'Owner', value: count('owner'), color: c.accent },
      { name: 'Editor', value: count('editor'), color: c.info },
      { name: 'Viewer', value: count('viewer'), color: c.violet },
    ].filter((r) => r.value > 0)
  }, [data, c])

  if (error)
    return (
      <>
        <PageHeader title="Dashboard" />
        <ErrorState title="Could not load the dashboard" error={error} onRetry={reload} />
      </>
    )

  const total = data ? data.owned.length + data.shared.length : 0
  const stored = data ? data.owned.reduce((a, f) => a + (f.original_size || 0), 0) : 0
  const empty = data && total === 0

  return (
    <>
      <PageHeader
        crumbs={[{ label: 'Vault' }, { label: 'Dashboard' }]}
        title={`Welcome back, ${user.name.split(' ')[0]}`}
        description="Your encrypted vault at a glance. Everything stored here is ciphertext."
        actions={
          <Button variant="primary" icon={Upload} onClick={() => navigate('/app/files')}>
            Upload a file
          </Button>
        }
      />

      <Stagger className="grid grid-4 mt">
        <StatCard label="Files you can open" icon={Files} value={total} loading={loading} />
        <StatCard label="Owned by you" icon={UserRoundCheck} tone="safe" value={data?.owned.length ?? 0} loading={loading} />
        <StatCard label="Shared with you" icon={Share2} tone="info" value={data?.shared.length ?? 0} loading={loading} />
        <StatCard label="Plaintext you store" icon={HardDrive} value={loading ? undefined : bytes(stored)} loading={loading} />
      </Stagger>

      {empty && (
        <SlideUp>
          <Card className="mt">
            <EmptyState icon={Upload} title="Your vault is empty" actions={<Link to="/app/files" className="btn btn-primary">Upload your first file</Link>}>
              Files are encrypted in this browser before upload, so even the server cannot read them.
            </EmptyState>
          </Card>
        </SlideUp>
      )}

      <div className="grid grid-2 mt" style={{ alignItems: 'stretch' }}>
        <SlideUp delay={0.05}>
          <ChartCard title="Security events" subtitle="Vault-wide audit events per day, last 14 days" height={260}>
            {loading ? <Skeleton height={240} /> : <AreaTrend data={trend} xKey="day" yKey="events" name="Events" labelFormat={(d) => (d?.length > 5 ? d.slice(5) : d)} yDomain={[0, 'auto']} />}
          </ChartCard>
        </SlideUp>
        <SlideUp delay={0.1}>
          <ChartCard title="Your access by role" subtitle="Across all files you can open" height={260}>
            {loading ? (
              <Skeleton height={240} />
            ) : roles.length ? (
              <DonutChart data={roles} centerValue={total} centerLabel={total === 1 ? 'file' : 'files'} />
            ) : (
              <EmptyState title="No files yet">Role breakdown appears after your first upload.</EmptyState>
            )}
          </ChartCard>
        </SlideUp>
      </div>

      <div className="grid grid-2 mt" style={{ alignItems: 'start' }}>
        <SlideUp delay={0.1}>
          <Card>
            <CardHeader title="Security status" subtitle="How this vault protects your data" />
            <div className="card-body stack">
              <div className="row" style={{ flexWrap: 'wrap' }}>
                <Badge tone="safe" dot>Encrypted before upload</Badge>
                <Badge tone="safe" dot>Ciphertext-only storage</Badge>
                <Badge tone="safe" dot>Role-based access</Badge>
                <Badge dot>AES-256-GCM · RSA-2048 · SHA-256</Badge>
              </div>
              <VerifyChain />
            </div>
          </Card>
        </SlideUp>
        <SlideUp delay={0.15}>
          <Card>
            <CardHeader title="Recent activity" actions={<Link to="/app/audit" className="btn btn-ghost btn-sm">View all</Link>} />
            <div className="card-body">
              {loading ? (
                <Skeleton height={140} />
              ) : data.audit.length ? (
                <Timeline
                  items={data.audit.slice(0, 6).map((a) => ({
                    key: a.id,
                    title: actionLabel(a.action),
                    tone: a.success ? 'safe' : 'danger',
                    meta: `${ago(a.timestamp_utc)} · ${a.user_email || 'system'}`,
                  }))}
                />
              ) : (
                <EmptyState icon={ShieldCheck} title="No events yet">Security events appear here as you use the vault.</EmptyState>
              )}
            </div>
          </Card>
        </SlideUp>
      </div>
    </>
  )
}
