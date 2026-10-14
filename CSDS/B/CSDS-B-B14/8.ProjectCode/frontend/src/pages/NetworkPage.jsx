import { useState } from 'react'
import { Droplets, Gauge, MapPinned, Play, Scale } from 'lucide-react'
import api, { errorText } from '../api'
import useApi from '../useApi'
import { Badge, Button, Card, ErrorState, Field, KeyValueList, PageHeader, PageSkeleton, Select, Skeleton, StatCard, Table, Tabs, useToast } from '../components/ui'
import { GroupedBars } from '../components/charts'
import NetworkMap, { MapLegend } from '../components/NetworkMap.jsx'
import { fmtInt, fmtNum } from '../lib/format'
import { STATUS_TONE, ZONE_COLORS } from '../lib/aqua'
import { useChartTheme } from '../lib/palette'

const VIEWS = [
  { id: 'map', label: 'Map', icon: MapPinned },
  { id: 'imbalance', label: 'Distribution imbalance', icon: Scale },
]

export default function NetworkPage() {
  const [tab, setTab] = useState('map')
  return (
    <>
      <PageHeader
        eyebrow="Network twin"
        icon={MapPinned}
        title="Network map"
        lead="Digital twin of the city distribution network (WNTR / EPANET), with pressures and flows at the 08:00 peak."
        actions={<Tabs tabs={VIEWS} value={tab} onChange={setTab} label="Network views" name="netview" />}
      />
      {tab === 'map' ? <MapView /> : <Imbalance />}
    </>
  )
}

