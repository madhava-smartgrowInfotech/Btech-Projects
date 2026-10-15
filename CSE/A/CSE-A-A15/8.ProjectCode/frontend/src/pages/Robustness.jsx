import { useEffect, useState } from 'react'
import { BarChart, Bar, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts'
import { Gauge, ShieldHalf } from 'lucide-react'
import api, { describeError, fmtBytes, fmtMs } from '../api'
import SentPicker from '../components/SentPicker'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge, Card } from '../components/ui/display'
import { ChartFrame, MonoTooltip, useChartTheme } from '../components/ui/charts'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { riskVar } from '../format'

export default function Robustness() {
  const toast = useToast()
  const { tokens, axis, grid, animate } = useChartTheme()
  const [op, setOp] = useState(null)
  const [report, setReport] = useState(null)
  const [busy, setBusy] = useState(false)
  const [attackError, setAttackError] = useState(null)
  const [capacity, setCapacity] = useState(null)
  const [capError, setCapError] = useState(null)
  const [bench, setBench] = useState(null)
  const [benchBusy, setBenchBusy] = useState(false)
  const [benchError, setBenchError] = useState(null)

  const loadCapacity = () => {
    setCapError(null)
    api.get('/benchmark/capacity').then((r) => setCapacity(r.data)).catch((e) => setCapError(describeError(e)))
  }
  useEffect(() => { loadCapacity() }, [])

  useEffect(() => {
    let live = true
    setReport(null)
    setAttackError(null)
    if (op) api.get(`/robustness/${op.id}`).then((r) => live && setReport(r.data)).catch(() => {})
    return () => { live = false }
  }, [op?.id])

  async function runAttacks() {
    setBusy(true)
    setAttackError(null)
    try {
      const { data } = await api.post(`/robustness/${op.id}`)
      setReport(data)
      toast({ tone: 'ok', title: 'Attacks finished', body: `Payload survives ${data.survived.length} of ${data.results.length}.` })
    } catch (e) {
      setAttackError(describeError(e))
    } finally {
      setBusy(false)
    }
  }

  async function runBench() {
    setBenchBusy(true)
    setBenchError(null)
    try {
      const { data } = await api.post('/benchmark/run')
      setBench(data)
      toast({ tone: 'ok', title: 'Benchmark finished', body: `${data.rows.length} runs across the sample covers.` })
    } catch (e) {
      setBenchError(describeError(e))
    } finally {
      setBenchBusy(false)
    }
  }

  const jpegLost = report?.results.some((r) => r.attack.startsWith('jpeg') && r.status !== 'recovered')
  const berRows = report?.results.map((r) => ({ name: r.label, ber: r.bit_error_rate == null ? 0 : r.bit_error_rate * 100 }))

  const attackCols = [
    { key: 'attack', label: 'Attack', render: (r) => <>
      <span className="font-medium text-fg">{r.label}</span>
      <div className="font-mono text-[11px] text-dim">{r.size}</div>
    </> },
    { key: 'status', label: 'Result', render: (r) => (
      <Badge tone={r.status === 'recovered' ? 'ok' : 'alert'} dot>{r.status === 'recovered' ? 'payload survives' : 'payload lost'}</Badge>
    ) },
    { key: 'ber', label: 'LSB error rate', align: 'right', render: (r) => (
      <span className="font-mono text-xs tabular-nums" style={{ color: r.bit_error_rate == null ? undefined : riskVar(r.bit_error_rate) }}>
        {r.bit_error_rate == null ? '-' : `${(r.bit_error_rate * 100).toFixed(1)}%`}
      </span>
    ) },
    { key: 'why', label: 'What happened', className: 'text-muted min-w-[16rem]', render: (r) => <>
      {r.why}
      <div className="mt-0.5 font-mono text-[11px] text-dim">{r.detail}</div>
    </> },
  ]

  const capColumns = [
    { key: 'cover', label: 'Cover', render: (c) => <span className="font-medium text-fg">{c.cover}</span> },
    { key: 'size', label: 'Size (px)', render: (c) => `${c.width} × ${c.height}` },
    { key: 'max', label: 'Maximum hidden', align: 'right', render: (c) => fmtBytes(c.max_bundle_bytes) },
    { key: 'bpp', label: 'Bits / pixel', align: 'right', render: (c) => c.max_bits_per_pixel },
  ]

  const benchCell = (r, f) => (r.fits ? f(r) : '-')
  const benchCols = [
    { key: 'cover', label: 'Cover', render: (r) => r.cover },
    { key: 'payload', label: 'Payload', render: (r) => fmtBytes(r.payload_bytes) },
    { key: 'used', label: 'Used', render: (r) => (r.fits ? `${r.used_pct}%` : <span className="text-dim">does not fit - blocked by the capacity check</span>) },
    { key: 'psnr', label: 'PSNR', align: 'right', render: (r) => benchCell(r, (x) => `${x.psnr_db} dB`) },
    { key: 'ssim', label: 'SSIM', align: 'right', render: (r) => benchCell(r, (x) => x.ssim) },
    { key: 'enc', label: 'Encrypt', align: 'right', render: (r) => benchCell(r, (x) => fmtMs(x.encrypt_ms)) },
    { key: 'emb', label: 'Embed', align: 'right', render: (r) => benchCell(r, (x) => fmtMs(x.embed_ms)) },
    { key: 'ext', label: 'Extract', align: 'right', render: (r) => benchCell(r, (x) => fmtMs(x.extract_ms)) },
    { key: 'dec', label: 'Decrypt', align: 'right', render: (r) => benchCell(r, (x) => fmtMs(x.decrypt_ms)) },
  ]

  return (
    <>
      <PageHeader title="Robustness and benchmark"
        subtitle="LSB hiding survives lossless handling and nothing else. This page attacks a stego image and states exactly what lives and what dies, then measures capacity and speed across covers." />

      <div className="space-y-6">
        <Card title="Attack a stego image" bodyClass="space-y-4 p-4">
          <SentPicker onChange={setOp} />
          <Button icon={ShieldHalf} loading={busy} disabled={!op} onClick={runAttacks}>
            {busy ? 'Recompressing, adding noise, cropping…' : 'Run robustness tests'}
          </Button>
          <ErrorState error={attackError} />

          {busy && <Skeleton className="h-64 w-full" />}

          {report && !busy && (
            <>
              <Table
                caption="Robustness results per attack"
                columns={attackCols}
                rows={report.results}
                rowKey={(r) => r.attack}
                cards={(r) => (
                  <div className="panel space-y-1 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-fg">{r.label}</span>
                      <Badge tone={r.status === 'recovered' ? 'ok' : 'alert'} dot>{r.status === 'recovered' ? 'survives' : 'lost'}</Badge>
                    </div>
                    <div className="text-xs text-muted">{r.why}</div>
                  </div>
                )}
              />

              <ChartFrame height={44 * berRows.length + 40} crosshair={false} label="LSB error rate per attack, percent">
                {({ width, height }) => (
                  <BarChart width={width} height={height} data={berRows} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
                    <CartesianGrid {...grid} horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} {...axis} />
                    <YAxis type="category" dataKey="name" width={190} {...axis} />
                    <Tooltip cursor={{ fill: tokens.panel2 }} content={<MonoTooltip valueFormat={(v) => `${v.toFixed(1)}%`} />} />
                    <Bar dataKey="ber" name="LSB error rate" fill={tokens.alert} isAnimationActive={animate} radius={[0, 3, 3, 0]} />
                  </BarChart>
                )}
              </ChartFrame>

              <div className="rounded-[6px] border border-line bg-panel-2 p-3 text-sm text-muted">
                <b className="text-fg">Survives:</b> {report.survived.join(', ') || 'nothing'}. <b className="text-fg">Lost:</b> {report.lost.join(', ') || 'nothing'}.
                {jpegLost && ' JPEG recompression rewrites the lowest bits of every pixel, so the hidden bundle cannot be read back. Always send and store the stego image as PNG, and avoid chat apps or sites that re-encode pictures.'}
              </div>
            </>
          )}
        </Card>

        <Card title="Capacity per cover" bodyClass="px-4 pb-2 pt-0">
          <Table
            caption="Capacity of each sample cover"
            columns={capColumns}
            rows={capacity}
            rowKey={(c) => c.cover}
            loading={capacity === null && !capError}
            empty={capError ? <ErrorState error={capError} onRetry={loadCapacity} /> : <EmptyState title="No sample covers" body="Run scripts/make_samples.py to create them." />}
          />
        </Card>

        <Card title="Speed and quality benchmark" eyebrow="RSA-2048 · median of 2 runs" bodyClass="space-y-4 p-4">
          <p className="text-sm text-muted">
            Runs the full encrypt, embed, extract and decrypt cycle on every sample cover at 1 KiB, 16 KiB and 64 KiB payloads. It can take a little while.
          </p>
          <Button variant="secondary" icon={Gauge} loading={benchBusy} onClick={runBench}>
            {benchBusy ? 'Benchmarking…' : 'Run benchmark'}
          </Button>
          <ErrorState error={benchError} onRetry={runBench} />
          {bench && (
            <Table
              caption="Benchmark runs per cover and payload size"
              columns={benchCols}
              rows={bench.rows}
              rowKey={(r) => `${r.cover}-${r.payload_bytes}`}
              empty={<EmptyState title="No runs" body="The benchmark returned no rows." />}
            />
          )}
        </Card>
      </div>
    </>
  )
}
