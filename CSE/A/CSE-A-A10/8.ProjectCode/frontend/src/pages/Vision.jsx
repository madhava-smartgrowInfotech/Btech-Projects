import { Car, Gauge, ScanEye, Siren, Timer, Upload } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { describeError } from '../api'
import { LEVEL_TONE, VEHICLE } from '../format'
import { logEvent } from '../lib/activity'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button, FileDrop, Input, Switch } from '../components/ui/controls'
import { Badge, Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import { TabPanel, Tabs } from '../components/ui/nav'
import RangeField from '../components/ui/RangeField'

const TABS = [
  { id: 'synthetic', label: 'Synthetic scene' },
  { id: 'sample', label: 'YOLOv8 · sample photo' },
  { id: 'upload', label: 'YOLOv8 · upload' },
]

function Segmented({ label, value, onChange, options }) {
  return (
    <div role="radiogroup" aria-label={label}>
      <div className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-muted">{label}</div>
      <div className="inline-flex overflow-hidden rounded-[6px] border border-line-strong">
        {options.map((o) => (
          <button key={o} type="button" role="radio" aria-checked={value === o} onClick={() => onChange(o)}
            className={`h-10 px-4 font-mono text-sm transition-colors ${value === o ? 'bg-ok/15 text-ok' : 'bg-panel-2 text-muted hover:text-fg'}`}>{o}</button>
        ))}
      </div>
    </div>
  )
}

export default function Vision() {
  const [tab, setTab] = useState('synthetic')
  const [syn, setSyn] = useState({ vehicles: 9, ambulance: true, flash: 'A', seed: 3 })
  const [conf, setConf] = useState(0.3)
  const [file, setFile] = useState(null)
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const seq = useRef(0)

  const analyze = useCallback(async () => {
    const my = ++seq.current
    setLoading(true)
    setError(null)
    try {
      let r
      if (tab === 'synthetic') r = await api.get('/vision/synthetic', { params: { vehicles: syn.vehicles, ambulance: syn.ambulance, flash: syn.flash, seed: syn.seed } })
      else if (tab === 'sample') r = await api.get('/vision/sample', { params: { conf } })
      else {
        if (!file) { setRes(null); setLoading(false); return }
        const fd = new FormData()
        fd.append('file', file)
        fd.append('conf', String(conf))
        r = await api.post('/vision/analyze', fd)
      }
      if (my !== seq.current) return
      setRes(r.data)
      logEvent('pipeline', `vision ${r.data.source}: ${r.data.detections.length} vehicles · ${r.data.report.level}${r.data.report.emergency ? ' · EMERGENCY' : ''}`)
    } catch (e) {
      if (my !== seq.current) return
      setRes(null)
      setError(describeError(e))
    } finally {
      if (my === seq.current) setLoading(false)
    }
  }, [tab, syn, conf, file])

  // synthetic scenes and the sample photo re-run on every change (debounced); uploads run when a file is chosen
  useEffect(() => {
    const t = setTimeout(analyze, tab === 'synthetic' ? 250 : 120)
    return () => clearTimeout(t)
  }, [analyze, tab])

  useEffect(() => { setRes(null); setError(null) }, [tab])

  const rep = res?.report
  const classes = rep ? Object.entries(rep.counts).filter(([, n]) => n) : []

  return (
    <div>
      <PageHeader eyebrow="03 · vision" title="Vehicle detection and density"
        subtitle="Cars, bikes, buses and trucks are detected, density is computed in passenger-car units, and a red+blue light-bar cluster flags an emergency vehicle." />

      <Tabs id="vision" tabs={TABS} value={tab} onChange={setTab} label="Input source" />
      <TabPanel tabsId="vision" value={tab} className="pt-4">
        <Card title="Input">
          {tab === 'synthetic' && (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <RangeField label="Vehicles" value={syn.vehicles} min={2} max={16} onChange={(v) => setSyn((s) => ({ ...s, vehicles: v }))} />
              <div className="flex flex-col justify-end"><Switch checked={syn.ambulance} onChange={(v) => setSyn((s) => ({ ...s, ambulance: v }))} label="Ambulance present" /></div>
              <Segmented label="Flash frame" value={syn.flash} onChange={(v) => setSyn((s) => ({ ...s, flash: v }))} options={['A', 'B']} />
              <Input label="Scene seed" type="number" min={0} max={999} value={syn.seed}
                onChange={(e) => setSyn((s) => ({ ...s, seed: Math.min(999, Math.max(0, Number(e.target.value) || 0)) }))} />
            </div>
          )}
          {tab === 'sample' && (
            <div className="max-w-md">
              <RangeField label="Confidence threshold" value={conf} min={0.1} max={0.9} step={0.05} format={(v) => v.toFixed(2)} onChange={setConf} />
              <p className="mt-2 text-xs text-dim">Runs YOLOv8n on the sample street photo shipped with the model package.</p>
            </div>
          )}
          {tab === 'upload' && (
            <div className="grid gap-4 md:grid-cols-2">
              <FileDrop label="Drop a traffic camera image" accept=".jpg,.jpeg,.png,image/jpeg,image/png" multiple={false} onFiles={(fs) => setFile(fs[0] || null)} />
              <RangeField label="Confidence threshold" value={conf} min={0.1} max={0.9} step={0.05} format={(v) => v.toFixed(2)} onChange={setConf} />
            </div>
          )}
        </Card>

        <div className="mt-4 space-y-4" aria-live="polite">
          {error && <ErrorState error={error} title="Detection failed" onRetry={analyze} />}

          {tab === 'upload' && !file && !error && (
            <Card><EmptyState icon={Upload} title="Upload an image to begin" body="Choose a .jpg or .png frame from a junction camera. YOLOv8 will count the vehicles and estimate density."
              action={<Button variant="secondary" icon={Upload} onClick={() => document.querySelector('input[type=file]')?.click()}>Choose image</Button>} /></Card>
          )}

          {loading && !res && !error && (tab !== 'upload' || file) && (
            <div className="grid gap-4 lg:grid-cols-2" aria-busy="true"><Skeleton className="h-72" /><Skeleton className="h-72" /></div>
          )}

          {res && (
            <div className={loading ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card title="Camera frame" action={<Badge>{res.width}×{res.height}</Badge>}>
                  <img src={res.frame} alt="Camera frame as received" className="w-full rounded-[4px] border border-line" />
                </Card>
                <Card title="Detections" action={<Badge tone="info">{res.lightbars} light-bar cluster{res.lightbars === 1 ? '' : 's'}</Badge>}>
                  <img src={res.annotated} alt={`Detected vehicles: ${classes.map(([c, n]) => `${n} ${c}`).join(', ') || 'none'}`} className="w-full rounded-[4px] border border-line" />
                  <p className="mt-2 text-xs text-dim">Magenta ring = light-bar cluster.</p>
                </Card>
              </div>

              <Stagger className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5" gap={0.05}>
                <StatCard icon={Car} label="Vehicles detected" value={res.detections.length} sub={classes.map(([c, n]) => `${n} ${c}`).join(', ') || 'none'} tone="info" />
                <StatCard icon={Gauge} label="Density (PCU)" value={`${rep.pcu}`} sub={`${Math.round(rep.ratio * 100)}% of road capacity`} tone={LEVEL_TONE[rep.level]} />
                <StatCard icon={ScanEye} label="Congestion level" value={rep.level} sub="from PCU-weighted count" tone={LEVEL_TONE[rep.level]} />
                <StatCard icon={Siren} label="Emergency vehicle" value={rep.emergency ? 'YES' : 'no'} sub={rep.emergency ? 'red+blue light-bar found' : 'no light-bar'} tone={rep.emergency ? 'alert' : 'ok'} live={rep.emergency} />
                <StatCard icon={Timer} label="Recommended green" value={`${rep.green} s`} sub={rep.emergency ? 'pre-empt' : 'density-based'} tone="ok" />
              </Stagger>

              {res.truth_count !== null && (
                <p className="mt-3 font-mono text-xs text-muted">
                  Ground truth: {res.truth_count} vehicles · detected: {res.detections.length}. Try flash frame B - the light-bar colours swap, and detection stays stable.
                </p>
              )}

              {res.detections.length > 0 && (
                <Card title="Detections" className="mt-4" bodyClass="p-0">
                  <ul className="grid divide-y divide-line sm:grid-cols-2 sm:divide-y-0" aria-label="Detected vehicles">
                    {res.detections.slice(0, 40).map((d, i) => (
                      <li key={i} className="flex items-center gap-3 border-line px-4 py-2 text-xs sm:border-b">
                        <i className="inline-block h-2.5 w-2.5 rounded-[2px]" style={{ background: (VEHICLE[d.cls] || VEHICLE.car).color }} aria-hidden="true" />
                        <span className="w-20 font-mono text-fg">{d.cls}</span>
                        <span className="font-mono tabular-nums text-muted">conf {d.conf?.toFixed(2)}</span>
                        <span className="ml-auto font-mono text-dim">[{d.box.join(', ')}]</span>
                        {d.lightbar > 0.25 && <Badge tone="alert">light-bar</Badge>}
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          )}
        </div>

        <Card title="How it works" className="mt-4">
          <ol className="prose-case space-y-1 text-sm text-muted">
            <li><strong>YOLOv8n</strong> (COCO-pretrained) finds cars, motorbikes, buses and trucks; for synthetic frames a contour detector stands in.</li>
            <li><strong>Light-bar detector</strong> thresholds saturated red and blue in HSV and looks for touching blobs - the flashing signature of an emergency vehicle. A detection whose light-bar sits on the roof region of a vehicle box is relabelled <strong>ambulance</strong>.</li>
            <li><strong>Density</strong> = sum of passenger-car equivalents (bike 0.5, car 1, truck 2, bus 3) ÷ road capacity.</li>
            <li>The recommended green time feeds the signal controller (emergency ⇒ pre-empt).</li>
          </ol>
        </Card>
      </TabPanel>
    </div>
  )
}
