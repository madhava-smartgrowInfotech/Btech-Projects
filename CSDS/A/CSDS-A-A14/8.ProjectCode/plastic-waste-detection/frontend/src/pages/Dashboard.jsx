import { useCallback, useEffect, useMemo, useState } from 'react'
import { BarChart3, Gauge, Images, RefreshCw, ScanSearch, Target, Trash2 } from 'lucide-react'
import { BarCompare, LineCompare } from '../components/charts'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Modal,
  PageHeader,
  PageSkeleton,
  StatCard,
  Table,
  useToast,
} from '../components/ui'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { fmtInt } from '../lib/format'

const COLUMNS = [
  { key: 'filename', label: 'Filename', wrap: true },
  { key: 'object_count', label: 'Objects', numeric: true },
  { key: 'avg_confidence_pct', label: 'Avg Confidence (%)', numeric: true, render: (r) => r.avg_confidence_pct.toFixed(1) },
  { key: 'timestamp', label: 'Date' },
]

/** Same aggregates as pages/2_Dashboard.py (pandas) - computed from the real history rows. */
function summarise(rows) {
  const withPct = rows.map((r) => ({ ...r, avg_confidence_pct: Math.round(r.avg_confidence * 1000) / 10 }))
  const pcts = withPct.map((r) => r.avg_confidence_pct)
  const oldestFirst = [...withPct].reverse()

  // unique x labels even when the same file was analysed twice
  const seen = new Map()
  const perImage = oldestFirst.slice(-30).map((r) => {
    const n = (seen.get(r.filename) || 0) + 1
    seen.set(r.filename, n)
    return { name: n > 1 ? `${r.filename} (${n})` : r.filename, value: r.object_count }
  })

  const lo = Math.floor(Math.min(...pcts) / 10) * 10
  const hi = Math.max(lo + 10, Math.ceil(Math.max(...pcts) / 10) * 10)
  const bins = []
  for (let s = lo; s < hi; s += 10) {
    const last = s + 10 >= hi
    bins.push({
      name: `${s}–${s + 10}`,
      value: pcts.filter((p) => p >= s && (last ? p <= s + 10 : p < s + 10)).length,
    })
  }

  return {
    rows: withPct,
    totalImages: withPct.length,
    totalObjects: withPct.reduce((a, r) => a + r.object_count, 0),
    avgConf: pcts.reduce((a, b) => a + b, 0) / pcts.length,
    maxConf: Math.max(...pcts),
    perImage,
    perImageCapped: oldestFirst.length > 30,
    bins,
    timeline: oldestFirst.map((r) => ({ x: r.timestamp, objects: r.object_count })),
  }
}

