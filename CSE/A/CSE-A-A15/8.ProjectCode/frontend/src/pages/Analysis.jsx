import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BarChart, Bar, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts'
import { FileSearch } from 'lucide-react'
import api, { describeError, fmtBytes, fmtMs } from '../api'
import AuthImage from '../components/AuthImage'
import SentPicker from '../components/SentPicker'
import { PageHeader } from '../components/ui/AppShell'
import { ChartFrame, MonoTooltip, useChartTheme } from '../components/ui/charts'
import { Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'

// Measures of the chosen message: PSNR/SSIM against the cover, the two pictures, histograms, bit planes, timings.
export default function Analysis() {
  const [params] = useSearchParams()
  const [picked, setPicked] = useState(null)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const id = picked?.id ?? params.get('op')
  const { tokens, axis, grid, animate } = useChartTheme()

  useEffect(() => {
    let live = true
    setData(null)
    setError(null)
    if (!id) return undefined
    api.get(`/analysis/${id}`)
      .then((r) => live && setData(r.data))
      .catch((e) => live && setError(describeError(e)))
    return () => { live = false }
  }, [id])

  const d = data
  const psnrOk = d && (d.quality.psnr_db == null || d.quality.psnr_db > 50)
  const stageRows = d && [
    { stage: 'Encrypt', ms: d.timings_ms.encrypt },
    { stage: 'Embed', ms: d.timings_ms.embed },
    { stage: 'PNG', ms: d.timings_ms.png_encode },
    { stage: 'Metrics', ms: d.timings_ms.metrics },
  ]

  return (
    <>
      <PageHeader title="Analysis"
        subtitle="How visible is the hidden data? PSNR and SSIM compare the stego image with the original cover; the histograms and bit planes show where the change lives." />

      <Card title="Message" className="mb-6" bodyClass="p-4">
        <SentPicker onChange={setPicked} />
      </Card>

      {error && <div className="mb-6"><ErrorState error={error} /></div>}
      {!id && !error && <EmptyState icon={FileSearch} title="No message selected" body="Pick a sent message above to see its measures." />}

      {id && !d && !error && (
        <div className="space-y-6" aria-busy="true" aria-label="Loading analysis">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-28" />)}</div>
          <Skeleton className="h-72 w-full" />
        </div>
      )}

      {d && (
        <div className="space-y-6">
          <Card title="Imperceptibility" eyebrow={`operation #${d.op_id}`}>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 2xl:grid-cols-6">
              <StatCard label="PSNR" value={`${d.quality.psnr_db ?? 'inf'} dB`} tone={psnrOk ? 'ok' : 'alert'} sub="above 50 dB is invisible" />
              <StatCard label="SSIM" value={String(d.quality.ssim)} tone="ok" sub="1 = identical" />
              <StatCard label="MSE" value={String(d.quality.mse)} />
              <StatCard label="Largest change" value={`${d.quality.max_abs_change} / 255`} sub="per colour value" />
              <StatCard label="Values changed" value={`${d.quality.changed_pct}%`} sub={`${d.quality.values_changed.toLocaleString('en-IN')} of ${d.quality.values_total.toLocaleString('en-IN')}`} />
              <StatCard label="Capacity used" value={`${d.capacity.used_pct}%`} sub={`${d.capacity.payload_bits_per_pixel} bits/pixel`} />
            </div>
          </Card>

          <Card title="Cover and stego, side by side">
            <div className="grid gap-4 sm:grid-cols-2">
              {[['Original cover', 'cover'], ['Stego image', 'stego']].map(([t, w]) => (
                <figure key={w} className="space-y-2">
                  <AuthImage path={`/ops/${d.op_id}/${w}`} alt={t} className="max-h-80 w-full rounded-[6px] border border-line object-contain" />
                  <figcaption className="text-center font-mono text-[11px] uppercase tracking-wider text-dim">{t}</figcaption>
                </figure>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted">
              Cover {d.capacity.width} × {d.capacity.height} px, holds up to {fmtBytes(d.capacity.max_bundle_bytes)}; this message used {fmtBytes(d.capacity.bundle_bytes)}.
            </p>
          </Card>

          <Card title="Histograms" bodyClass="p-4">
            <AuthImage path={`/analysis/${d.op_id}/histogram.png`} alt="Histograms of cover and stego" className="w-full" />
            <p className="mt-3 text-xs text-muted">
              Grey is the cover, the coloured line is the stego image. Changing only the lowest bit moves counts between neighbouring values, so the overall shape stays the same.
            </p>
          </Card>

          <Card title="Bit planes" bodyClass="p-4">
            <AuthImage path={`/analysis/${d.op_id}/bitplanes.png`} alt="Bit planes of cover and stego" className="mx-auto w-full max-w-3xl" />
            <p className="mt-3 text-xs text-muted">
              Plane 0 (least significant) is where the data goes: the stego version looks like noise in the rows that carry data. Higher planes, which make up the picture you see, are identical.
            </p>
          </Card>

          <Card title="Processing time" bodyClass="p-4">
            <ChartFrame height={200} crosshair={false} label="Processing time per stage in milliseconds">
              {({ width, height }) => (
                <BarChart width={width} height={height} data={stageRows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid {...grid} vertical={false} />
                  <XAxis dataKey="stage" {...axis} />
                  <YAxis {...axis} width={44} tickFormatter={(v) => `${Math.round(v)}`} />
                  <Tooltip cursor={{ fill: tokens.panel2 }} content={<MonoTooltip valueFormat={(v) => fmtMs(v)} />} />
                  <Bar dataKey="ms" name="time" fill={tokens.ok} isAnimationActive={animate} radius={[3, 3, 0, 0]} />
                </BarChart>
              )}
            </ChartFrame>
            <p className="mt-2 font-mono text-[11px] text-dim">Milliseconds for this message. Encrypt includes AES and the RSA key wrap.</p>
          </Card>
        </div>
      )}
    </>
  )
}
