import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Activity as ActivityIcon, Bot, Percent, RefreshCw, ScanSearch, ShieldAlert, Users } from 'lucide-react'
import { ReferenceLine } from 'recharts'
import { api } from '../lib/api'
import { useStats } from '../lib/stats'
import { useAsync } from '../lib/useAsync'
import { DECIDED_BY, VERDICT, ago, pct, when } from '../lib/format'
import { Badge, Button, Card, Container, EmptyState, ErrorState, PageHeader, SearchField, Select, Skeleton, StatCard, Switch, Table } from '../components/ui'
import { AreaTrend, ChartCard, DonutChart, useChartColors } from '../components/charts'
import { Reveal, Stagger } from '../components/motion'
import '../styles/pages.css'

const LIMIT = 200

export default function Activity() {
  const [live, setLive] = useState(false)
  const [query, setQuery] = useState('')
  const [verdict, setVerdict] = useState('')
  const navigate = useNavigate()
  const { ti, config } = useStats()
  const c = useChartColors()
  const log = useAsync(() => api.checks(LIMIT), [], { poll: live ? 10000 : 0 })
  const checks = log.data || []

  const counts = useMemo(() => checks.reduce((a, x) => ({ ...a, [x.verdict]: (a[x.verdict] || 0) + 1 }), {}), [checks])
  const byDecider = useMemo(() => checks.reduce((a, x) => ({ ...a, [x.decided_by]: (a[x.decided_by] || 0) + 1 }), {}), [checks])
  const scored = checks.filter((x) => x.probability !== null && x.probability !== undefined)
  const avg = scored.length ? scored.reduce((a, x) => a + x.probability, 0) / scored.length : null
  const trend = useMemo(
    () =>
      [...checks]
        .reverse()
        .filter((x) => x.probability !== null && x.probability !== undefined)
        .map((x, i) => ({ n: i + 1, probability: x.probability, url: x.url, at: x.created_at })),
    [checks],
  )
  const donut = [
    { name: 'Phishing', value: counts.phishing || 0, color: c.danger },
    { name: 'Suspicious', value: counts.suspicious || 0, color: c.warn },
    { name: 'Safe', value: counts.safe || 0, color: c.accent },
    { name: 'Unknown', value: counts.unknown || 0, color: c.text3 },
  ].filter((d) => d.value > 0)

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase()
    return checks.filter((x) => (!verdict || x.verdict === verdict) && (!q || x.url.toLowerCase().includes(q)))
  }, [checks, query, verdict])

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Activity' }]}
        title="Check activity"
        description={`The last ${LIMIT} URL checks logged by the detector - from this UI, the API and the command line.`}
        actions={
          <>
            <Switch label="Live" checked={live} onChange={(e) => setLive(e.target.checked)} />
            <Button icon={RefreshCw} onClick={() => log.reload()}>
              Refresh
            </Button>
          </>
        }
      />

      {log.error ? (
        <Card>
          <ErrorState title="Could not load the check log" error={log.error} onRetry={log.reload} />
        </Card>
      ) : log.loading && !log.data ? (
        <div className="grid grid-4" aria-busy="true">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} height={128} radius={12} />
          ))}
          <Skeleton height={300} radius={12} style={{ gridColumn: '1 / -1' }} />
        </div>
      ) : checks.length === 0 ? (
        <Card>
          <EmptyState
            icon={ActivityIcon}
            title="No checks logged yet"
            actions={
              <Button as={Link} to="/app/check" variant="primary" icon={ScanSearch}>
                Check a URL
              </Button>
            }
          >
            Every URL checked through PhishGuard is recorded here with its verdict and probability.
          </EmptyState>
        </Card>
      ) : (
        <div className="stack">
          <Stagger className="grid grid-4">
            <StatCard label="Checks (all time)" icon={ActivityIcon} value={ti?.checks ?? checks.length} delta={`${checks.length} shown below`} />
            <StatCard label="Flagged phishing" icon={ShieldAlert} tone="danger" value={counts.phishing || 0} delta={`${pct((counts.phishing || 0) / checks.length)} of recent checks`} />
            <StatCard label="Average probability" icon={Percent} tone="warn" value={avg === null ? '-' : avg * 100} format={(v) => `${v.toFixed(1)}%`} delta={`over ${scored.length} scored checks`} />
            <StatCard
              label="Decided by community"
              icon={Users}
              tone="info"
              value={byDecider.community || 0}
              delta={`${byDecider.ml || 0} by the ML model`}
            />
          </Stagger>

          <div className="split">
            <Reveal>
              <ChartCard title="Phishing probability per check" subtitle="Oldest → newest · dashed lines are the verdict thresholds" height={260}>
                <AreaTrend
                  data={trend}
                  xKey="n"
                  yKey="probability"
                  name="Probability"
                  yDomain={[0, 1]}
                  valueFormat={(v) => `${Math.round(v * 100)}%`}
                  labelFormat={(n) => `Check #${n}`}
                  refLines={[
                    <ReferenceLine key="s" y={config?.suspicious_threshold ?? 0.35} stroke={c.warn} strokeDasharray="4 4" strokeOpacity={0.7} />,
                    <ReferenceLine key="p" y={config?.phishing_threshold ?? 0.6} stroke={c.danger} strokeDasharray="4 4" strokeOpacity={0.7} />,
                  ]}
                />
              </ChartCard>
            </Reveal>
            <Reveal delay={0.05}>
              <ChartCard title="Verdict mix" subtitle={`Last ${checks.length} checks`} height={260}>
                <DonutChart data={donut} centerValue={checks.length} centerLabel="checks" />
              </ChartCard>
            </Reveal>
          </div>

          <Card>
            <div className="toolbar">
              <SearchField value={query} onChange={setQuery} label="Search checked URLs" placeholder="Search URL…" className="toolbar-search" />
              <div className="toolbar-filter">
                <Select
                  label="Verdict"
                  labelHidden
                  value={verdict}
                  onChange={(e) => setVerdict(e.target.value)}
                  options={[{ value: '', label: 'All verdicts' }, ...Object.entries(VERDICT).map(([k, v]) => ({ value: k, label: v.label }))]}
                />
              </div>
            </div>
            <Table
              caption="Check log"
              rows={rows}
              rowKey={(x) => x.id}
              pageSize={15}
              initialSort={{ key: 'id', dir: 'desc' }}
              onRowClick={(x) => navigate(`/app/check?url=${encodeURIComponent(x.url)}`)}
              empty={
                <EmptyState icon={ScanSearch} title="No matching checks" actions={<Button onClick={() => (setQuery(''), setVerdict(''))}>Clear filters</Button>}>
                  Nothing in the log matches this search.
                </EmptyState>
              }
              columns={[
                { key: 'id', label: '#', num: true, render: (x) => <span className="faint">{x.id}</span> },
                { key: 'url', label: 'URL', className: 'url-cell', render: (x) => (x.url.length > 90 ? `${x.url.slice(0, 90)}…` : x.url) },
                { key: 'verdict', label: 'Verdict', render: (x) => <Badge tone={VERDICT[x.verdict]?.tone} dot>{VERDICT[x.verdict]?.label || x.verdict}</Badge> },
                { key: 'probability', label: 'Probability', num: true, render: (x) => pct(x.probability) },
                {
                  key: 'decided_by',
                  label: 'Decided by',
                  render: (x) => (
                    <span className="row" style={{ gap: 6, flexWrap: 'nowrap' }}>
                      {x.decided_by === 'community' ? <Users size={14} aria-hidden="true" /> : <Bot size={14} aria-hidden="true" />}
                      {DECIDED_BY[x.decided_by]?.label || x.decided_by}
                    </span>
                  ),
                },
                { key: 'created_at', label: 'When', render: (x) => <span className="faint" title={when(x.created_at)}>{ago(x.created_at)}</span> },
              ]}
            />
          </Card>
        </div>
      )}
    </Container>
  )
}
