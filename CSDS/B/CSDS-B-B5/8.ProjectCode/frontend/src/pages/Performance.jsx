import { Activity, Gauge, Hand, Languages, Timer } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Tooltip as RTooltip, XAxis, YAxis } from 'recharts'
import api, { describeError } from '../api'
import { SlideUp, Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../components/ui/charts'
import { Card, KeyValueList, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton } from '../components/ui/feedback'
import { TabPanel, Tabs } from '../components/ui/nav'
import Table from '../components/ui/Table'
import { label as pretty, ms, pct, stamp } from '../format'

const TABS = [{ id: 'words', label: 'Words' }, { id: 'letters', label: 'Fingerspelling' }]

function Confusion({ block }) {
  const [hover, setHover] = useState(null)
  const { labels, confusion } = block
  const n = labels.length
  return (
    <div className="min-w-0">
      <div className="mb-2 min-h-5 font-mono text-xs text-muted" aria-live="polite">
        {hover
          ? <>true <b className="text-fg">{pretty(labels[hover[0]])}</b> → predicted <b className="text-fg">{pretty(labels[hover[1]])}</b>: <span className="text-ok">{confusion[hover[0]][hover[1]]}</span></>
          : 'Rows: true sign · columns: predicted sign. Hover or tap a cell.'}
      </div>
      <div className="overflow-x-auto pb-2" role="img" aria-label={`Confusion matrix, ${n} classes. ${labels.length ? 'Strong diagonal means correct predictions.' : ''}`}>
        <div className="grid w-max gap-px" style={{ gridTemplateColumns: `92px repeat(${n}, 12px)` }} onMouseLeave={() => setHover(null)}>
          {confusion.map((row, i) => {
            const total = row.reduce((a, b) => a + b, 0) || 1
            return [
              <div key={`l${i}`} className="truncate bg-panel pr-1.5 text-right font-mono text-[9px] leading-3 text-muted">{pretty(labels[i])}</div>,
              ...row.map((v, j) => {
                const a = Math.round((0.25 + 0.75 * (v / total)) * 100)
                const bg = v === 0 ? 'var(--panel-2)' : `color-mix(in oklab, ${i === j ? 'var(--ok)' : 'var(--alert)'} ${a}%, transparent)`
                return <div key={`${i}-${j}`} className="h-3 w-3" style={{ background: bg }} onMouseEnter={() => setHover([i, j])} onClick={() => setHover([i, j])} />
              }),
            ]
          })}
        </div>
      </div>
    </div>
  )
}

function PerClass({ rows }) {
  const columns = [
    { key: 'label', label: 'Sign', sortable: true, defaultDir: 'asc', render: (r) => pretty(r.label) },
    { key: 'precision', label: 'Prec.', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => pct(r.precision) },
    { key: 'recall', label: 'Recall', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => pct(r.recall) },
    { key: 'f1', label: 'F1', sortable: true, defaultDir: 'asc', align: 'right', className: 'font-mono tabular-nums', render: (r) => <span className={r.f1 < 0.6 ? 'text-alert' : r.f1 < 0.9 ? 'text-warn' : ''}>{pct(r.f1)}</span> },
    { key: 'support', label: 'Test', sortable: true, align: 'right', className: 'font-mono tabular-nums' },
  ]
  return (
    <div className="max-h-80 overflow-y-auto">
      <Table columns={columns} rows={rows} rowKey={(r) => r.label} initialSort={{ key: 'f1', dir: 'asc' }} dense caption="Per-class precision, recall and F1" />
    </div>
  )
}

function LatencyChart({ lat }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  const data = [
    { stage: 'Landmarks', mean: lat.landmarks_ms?.mean, p95: lat.landmarks_ms?.p95 },
    { stage: 'Word model', mean: lat.word_model_ms?.mean, p95: lat.word_model_ms?.p95 },
    { stage: 'Letter model', mean: lat.letter_model_ms?.mean, p95: lat.letter_model_ms?.p95 },
    { stage: 'Whole frame', mean: lat.frame_total_ms?.mean, p95: lat.frame_total_ms?.p95 },
  ].filter((d) => d.mean != null)
  return (
    <>
      <ChartFrame height={240} label="Per-frame latency by stage, mean and p95 in milliseconds">
        {({ width, height }) => (
          <BarChart width={width} height={height} data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
            <CartesianGrid vertical={false} {...grid} />
            <XAxis dataKey="stage" {...axis} />
            <YAxis {...axis} unit=" ms" />
            <RTooltip cursor={{ fill: tokens.grid }} content={<MonoTooltip valueFormat={(v) => ms(v)} />} />
            <Bar dataKey="mean" name="mean" fill={tokens.ok} radius={[2, 2, 0, 0]} isAnimationActive={animate} />
            <Bar dataKey="p95" name="p95" fill={tokens.cyan} radius={[2, 2, 0, 0]} isAnimationActive={animate} />
          </BarChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'mean', color: tokens.ok }, { label: 'p95', color: tokens.cyan }]} />
    </>
  )
}

