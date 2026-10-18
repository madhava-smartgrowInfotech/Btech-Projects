import { useMemo } from 'react'
import { TriangleAlert } from 'lucide-react'
import { useSimulation } from '../hooks/useSimulation'
import { NODE_IDS, num } from '../lib/format'
import { PageHeader } from '../components/ui/layout'
import { MultiLineChart, useChartColors } from '../components/charts'
import { SlideUp } from '../components/motion'
import ChartPanel from '../components/safegrid/ChartPanel'

export default function PowerFlow() {
  const { series, grid } = useSimulation()
  const c = useChartColors()
  const last = series[series.length - 1]
  const lineNames = Object.keys(last?.lines || {})
  const busNames = Object.keys(last?.buses || {})

  const data = useMemo(
    () =>
      series.map((s) => ({
        time: s.time,
        generation: s.generation_kw,
        load: s.load_kw,
        import: s.import_kw,
        export: s.export_kw,
        price: s.price,
        losses: s.losses_kw,
        ...Object.fromEntries(busNames.map((b) => [`bus_${b}`, s.buses?.[b]])),
        ...Object.fromEntries(lineNames.map((l) => [`line_${l}`, s.lines?.[l]])),
        ...Object.fromEntries(NODE_IDS.map((n) => [`ex_${n}`, s.nodes?.[n]?.exchange_kw])),
        ...Object.fromEntries(NODE_IDS.map((n) => [`bat_${n}`, s.nodes?.[n]?.battery_kw])),
      })),
    [series, busNames.join(), lineNames.join()], // eslint-disable-line react-hooks/exhaustive-deps
  )

  const pal = c.palette
  const kw1 = (v) => num(v, 1)
  const charts = [
    {
      title: 'Bus voltage', subtitle: 'per unit, with the 0.95 - 1.05 band', fmt: (v) => num(v, 3), domain: [0.94, 1.06],
      refs: [{ y: 1.05, label: '1.05 max' }, { y: 0.95, label: '0.95 min' }],
      series: busNames.map((b, i) => ({ key: `bus_${b}`, label: b, color: pal[i % pal.length] })),
    },
    {
      title: 'Line loading', subtitle: 'percent of rated current', fmt: (v) => `${num(v, 0)}%`, domain: [0, (max) => Math.max(110, Math.ceil(max))], refs: [{ y: 100, label: '100% limit' }],
      series: lineNames.map((l, i) => ({ key: `line_${l}`, label: l, color: pal[i % pal.length] })),
    },
    { title: 'Net exchange per node', subtitle: 'kW, positive = import', fmt: kw1, series: NODE_IDS.map((n) => ({ key: `ex_${n}`, label: n, color: c.node[n] })) },
    { title: 'Battery power per node', subtitle: 'kW, positive = charging', fmt: kw1, series: NODE_IDS.map((n) => ({ key: `bat_${n}`, label: n, color: c.node[n] })) },
    { title: 'Generation and consumption', subtitle: 'kW, whole feeder', fmt: kw1, series: [{ key: 'generation', label: 'Generation', color: c.accent, area: true }, { key: 'load', label: 'Consumption', color: c.danger }] },
    { title: 'Imports and exports', subtitle: 'kW at the external grid', fmt: kw1, series: [{ key: 'import', label: 'Import', color: c.info }, { key: 'export', label: 'Export', color: c.warn }] },
    { title: 'Electricity price', subtitle: 'INR per kWh, illustrative tariff', fmt: kw1, series: [{ key: 'price', label: 'Price', color: c.violet }] },
    { title: 'Network losses', subtitle: 'kW', fmt: (v) => num(v, 3), series: [{ key: 'losses', label: 'Losses', color: c.text3 }] },
  ]

  return (
    <div className="stack">
      <PageHeader title="Power flow" description="Results of the AC power flow after the validated actions of each step." />
      {grid?.converged === false && (
        <div className="notice danger" role="alert">
          <TriangleAlert size={18} aria-hidden="true" /> The last power flow did not converge. Values for that step may be unreliable.
        </div>
      )}
      <div className="grid grid-2">
        {charts.map((ch, i) => (
          <SlideUp key={ch.title} inView delay={(i % 2) * 0.06}>
            <ChartPanel cta={i === 0} title={ch.title} subtitle={ch.subtitle} legend={ch.series.map((s) => ({ label: s.label, color: s.color }))}>
              <MultiLineChart data={data} series={ch.series} valueFormat={ch.fmt} yDomain={ch.domain} refs={ch.refs} />
            </ChartPanel>
          </SlideUp>
        ))}
      </div>
    </div>
  )
}