export default function Dashboard() {
  const toast = useToast()
  const [state, setState] = useState({ status: 'loading', rows: [], error: null })
  const [confirm, setConfirm] = useState(false)
  const [clearing, setClearing] = useState(false)

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setState((s) => ({ ...s, status: 'loading', error: null }))
    try {
      const rows = await api.history()
      setState({ status: 'ready', rows, error: null })
    } catch (error) {
      setState({ status: 'error', rows: [], error })
    }
  }, [])

  useEffect(() => {
    document.title = 'Dashboard · PlastiScan'
    load()
  }, [load])

  const data = useMemo(() => (state.rows.length ? summarise(state.rows) : null), [state.rows])

  const clear = async () => {
    setClearing(true)
    try {
      await api.clearHistory()
      setConfirm(false)
      toast({ kind: 'success', title: 'History cleared', message: 'All logged detection runs were removed.' })
      await load(true)
    } catch (e) {
      toast({ kind: 'error', title: 'Could not clear history', message: e.message })
    } finally {
      setClearing(false)
    }
  }

  const actions = (
    <>
      <Button variant="secondary" icon={RefreshCw} onClick={() => load()} loading={state.status === 'loading'}>
        Refresh
      </Button>
      {data && (
        <Button variant="danger" icon={Trash2} onClick={() => setConfirm(true)}>
          Clear history
        </Button>
      )}
    </>
  )

  return (
    <div>
      <PageHeader
        eyebrow="Dashboard"
        icon={BarChart3}
        title="What has been analysed so far"
        lead="Aggregate statistics built from every logged detection run. Nothing here is sample data."
        actions={actions}
      />

      {state.status === 'loading' && <PageSkeleton kpis={4} blocks={2} />}

      {state.status === 'error' && <ErrorState title="Could not load the detection history" error={state.error} onRetry={() => load()} />}

      {state.status === 'ready' && !data && (
        <EmptyState
          icon={Images}
          tone="mint"
          title="No detection history yet"
          message="Run a detection on the Detection page - every analysed image that contains at least one object is automatically logged here."
          action={<Button to="/app/detect" icon={ScanSearch}>Run a detection</Button>}
        />
      )}

      {state.status === 'ready' && data && (
        <Stagger className="stack" gap={0.06}>
          <Stagger.Item className="grid-kpi">
            <StatCard label="Total images analysed" value={data.totalImages} format={fmtInt} icon={Images} tone="lavender" />
            <StatCard label="Total plastic objects detected" value={data.totalObjects} format={fmtInt} icon={ScanSearch} tone="mint" />
            <StatCard label="Average confidence" value={data.avgConf} format={(v) => `${v.toFixed(1)}%`} icon={Gauge} tone="peach" />
            <StatCard label="Highest confidence" value={data.maxConf} format={(v) => `${v.toFixed(1)}%`} icon={Target} tone="sky" />
          </Stagger.Item>

          <Stagger.Item className="grid-2">
            <Card title="Objects detected per image" subtitle={data.perImageCapped ? 'Latest 30 runs, oldest to newest' : 'Oldest to newest'} hover={false}>
              <BarCompare
                data={data.perImage}
                name="Objects"
                label="Bar chart of objects detected per analysed image"
                valueFormat={(v) => fmtInt(v)}
                xFormat={(n) => (data.perImage.length > 5 ? `#${data.perImage.findIndex((d) => d.name === n) + 1}` : n)}
                xInterval={data.perImage.length > 14 ? 'preserveStartEnd' : 0}
                color="#A9D6FF"
                height={280}
              />
            </Card>
            <Card title="Confidence distribution" subtitle="Runs by average confidence (%)" hover={false}>
              <BarCompare
                data={data.bins}
                name="Runs"
                label="Histogram of average confidence per run"
                valueFormat={(v) => fmtInt(v)}
                color="#C7B9FF"
                height={280}
              />
            </Card>
          </Stagger.Item>

          <Stagger.Item>
            <Card title="Detection history over time" subtitle="Objects detected in each run" hover={false}>
              <LineCompare
                data={data.timeline}
                series={[{ key: 'objects', name: 'Objects detected', color: '#9D8BF5' }]}
                valueFormat={(v) => fmtInt(v)}
                xFormat={(x) => String(x).slice(5, 19)}
                label="Line chart of objects detected over time"
                height={260}
              />
            </Card>
          </Stagger.Item>

          <Stagger.Item>
            <Card
              title="Detection history"
              subtitle={`${data.totalImages} logged run${data.totalImages === 1 ? '' : 's'}, newest first`}
              actions={<Badge tone="mint">Live from the database</Badge>}
              hover={false}
            >
              <Table
                columns={COLUMNS}
                rows={data.rows}
                rowKey={(r, i) => `${r.timestamp}-${i}`}
                pageSize={10}
                searchKeys={['filename', 'timestamp']}
                searchPlaceholder="Search by filename or date"
                caption="Detection history"
                cardTitle={(r) => r.filename}
                initialSort={null}
              />
            </Card>
          </Stagger.Item>
        </Stagger>
      )}

      <Modal
        open={confirm}
        onClose={() => !clearing && setConfirm(false)}
        title="Clear all detection history?"
        description={`This permanently deletes ${data?.totalImages ?? 0} logged run${data?.totalImages === 1 ? '' : 's'} from the database. Saved images in results/ are not touched.`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirm(false)} disabled={clearing} data-autofocus>
              Keep history
            </Button>
            <Button variant="danger" icon={Trash2} loading={clearing} onClick={clear}>
              Clear history
            </Button>
          </>
        }
      />
    </div>
  )
}
