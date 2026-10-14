import { useCallback, useEffect, useState } from 'react'
import { ShieldAlert, Users, Wrench, Zap } from 'lucide-react'
import api, { errorText } from '../api'
import useApi from '../useApi'
import { useAuth } from '../auth.jsx'
import { Badge, Button, Card, ErrorState, Field, KeyValueList, PageHeader, Select, Skeleton, Table, Tabs, useToast } from '../components/ui'
import { BarCompare, LineCompare } from '../components/charts'
import NetworkMap, { MapLegend } from '../components/NetworkMap.jsx'
import { fmtInt, fmtNum, fmtPct, timeAgo } from '../lib/format'
import { TYPE_TONE } from '../lib/aqua'
import { useChartTheme } from '../lib/palette'

const TABS = [
  { id: 'leaks', label: 'Leak detection', icon: ShieldAlert },
  { id: 'meters', label: 'Abnormal consumption', icon: Users },
]

function LeakPanel() {
  const t = useChartTheme()
  const toast = useToast()
  const { user } = useAuth()
  const net = useApi('/network')
  const pipes = useApi('/leaks/pipes')
  const events = useApi('/leaks/events')
  const [pipe, setPipe] = useState('P53')
  const [size, setSize] = useState(12)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const canInject = user?.role === 'engineer'
  const onPipeClick = useCallback((p) => setPipe(p), [])

  // Keep the selection on a pipe that exists in the twin.
  useEffect(() => {
    if (pipes.data?.length && !pipes.data.some((p) => p.pipe === pipe)) setPipe(pipes.data[0].pipe)
  }, [pipes.data, pipe])

  async function inject() {
    setBusy('inject')
    setError('')
    try {
      const r = await api.post('/leaks/inject', { pipe, leak_lps: size })
      setResult(r.data)
      net.reload()
      events.reload()
      toast({
        kind: 'info',
        title: r.data.detected ? `Leak detected, most likely near ${r.data.ranking[0].pipe}` : 'No leak detected',
        message: r.data.detected
          ? `Probability ${Math.round(r.data.leak_probability * 100)}%. An alert was raised.`
          : `The ${size} L/s leak on ${pipe} was not detected.`,
      })
    } catch (e) {
      setError(errorText(e))
    } finally {
      setBusy('')
    }
  }

  async function repair() {
    setBusy('repair')
    setError('')
    try {
      const r = await api.post('/leaks/clear')
      setResult(null)
      net.reload()
      events.reload()
      toast({ kind: 'success', title: 'Network repaired', message: `${r.data.repaired} injected leak(s) closed. The twin is back to baseline.` })
    } catch (e) {
      setError(errorText(e))
    } finally {
      setBusy('')
    }
  }

  const suspects = result?.ranking || net.data?.suspects || []

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <div className="grid-2 wide-left">
        <Card
          title="Leak scenario on the twin"
          subtitle="Choose a pipe, or click one on the map. The twin simulates what the 16 pressure loggers and 5 zone inlet meters report in the 03:00 night-flow window. The detector then decides whether there is a leak, and ranks the likely pipes."
        >
          <div className="stack" style={{ '--gap': '16px' }}>
            {pipes.loading && !pipes.data && <Skeleton height={50} radius={16} />}
            {pipes.error && <ErrorState compact title="Pipe list did not load" error={pipes.error} onRetry={pipes.reload} />}
            {pipes.data && (
              <Select id="leak-pipe" label="Pipe" value={pipe} onChange={(e) => setPipe(e.target.value)} options={pipes.data.map((p) => ({ value: p.pipe, label: `${p.pipe} (${p.zone})` }))} />
            )}

            <Field label={`Leak size: ${size} L/s`} id="leak-size" hint="2 to 30 L/s">
              <input
                id="leak-size"
                type="range"
                min="2"
                max="30"
                step="1"
                value={size}
                onChange={(e) => setSize(Number(e.target.value))}
                style={{ width: '100%', minHeight: 44, accentColor: 'var(--lavender-ink)' }}
              />
            </Field>

            {!canInject && (
              <p className="field-hint" role="note">
                Leak scenarios are run by the engineer role. As a manager you can view the results.
              </p>
            )}
            {error && (
              <p className="field-error" role="alert">
                {error}
              </p>
            )}

            <div className="row">
              <Button variant="danger" icon={Zap} loading={busy === 'inject'} disabled={!canInject || !!busy || !pipe} onClick={inject}>
                Inject leak
              </Button>
              <Button variant="secondary" icon={Wrench} loading={busy === 'repair'} disabled={!canInject || !!busy} onClick={repair} title="Repair all injected leaks">
                Repair all
              </Button>
            </div>

            {result && (
              <div role="status" style={{ borderRadius: 'var(--r)', padding: 14, background: result.detected ? 'var(--rose-soft)' : 'var(--mint-soft)' }}>
                <Badge tone={result.detected ? 'rose' : 'mint'} dot>
                  {result.detected ? 'Leak detected, alert raised' : 'No leak detected'}
                </Badge>
                <p className="small" style={{ marginTop: 8 }}>
                  Leak probability {fmtPct(result.leak_probability, 1)}. The injected pipe {result.event.pipe} ranked <b>#{result.true_rank ?? '–'}</b> of{' '}
                  {pipes.data?.length ?? '–'}.
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card title="Network map" subtitle="Numbered pipes are the ranked suspects (1 = most likely). The selected pipe is drawn in black.">
          {net.error && !net.data && <ErrorState compact title="Map unavailable" error={net.error} onRetry={net.reload} />}
          {net.data ? (
            <>
              <NetworkMap
                nodes={net.data.nodes}
                links={net.data.links}
                suspects={suspects}
                activeLeaks={net.data.active_leaks}
                onPipeClick={onPipeClick}
                selectedPipe={pipe}
                height={420}
              />
              <MapLegend zones={net.data.zones} />
            </>
          ) : (
            !net.error && <Skeleton height={420} radius={18} />
          )}
        </Card>
      </div>

      {result && (
        <div className="grid-2">
          <Card title="Likely leak locations" subtitle="Ranked by detector match">
            <Table
              caption="Ranked leak suspects"
              rows={result.ranking}
              rowKey={(r) => r.pipe}
              pageSize={0}
              highlight={(r) => r.pipe === result.event.pipe}
              columns={[
                { key: 'rank', label: 'Rank', sortable: false, render: (r) => `#${result.ranking.indexOf(r) + 1}` },
                {
                  key: 'pipe',
                  label: 'Pipe',
                  render: (r) => (
                    <span className="row" style={{ '--gap': '8px', flexWrap: 'nowrap' }}>
                      {r.pipe}
                      {r.pipe === result.event.pipe && <Badge tone="mint">injected</Badge>}
                    </span>
                  ),
                },
                { key: 'zone', label: 'Zone' },
                { key: 'score', label: 'Match', numeric: true, render: (r) => fmtPct(r.score, 1) },
                { key: 'estimated_lps', label: 'Est. size', numeric: true, render: (r) => `${r.estimated_lps} L/s` },
              ]}
            />
          </Card>
          <Card title="Zone inlet residuals" subtitle="Observed minus the twin's expectation, in L/s. Extra inflow shows where the water is going.">
            <BarCompare
              label="Extra inflow per zone in litres per second"
              data={Object.entries(result.zone_inflow_residual_lps).map(([z, v]) => ({ name: z, value: Math.max(0, v), color: t.rose }))}
              valueFormat={(v) => fmtNum(v, 1)}
              name="Extra inflow (L/s)"
              height={240}
            />
          </Card>
        </div>
      )}

      <Card title="Leak scenarios run" subtitle="The 30 most recent. Repaired scenarios stay listed.">
        {events.error && <ErrorState compact title="Scenarios did not load" error={events.error} onRetry={events.reload} />}
        {events.loading && !events.data && <Skeleton height={140} />}
        {events.data && (
          <Table
            caption="Leak scenarios"
            rows={events.data}
            rowKey={(e) => e.id}
            pageSize={8}
            columns={[
              { key: 'created_at', label: 'When', render: (e) => timeAgo(e.created_at) },
              { key: 'pipe', label: 'Pipe', render: (e) => `${e.pipe} (${e.zone})` },
              { key: 'leak_lps', label: 'Size', numeric: true, render: (e) => `${e.leak_lps} L/s` },
              {
                key: 'detected',
                label: 'Detected',
                sortable: false,
                render: (e) => <Badge tone={e.detected ? 'rose' : 'neutral'}>{e.detected ? `yes, ${Math.round(e.probability * 100)}%` : 'no'}</Badge>,
              },
              { key: 'top_pipe', label: 'Top suspect' },
              { key: 'true_rank', label: 'Rank of true pipe', numeric: true, render: (e) => `#${e.true_rank ?? '–'}` },
              { key: 'active', label: 'State', sortable: false, render: (e) => (e.active ? <Badge tone="peach">active</Badge> : <Badge>repaired</Badge>) },
            ]}
          />
        )}
      </Card>
    </div>
  )
}

function MeterDetail({ id }) {
  const t = useChartTheme()
  const { data, loading, error, reload } = useApi(`/anomalies/meter/${id}`)
  if (loading && !data) return <Skeleton height={240} radius={18} style={{ marginTop: 18 }} />
  if (error) return <ErrorState compact title="Meter readings did not load" error={error} onRetry={reload} />
  if (!data) return null
  const days = data.daily.slice(-14)
  return (
    <div className="stack" style={{ '--gap': '20px', marginTop: 20 }}>
      <div>
        <p className="field-label" style={{ marginBottom: 6 }}>
          Hourly use, last 14 days (m³/h)
        </p>
        <LineCompare
          label={`Hourly water use for meter ${id}`}
          data={data.hourly.map((h) => ({ x: String(h.ts).slice(5, 16), m3: h.m3 }))}
          series={[{ key: 'm3', name: 'Hourly use (m³/h)', color: t.sky }]}
          yFormat={(v) => fmtNum(v, 2)}
          valueFormat={(v) => `${fmtNum(v, 3)} m³/h`}
          dots={false}
          height={200}
        />
      </div>
      <div>
        <p className="field-label" style={{ marginBottom: 6 }}>
          Daily total. Red bars were flagged by the model.
        </p>
        <BarCompare
          label={`Daily water use for meter ${id}, flagged days in red`}
          data={days.map((d) => ({ name: d.date.slice(5), value: d.total, color: d.anomaly ? t.rose : t.sky }))}
          valueFormat={(v) => fmtNum(v, 2)}
          name="Daily total (m³)"
          height={200}
        />
      </div>
    </div>
  )
}

function MeterPanel() {
  const { data, loading, error, reload } = useApi('/anomalies')
  const [sel, setSel] = useState(null)

  useEffect(() => {
    if (data?.meters?.length && !sel) setSel((data.meters.find((m) => m.type === 'night_flow') || data.meters[0]).meter_id)
  }, [data, sel])

  if (loading && !data) {
    return (
      <Card hover={false}>
        <Skeleton height={320} radius={18} />
        <p className="small muted" role="status" style={{ marginTop: 12 }}>
          Scoring customer meters…
        </p>
      </Card>
    )
  }
  if (error && !data) return <ErrorState title="Meter scores did not load" error={error} onRetry={reload} />
  if (!data) return null

  const meter = data.meters.find((m) => m.meter_id === sel)

  return (
    <div className="grid-2 wide-left">
      <Card title="Flagged meters" subtitle={`${data.summary.flagged} of ${data.summary.meters} meters abnormal in the last 7 days (data to ${data.summary.data_until}). Choose a meter to see its readings.`}>
        <Table
          caption="Flagged customer meters"
          rows={data.meters}
          rowKey={(m) => m.meter_id}
          pageSize={10}
          searchKeys={['meter_id', 'zone', 'type']}
          searchPlaceholder="Search meter, zone or pattern"
          highlight={(m) => m.meter_id === sel}
          columns={[
            {
              key: 'meter_id',
              label: 'Meter',
              render: (m) => (
                <span>
                  <Button variant="ghost" size="sm" aria-pressed={m.meter_id === sel} onClick={() => setSel(m.meter_id)}>
                    {m.meter_id}
                  </Button>
                  <span className="tiny muted" style={{ display: 'block' }}>
                    {m.customer_type}
                  </span>
                </span>
              ),
            },
            { key: 'zone', label: 'Zone' },
            {
              key: 'type',
              label: 'Pattern',
              sortable: false,
              render: (m) => <Badge tone={TYPE_TONE[m.type] || 'neutral'}>{m.type.replace(/_/g, ' ')}</Badge>,
            },
            { key: 'anomalous_days', label: 'Days', numeric: true },
            { key: 'since', label: 'Since' },
            { key: 'score', label: 'Score', numeric: true, render: (m) => fmtNum(m.score, 2) },
          ]}
        />
      </Card>

      <Card title={meter ? `Meter ${meter.meter_id}` : 'Meter detail'} subtitle={meter ? `${meter.type.replace(/_/g, ' ')}. ${meter.description}` : 'Select a meter to see its readings.'}>
        {meter && (
          <KeyValueList
            items={[
              ['Night flow', `${fmtInt(meter.night_flow_m3h * 1000)} L/h (baseline ${fmtInt(meter.baseline_night_m3h * 1000)} L/h)`],
              ['Daily use', `${fmtNum(meter.day_total_m3, 2)} m³ (baseline ${fmtNum(meter.baseline_total_m3, 2)} m³)`],
            ]}
          />
        )}
        {sel && <MeterDetail id={sel} />}
      </Card>
    </div>
  )
}

export default function Leaks() {
  const [tab, setTab] = useState('leaks')
  return (
    <>
      <PageHeader
        eyebrow="Leaks and anomalies"
        icon={ShieldAlert}
        title="Leaks and anomalies"
        lead="Model-based leak detection on the twin, and an IsolationForest over customer meters."
        actions={<Tabs tabs={TABS} value={tab} onChange={setTab} label="Leak views" name="leakview" />}
      />
      {tab === 'leaks' ? <LeakPanel /> : <MeterPanel />}
    </>
  )
}