function MapView() {
  const { data, loading, error, reload } = useApi('/network')
  const [colorBy, setColorBy] = useState('zone')

  if (loading && !data) {
    return (
      <Card hover={false}>
        <Skeleton height={520} radius={18} />
        <p className="small muted" role="status" style={{ marginTop: 12 }}>
          Running the hydraulic simulation…
        </p>
      </Card>
    )
  }
  if (error && !data) return <ErrorState title="The network did not load" error={error} onRetry={reload} />
  if (!data) return null

  const junctions = data.nodes.filter((n) => n.type === 'Junction').length - 1
  const pipes = data.links.filter((l) => l.type === 'Pipe').length

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <Card
        title="Pipes and pressures at 08:00"
        subtitle={`${junctions} junctions · ${pipes} pipes · 1 pump · 1 tank · ${data.sensors.length} pressure loggers · NRW ${fmtNum(data.summary.nrw_pct, 1)}% · average pressure ${fmtNum(data.summary.avg_pressure, 1)} m`}
        actions={
          <Select
            id="colour-by"
            label="Colour"
            value={colorBy}
            onChange={(e) => setColorBy(e.target.value)}
            options={[
              { value: 'zone', label: 'Pipes by zone' },
              { value: 'flow', label: 'Pipe width by flow' },
            ]}
          />
        }
      >
        {data.active_leaks.length > 0 && (
          <p style={{ marginBottom: 12 }}>
            <Badge tone="rose" dot>
              {data.active_leaks.length} leak(s) active in the twin
            </Badge>
          </p>
        )}
        <NetworkMap nodes={data.nodes} links={data.links} suspects={data.suspects} activeLeaks={data.active_leaks} colorBy={colorBy} height={520} />
        <MapLegend colorBy={colorBy} zones={data.zones} />
      </Card>

      <div className="grid-kpi">
        {Object.values(data.zone_stats).map((z) => (
          <Card key={z.zone} hover={false} style={{ borderTop: `4px solid ${ZONE_COLORS[z.zone] || 'var(--border)'}` }}>
            <h3>{z.name}</h3>
            <div style={{ marginTop: 12 }}>
              <KeyValueList
                items={[
                  ['Demand', `${fmtInt(z.demand_m3)} m³/day`],
                  ['Pressure', `${fmtNum(z.avg_pressure, 1)} m (min ${fmtNum(z.min_pressure, 1)})`],
                  ['Losses', `${fmtInt(z.losses_m3)} m³/day`],
                ]}
              />
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

function Imbalance() {
  const t = useChartTheme()
  const toast = useToast()
  const { data, loading, error, reload } = useApi('/imbalance')
  const [speed, setSpeed] = useState(1.0)
  const [throttle, setThrottle] = useState('')
  const [what, setWhat] = useState(null)
  const [busy, setBusy] = useState(false)
  const [werr, setWerr] = useState('')

  async function run(sp, th) {
    setBusy(true)
    setWerr('')
    try {
      const r = await api.post('/imbalance/whatif', { pump_speed: sp, throttle: th || null })
      setWhat(r.data)
      toast({ kind: 'success', title: 'Scenario simulated', message: `Equity ${fmtNum(r.data.equity_score, 1)} · NRW ${fmtNum(r.data.nrw_pct, 1)}%` })
    } catch (e) {
      setWerr(errorText(e))
    } finally {
      setBusy(false)
    }
  }

  if (loading && !data) return <PageSkeleton kpis={4} blocks={1} />
  if (error && !data) return <ErrorState title="The imbalance analysis did not load" error={error} onRetry={reload} />
  if (!data) return null

  const cur = data.current
  const rec = data.suggestion.recommended
  const scenarioThrottle = throttle ? { [throttle]: 300 } : null

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <div className="grid-kpi">
        <StatCard label="Equity score" display={`${fmtNum(cur.equity_score, 1)} / 100`} icon={Scale} tone={cur.equity_score < 90 ? 'peach' : 'mint'} foot="worst vs best zone service" />
        <StatCard label="Non-revenue water" display={`${fmtNum(cur.nrw_pct, 1)}%`} icon={Droplets} tone="rose" />
        <StatCard label="System input" display={`${fmtInt(cur.system_input_m3)} m³/day`} icon={Gauge} tone="sky" />
        <StatCard label="Minimum pressure" display={`${fmtNum(cur.min_pressure, 1)} m`} icon={Gauge} tone={cur.min_pressure < 20 ? 'rose' : 'mint'} />
      </div>

      <Card tint={data.suggestion.improves ? 'peach' : 'mint'} hover={false} title="Rebalancing suggestion">
        <p>{data.suggestion.text}</p>
        {rec && (
          <div style={{ marginTop: 16 }}>
            <Button
              icon={Play}
              loading={busy}
              onClick={() => {
                setSpeed(rec.pump_speed)
                setThrottle(rec.throttle ? Object.keys(rec.throttle)[0] : '')
                run(rec.pump_speed, rec.throttle)
              }}
            >
              Test plan on the twin
            </Button>
          </div>
        )}
      </Card>

      <Card title="Supply vs demand per zone" subtitle="24-hour simulation">
        <Table
          caption="Supply and demand by zone"
          rows={data.zones}
          rowKey={(z) => z.zone}
          pageSize={0}
          columns={[
            {
              key: 'name',
              label: 'Zone',
              render: (z) => (
                <span className="row" style={{ '--gap': '8px', flexWrap: 'nowrap' }}>
                  <span aria-hidden="true" style={{ width: 10, height: 10, borderRadius: 999, background: ZONE_COLORS[z.zone], flex: 'none' }} />
                  {z.name}
                </span>
              ),
            },
            { key: 'demand_m3', label: 'Demand m³', numeric: true, render: (z) => fmtInt(z.demand_m3) },
            { key: 'supply_m3', label: 'Supply m³', numeric: true, render: (z) => fmtInt(z.supply_m3) },
            { key: 'service_ratio', label: 'Delivered', numeric: true, render: (z) => `${fmtNum(z.service_ratio * 100, 1)}%` },
            { key: 'losses_m3', label: 'Losses m³', numeric: true, render: (z) => fmtInt(z.losses_m3) },
            { key: 'pressure_adequacy', label: 'Pressure OK', numeric: true, render: (z) => `${fmtNum(z.pressure_adequacy * 100, 0)}%` },
            { key: 'avg_pressure', label: 'Avg / min m', numeric: true, sortable: false, render: (z) => `${fmtNum(z.avg_pressure, 1)} / ${fmtNum(z.min_pressure, 1)}` },
            { key: 'status', label: 'Status', sortable: false, render: (z) => <Badge tone={STATUS_TONE[z.status] || 'neutral'}>{z.status}</Badge> },
          ]}
        />
      </Card>

      <Card title="What-if on the twin" subtitle="Change the pump speed or throttle a trunk main, then simulate. Available to every role.">
        <div className="form-grid" style={{ alignItems: 'end' }}>
          <Field label={`Pump speed: ${Math.round(speed * 100)}%`} id="pump-speed" hint="85% to 125% of the normal setting">
            <input
              id="pump-speed"
              type="range"
              min="0.85"
              max="1.25"
              step="0.05"
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              style={{ width: '100%', minHeight: 44, accentColor: 'var(--lavender-ink)' }}
            />
          </Field>
          <Select
            id="throttle"
            label="Throttle a trunk main"
            value={throttle}
            onChange={(e) => setThrottle(e.target.value)}
            options={[
              { value: '', label: 'None' },
              { value: 'P01', label: 'Zone 1 trunk main (P01)' },
              { value: 'P02', label: 'Zone 4 trunk main (P02)' },
            ]}
          />
          <Button variant="secondary" icon={Play} loading={busy} onClick={() => run(speed, throttle ? scenarioThrottle : null)}>
            Simulate
          </Button>
        </div>

        {werr && <ErrorState compact title="The scenario did not run" error={werr} onRetry={() => run(speed, throttle ? scenarioThrottle : null)} />}

        {what && (
          <div className="stack" style={{ '--gap': '14px', marginTop: 20 }}>
            <p className="small">
              Scenario: <b>{what.action}</b>. Equity {fmtNum(cur.equity_score, 1)} → <b>{fmtNum(what.equity_score, 1)}</b>, NRW {fmtNum(cur.nrw_pct, 1)}% →{' '}
              <b>{fmtNum(what.nrw_pct, 1)}%</b>, minimum pressure {fmtNum(cur.min_pressure, 1)} m → <b>{fmtNum(what.min_pressure, 1)} m</b>.
            </p>
            <GroupedBars
              label="Share of each zone with adequate pressure, now and in the scenario"
              data={data.zones.map((z) => ({
                x: z.name || z.zone,
                now: z.pressure_adequacy * 100,
                scenario: what.zones[z.zone].pressure_adequacy * 100,
              }))}
              series={[
                { key: 'now', name: 'Now', color: t.axis },
                { key: 'scenario', name: 'Scenario', color: t.sky },
              ]}
              valueFormat={(v) => `${fmtNum(v, 0)}%`}
              height={240}
            />
          </div>
        )}
      </Card>
    </div>
  )
}
