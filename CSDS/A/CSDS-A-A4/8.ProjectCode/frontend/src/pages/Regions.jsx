import { useMemo, useState } from 'react'
import { Building2, Landmark, MapPinned, Users } from 'lucide-react'
import NetworkMap from '../components/NetworkMap'
import { Stagger } from '../components/motion'
import { Badge, Card, Checkbox, ErrorState, PageHeader, PageSkeleton, Select, StatCard, Table } from '../components/ui'
import { fmtInt, fmtNum } from '../lib/format'
import { useRegions } from '../lib/shared'

const TIER_TONE = { 1: 'lavender', 2: 'sky', 3: 'mint' }

export default function Regions() {
  const { data, error, loading, reload } = useRegions()
  const [tier, setTier] = useState('all')
  const [state, setState] = useState('all')
  const [majorOnly, setMajorOnly] = useState(false)

  const all = data?.regions || []
  const rows = useMemo(
    () =>
      all.filter(
        (r) => (tier === 'all' || String(r.tier) === tier) && (state === 'all' || r.state === state) && (!majorOnly || !r.parent || r.parent === r.city),
      ),
    [all, tier, state, majorOnly],
  )

  const header = (
    <PageHeader
      eyebrow="Objective 1 · Data"
      icon={MapPinned}
      title="Demand regions"
      lead="The 90 demand regions behind every forecast and plan: 30 Indian cities with real coordinates plus satellite districts. Read-only view of data/regions.csv with average monthly orders from the history."
    />
  )
  if (loading)
    return (
      <>
        {header}
        <PageSkeleton />
      </>
    )
  if (error)
    return (
      <>
        {header}
        <ErrorState title="Could not load the regions" error={error} onRetry={reload} />
      </>
    )

  const states = [...new Set(all.map((r) => r.state).filter(Boolean))].sort()
  const majors = all.filter((r) => !r.parent || r.parent === r.city).length
  const shownIdx = new Set(rows.map((r) => r.region_id))
  const mapRegions = all
  const demand = all.map((r) => (shownIdx.has(r.region_id) ? r.avg_orders : 0))

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}
      <Stagger className="grid-kpi">
        <Stagger.Item>
          <StatCard label="Regions" value={all.length} icon={MapPinned} tone="lavender" foot={`${majors} major cities`} />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="States covered" value={states.length} icon={Landmark} tone="sky" />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Population (cities)" value={all.filter((r) => !r.parent || r.parent === r.city).reduce((s, r) => s + (r.population || 0), 0)} format={(v) => `${fmtNum(v, 1)}M`} icon={Users} tone="mint" foot="millions, major cities" />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Avg monthly orders" value={all.reduce((s, r) => s + r.avg_orders, 0)} format={fmtInt} icon={Building2} tone="peach" foot="across all regions" />
        </Stagger.Item>
      </Stagger>

      <div className="grid-2 wide-left">
        <Card title="Regions" subtitle={`${rows.length} of ${all.length} shown`} hover={false}>
          <Table
            caption="Demand regions"
            rows={rows}
            rowKey={(r) => r.region_id}
            pageSize={10}
            searchKeys={['city', 'state', 'region_id']}
            searchPlaceholder="Search city, state or id"
            initialSort={{ key: 'avg_orders', dir: 'desc' }}
            tools={
              <div className="row" style={{ '--gap': '12px', alignItems: 'flex-end' }}>
                <div style={{ width: 150 }}>
                  <Select aria-label="Filter by tier" value={tier} onChange={(e) => setTier(e.target.value)} options={[{ value: 'all', label: 'All tiers' }, { value: '1', label: 'Tier 1' }, { value: '2', label: 'Tier 2' }, { value: '3', label: 'Tier 3' }]} />
                </div>
                <div style={{ width: 190 }}>
                  <Select aria-label="Filter by state" value={state} onChange={(e) => setState(e.target.value)} options={[{ value: 'all', label: 'All states' }, ...states]} />
                </div>
                <Checkbox label="Major cities only" checked={majorOnly} onChange={setMajorOnly} />
              </div>
            }
            columns={[
              { key: 'city', label: 'Region' },
              { key: 'state', label: 'State' },
              { key: 'tier', label: 'Tier', numeric: true, render: (r) => <Badge tone={TIER_TONE[r.tier] || 'neutral'}>Tier {r.tier}</Badge> },
              { key: 'population', label: 'Population', numeric: true, render: (r) => (r.population != null ? `${fmtNum(r.population, 2)}M` : '–') },
              { key: 'avg_orders', label: 'Avg orders / month', numeric: true, render: (r) => fmtInt(r.avg_orders) },
              { key: 'region_id', label: 'Id', render: (r) => <span className="mono muted">{r.region_id}</span> },
            ]}
          />
        </Card>
        <Card title="Where demand sits" subtitle="Circles sized by average monthly orders (filtered regions)">
          <NetworkMap regions={mapRegions} demand={demand} label={`Map of ${rows.length} demand regions`} />
        </Card>
      </div>
    </div>
  )
}
