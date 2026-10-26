import { lazy, Suspense, useCallback, useState } from 'react'
import { ArrowRight, Lock } from 'lucide-react'
import { Alert, Button, Card, EmptyState, ErrorState, Skeleton, StatCard, Table, Tabs, useToast } from '../ui'
import { PALETTE } from '../ui/palette'
import { fmtInt, fmtNum } from '../../lib/format'
import { usePipeline } from '../../lib/pipeline'

/* ---- charts: Recharts lives in a lazy chunk, so pages without charts never download it ---- */
export const BarBlocks = lazy(() => import('../ui/Charts').then((m) => ({ default: m.BarBlocks })))
export const LineBlocks = lazy(() => import('../ui/ChartsMore').then((m) => ({ default: m.LineBlocks })))
export const HBarBlocks = lazy(() => import('../ui/ChartsMore').then((m) => ({ default: m.HBarBlocks })))
export const GroupedBlocks = lazy(() => import('../ui/ChartsMore').then((m) => ({ default: m.GroupedBlocks })))
export const BoxBlocks = lazy(() => import('../ui/ChartsMore').then((m) => ({ default: m.BoxBlocks })))
export const ForecastBlocks = lazy(() => import('../ui/ChartsMore').then((m) => ({ default: m.ForecastBlocks })))

/** A titled card around a lazy chart, with a plain-text summary for screen readers. */
export function ChartCard({ title, summary, height = 280, children, actions }) {
  return (
    <Card title={title} actions={actions}>
      {summary && <p className="sr-only">{summary}</p>}
      <Suspense fallback={<Skeleton height={height} />}>{children}</Suspense>
    </Card>
  )
}

/** Shows the page only when its prerequisite is met; otherwise explains what to do first, with a link. */
export function Gate({ ok, loading, title, children, to, cta }) {
  const { error, refresh } = usePipeline()
  if (error) return <ErrorState title="The API is not reachable" error={error} onRetry={refresh} />
  if (loading) return <Skeleton height={160} />
  if (ok) return children
  return (
    <EmptyState
      icon={Lock}
      title={title}
      action={
        <Button variant="primary" to={to} iconRight={ArrowRight}>
          {cta}
        </Button>
      }
    >
      This step uses the output of the one before it. Run that first and come back.
    </EmptyState>
  )
}

/** Wrap an async call with loading + error state; errors are kept for an inline Alert and a toast. */
export function useAction() {
  const toast = useToast()
  const { refresh } = usePipeline()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const run = useCallback(
    async (fn, { success, silent } = {}) => {
      setLoading(true)
      setError(null)
      try {
        const out = await fn()
        if (success) toast.success(success)
        refresh()
        return out
      } catch (e) {
        setError(e)
        if (!silent) toast.error(e.message)
        return undefined
      } finally {
        setLoading(false)
      }
    },
    [toast, refresh],
  )
  return { run, loading, error, clear: () => setError(null) }
}

export function ActionError({ error }) {
  if (!error) return null
  return (
    <Alert tone="error">
      {error.message}
      {error.status === 0 ? ' Start the backend with run.bat.' : ''}
    </Alert>
  )
}

/** RMSE / MAE / MAPE / R2 tiles. */
export function MetricTiles({ metrics }) {
  if (!metrics) return null
  const excluded = metrics.MAPE_excluded_zero_rows
  return (
    <div className="metric-grid">
      <StatCard label="RMSE" value={fmtNum(metrics.RMSE, 3)} hint="Lower is better" />
      <StatCard label="MAE" value={fmtNum(metrics.MAE, 3)} hint="Lower is better" />
      <StatCard
        label="MAPE"
        value={metrics['MAPE (%)'] === null ? '—' : `${fmtNum(metrics['MAPE (%)'], 1)}%`}
        hint={excluded !== undefined && excluded !== null ? `${fmtInt(excluded)} zero-demand rows excluded` : 'Safe MAPE'}
      />
      <StatCard label="R²" value={fmtNum(metrics.R2, 3)} hint="Higher is better" />
    </div>
  )
}

const prettyHeader = (k) => k.replaceAll('_', ' ')

/** Table over an array of flat records. Numbers right-aligned; cell formatting via `format[col]`. */
export function RecordTable({ columns, rows, format = {}, pageSize = 10, caption, empty }) {
  const cols = columns.map((c) => ({
    key: c,
    label: prettyHeader(c),
    numeric: rows.some((r) => typeof r[c] === 'number'),
    render: (r) => {
      const v = r[c]
      if (v === null || v === undefined) return '—'
      if (format[c]) return format[c](v, r)
      if (typeof v === 'number') return Number.isInteger(v) ? v.toLocaleString() : Number(v.toFixed(4)).toString()
      return String(v)
    },
    sortValue: (r) => r[c],
  }))
  return <Table columns={cols} rows={rows} pageSize={pageSize} caption={caption} empty={empty} rowKey={(r, i) => i} />
}

const METRIC_TABS = [
  { id: 'RMSE', label: 'RMSE' },
  { id: 'MAE', label: 'MAE' },
  { id: 'MAPE (%)', label: 'MAPE' },
]
const MODEL_COLOURS = [PALETTE.sky, PALETTE.lime, PALETTE.coral, PALETTE.amber]

/** Model comparison table plus a bar chart that switches between RMSE, MAE and MAPE. */
export function ComparisonPanel({ rows, chartTitle = 'Model comparison' }) {
  const [metric, setMetric] = useState('RMSE')
  if (!rows?.length) return null
  const cols = ['Model', 'RMSE', 'MAE', 'MAPE (%)', 'MAPE_excluded_zero_rows', 'R2']
  const chartRows = rows.map((r, i) => ({ ...r, value: r[metric] ?? 0, fill: MODEL_COLOURS[i % MODEL_COLOURS.length] }))
  const best = [...rows].sort((a, b) => a.RMSE - b.RMSE)[0]
  return (
    <div className="page-stack">
      <Card title="Comparison so far">
        <RecordTable
          columns={cols}
          rows={rows}
          pageSize={10}
          caption="Model metrics"
          format={{
            RMSE: (v) => v.toFixed(3),
            MAE: (v) => v.toFixed(3),
            'MAPE (%)': (v) => `${v.toFixed(1)}%`,
            R2: (v) => v.toFixed(3),
            MAPE_excluded_zero_rows: (v) => v.toLocaleString(),
          }}
        />
      </Card>
      <Card title={`${chartTitle} · ${metric === 'MAPE (%)' ? 'MAPE' : metric}`}>
        <Tabs tabs={METRIC_TABS} value={metric} onChange={setMetric} label="Metric to chart" />
        <p className="sr-only">
          {rows.map((r) => `${r.Model} ${metric} ${Number(r[metric]).toFixed(3)}`).join('. ')}. Lowest RMSE: {best.Model}.
        </p>
        <Suspense fallback={<Skeleton height={260} />}>
          <BarBlocks data={chartRows} xKey="Model" yKey="value" name={metric === 'MAPE (%)' ? 'MAPE (%)' : metric} height={260} colorFn={(d) => d.fill} />
        </Suspense>
      </Card>
    </div>
  )
}