export default function Performance() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('words')
  const load = () => { setError(null); api.get('/metrics').then((r) => setData(r.data)).catch((e) => setError(describeError(e))) }
  useEffect(load, [])

  const ev = data?.evaluation
  const block = ev?.[tab]
  const lat = ev?.latency
  const latencyRows = useMemo(() => (lat ? [
    ['Landmarks (MediaPipe)', lat.landmarks_ms], ['Word model (ONNX)', lat.word_model_ms], ['Letter model (ONNX)', lat.letter_model_ms],
    ['Whole frame', lat.frame_total_ms], ['Sentence (rules)', lat.sentence_rules_ms],
    ['Speech-to-text / utterance', lat.speech_to_text_ms], ['Text-to-speech / sentence', lat.text_to_speech_ms],
  ].filter(([, v]) => v) : []), [lat])

  return (
    <>
      <PageHeader eyebrow="evaluation" title="Model performance"
        subtitle={ev ? `Held-out test data, measured on this computer's CPU · generated ${stamp(ev.generated_at)}` : 'Accuracy, confusion matrices and latency of the recognition models.'} />
      {error && <ErrorState title="Metrics" error={error} onRetry={load} />}
      {!error && !data && <PageSkeleton />}
      {data && !ev && (
        <Card title="evaluation"><EmptyState icon={Gauge} title="No evaluation yet" body="Run  python -m ml.eval  in the project folder to produce experiments/eval/metrics.json, then reload." /></Card>
      )}
      {ev && (
        <SlideUp>
          <div className="space-y-6">
            <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatCard icon={Hand} label="Word accuracy" value={ev.words.accuracy * 100} format={(v) => `${v.toFixed(1)}%`} sub={`top-3 ${pct(ev.words.top3_accuracy)} · ${ev.words.n_test} test signs`} />
              <StatCard icon={Languages} label="Fingerspelling" value={ev.letters.accuracy * 100} format={(v) => `${v.toFixed(1)}%`} tone="cyan" sub={`${ev.letters.n_test} test images · ${ev.letters.labels.length} classes`} />
              {ev.continuous && <StatCard icon={Activity} label="Continuous signing" value={ev.continuous.sign_accuracy * 100} format={(v) => `${v.toFixed(1)}%`} tone="info" sub={`${ev.continuous.n_sequences} sequences · WER ${pct(ev.continuous.word_error_rate)}`} />}
              {lat?.frame_total_ms && <StatCard icon={Timer} label="Frame latency" value={lat.frame_total_ms.mean} format={(v) => `${v.toFixed(1)} ms`} tone="warn" sub={`p95 ${ms(lat.frame_total_ms.p95)} · ~${lat.max_fps} FPS possible`} />}
            </Stagger>

            <Card title="confusion + per-class" action={<span className="hidden font-mono text-xs text-muted sm:inline">accuracy {pct(block.accuracy)} · macro F1 {pct(block.macro_f1)}</span>} bodyClass="p-4 space-y-4">
              <Tabs id="perf-tabs" tabs={TABS} value={tab} onChange={setTab} label="Vocabulary" />
              <TabPanel tabsId="perf-tabs" value={tab}>
                <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
                  <Confusion key={tab} block={block} />
                  <PerClass rows={block.per_class} />
                </div>
              </TabPanel>
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card title="latency (cpu)" bodyClass="p-4 space-y-4">
                <LatencyChart lat={lat} />
                <Table dense caption="Latency by stage" rowKey={(r) => r[0]} rows={latencyRows}
                  columns={[
                    { key: 'stage', label: 'Stage', render: (r) => r[0] },
                    { key: 'mean', label: 'Mean', align: 'right', className: 'font-mono tabular-nums', render: (r) => ms(r[1].mean) },
                    { key: 'p50', label: 'p50', align: 'right', className: 'font-mono tabular-nums', render: (r) => ms(r[1].p50) },
                    { key: 'p95', label: 'p95', align: 'right', className: 'font-mono tabular-nums', render: (r) => ms(r[1].p95) },
                  ]} />
                {data.live?.frames > 0 && (
                  <p className="font-mono text-xs text-muted">Live since server start: {data.live.frames} frames, average {ms(data.live.avg_frame_ms)}{data.live.p95_frame_ms && <>, p95 {ms(data.live.p95_frame_ms)}</>}.</p>
                )}
              </Card>

              <div className="space-y-6">
                <Card title="reliability" bodyClass="p-4">
                  <KeyValueList items={[
                    ev.words_live_pipeline && [`Live pipeline (${ev.words_live_pipeline.n_test} clips, ${ev.words_live_pipeline.n_classes} words)`, pct(ev.words_live_pipeline.accuracy)],
                    ev.words_live_pipeline && ['Same takes, reference landmarks', pct(ev.words_live_pipeline.same_clips_reference_accuracy)],
                    ev.robustness && ['Under camera noise', pct(ev.robustness.word_accuracy_perturbed)],
                    ev.robustness && ['Mirrored (left-handed) signing', pct(ev.robustness.word_accuracy_mirrored)],
                    ev.continuous && ['Sequences fully correct', pct(ev.continuous.sequence_exact)],
                    ev.speech && [`Speech-to-text WER (${ev.speech.n_phrases} phrases)`, pct(ev.speech.word_error_rate)],
                    ev.speech && ['Speech real-time factor', ev.speech.real_time_factor],
                    ev.sentence && ['Sentence rules vs reference', `${ev.sentence.exact_match} / ${ev.sentence.n}`],
                  ].filter(Boolean)} />
                  <p className="mt-3 text-xs text-dim">The live-pipeline figure is lower because those clips are low-resolution with drawn-on overlays; the models were trained on reference landmarks.</p>
                </Card>
                {data.training && (
                  <Card title="training" bodyClass="p-4">
                    <KeyValueList items={Object.entries(data.training).flatMap(([k, t]) => [
                      [`${k}: train / test samples`, `${t.train_samples} / ${t.test_samples}`],
                      [`${k}: epochs · seconds`, `${t.epochs} · ${Math.round(t.train_seconds)} s`],
                    ])} />
                  </Card>
                )}
              </div>
            </div>
          </div>
        </SlideUp>
      )}
    </>
  )
}
