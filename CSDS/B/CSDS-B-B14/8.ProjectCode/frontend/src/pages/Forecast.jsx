import { useState } from 'react'
import { CalendarDays, CloudRain, Flame, Gauge, TrendingUp } from 'lucide-react'
import useApi from '../useApi'
import { Badge, Card, ErrorState, PageHeader, PageSkeleton, Select, Skeleton, StatCard, Table } from '../components/ui'
import { LineCompare } from '../components/charts'
import { fmtInt, fmtNum, fmtSigned } from '../lib/format'
import { dayLabel } from '../lib/aqua'
import { useChartTheme } from '../lib/palette'

export default function Forecast() {
  const t = useChartTheme()
  const [zone, setZone] = useState('Z3')
  const zones = useApi('/forecast/zones')
  const { data, loading, error, reload } = useApi(`/forecast?zone=${zone}`)

  const header = (
    <PageHeader
      eyebrow="Demand"
      icon={TrendingUp}
      title="Demand forecast"
      lead="Next 7 days per zone, from consumption history and weather (XGBoost, recursive 7-day forecast)."
      actions={
        zones.loading && !zones.data ? (
          <Skeleton width={180} height={50} radius={16} />
        ) : zones.error ? (
          <ErrorState compact title="Zones did not load" error={zones.error} onRetry={zones.reload} />
        ) : (
          <Select id="zone" label="Zone" value={zone} onChange={(e) => setZone(e.target.value)} options={(zones.data || []).map((z) => ({ value: z.id, label: z.name }))} />
        )
      }
    />
  )

  if (loading) {
    return (
      <>
        {header}
        <PageSkeleton kpis={4} blocks={1} />
      </>
    )
  }
  if (error) {
    return (
      <>
        {header}
        <ErrorState title="The forecast did not load" error={error} onRetry={reload} />
      </>
    )
  }
  if (!data) return header

  const avg = data.avg_last_7
  const hist = data.history.slice(-21)
  const rows = [
    ...hist.map((h) => ({ x: dayLabel(h.date), billed: h.consumption_m3, forecast: null })),
    ...data.forecast.map((f) => ({ x: dayLabel(f.date), billed: null, forecast: f.forecast_m3 })),
  ]
  // Join the two lines at the last observed day so the forecast starts from the real value.
  if (hist.length) rows[hist.length - 1].forecast = hist[hist.length - 1].consumption_m3

  return (
    <>
      {header}
      <div className="stack" style={{ '--gap': '24px' }}>
        <div className="grid-kpi">
          <StatCard label="Peak day" display={dayLabel(data.peak.date)} icon={TrendingUp} tone="peach" foot={`${fmtInt(data.peak.forecast_m3)} m³ at ${data.peak.tmax} °C`} />
          <StatCard label="Hottest day" display={dayLabel(data.hottest.date)} icon={Flame} tone="rose" foot={`${data.hottest.tmax} °C maximum`} />
          <StatCard
            label="7-day total"
            display={`${fmtInt(data.week_totals[zone])} m³`}
            icon={CalendarDays}
            tone="sky"
            foot={`last 7 days averaged ${fmtInt(avg)} m³/day`}
          />
          <StatCard
            label="Model error (MAPE)"
            display={data.mape == null ? '–' : `${fmtNum(data.mape, 2)}%`}
            icon={Gauge}
            tone="mint"
            foot="7-day recursive, last 90 days"
          />
        </div>

        <Card title={`${data.zone_name}: last three weeks and next seven days`} subtitle={`Data up to ${dayLabel(data.data_until)} · weather: ${data.weather_source}`}>
          <LineCompare
            label={`Billed consumption and forecast for ${data.zone_name}, cubic metres per day`}
            data={rows}
            series={[
              { key: 'billed', name: 'Billed consumption (m³/day)', color: t.axis },
              { key: 'forecast', name: 'Forecast (m³/day)', color: t.lavender, dashed: true },
            ]}
            yFormat={(v) => fmtInt(v)}
            valueFormat={(v) => `${fmtInt(v)} m³`}
            height={300}
          />
        </Card>

        <Card title="Day by day" subtitle="Each forecast day against the last-week average">
          <Table
            caption="Seven-day demand forecast"
            rows={data.forecast}
            rowKey={(f) => f.date}
            pageSize={0}
            columns={[
              { key: 'date', label: 'Day', sortable: false, render: (f) => <strong>{dayLabel(f.date)}</strong> },
              { key: 'forecast_m3', label: 'Forecast m³', numeric: true, render: (f) => fmtInt(f.forecast_m3) },
              { key: 'vs', label: 'vs last week', numeric: true, sortable: false, render: (f) => fmtSigned(((f.forecast_m3 - avg) / avg) * 100, 1, '%') },
              { key: 'temp', label: 'Max / min °C', sortable: false, render: (f) => `${f.tmax} / ${f.tmin}` },
              {
                key: 'rain',
                label: 'Rain mm',
                sortable: false,
                render: (f) =>
                  f.precip > 0 ? (
                    <span className="row" style={{ '--gap': '6px' }}>
                      <CloudRain size={15} aria-hidden="true" color="var(--sky-ink)" />
                      {f.precip}
                    </span>
                  ) : (
                    '0'
                  ),
              },
              {
                key: 'flags',
                label: 'Flags',
                sortable: false,
                render: (f) => (
                  <span className="row" style={{ '--gap': '6px' }}>
                    {f.date === data.peak.date && <Badge tone="rose">peak demand</Badge>}
                    {f.date === data.hottest.date && <Badge tone="peach">hottest</Badge>}
                  </span>
                ),
              },
            ]}
          />
        </Card>
      </div>
    </>
  )
}
