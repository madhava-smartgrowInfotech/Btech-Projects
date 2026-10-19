import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { BarChart3, Play } from 'lucide-react'
import {
  Alert, Button, Card, EmptyState, ErrorState, Input, KeyValueList, PageHeader, Select, Skeleton, SkeletonBlock, StatCard, Switch, Table, Tabs, useToast,
} from '../components/ui'
import { api } from '../lib/api'
import { fmtDate, fmtNum } from '../lib/format'
import { useAsync } from '../lib/useAsync'
import { useMeta } from '../lib/meta'

// Recharts is heavy: only fetched when this screen has data to chart.
const BarBlocks = lazy(() => import('../components/ui/Charts').then((m) => ({ default: m.BarBlocks })))

const CHART_METRICS = [
  { key: 'prompt_story_similarity', label: 'Topic similarity' },
  { key: 'story_time_s', label: 'Story latency (s)' },
  { key: 'tts_time_s', label: 'TTS latency (s)' },
  { key: 'rtf', label: 'Real-time factor' },
  { key: 'wer', label: 'WER' },
  { key: 'cer', label: 'CER' },
]

const num = (v, d = 3) => (v === null || v === undefined ? '—' : fmtNum(v, d))

function Running({ since }) {
  const [sec, setSec] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setSec(Math.floor((Date.now() - since) / 1000)), 500)
    return () => clearInterval(t)
  }, [since])
  return (
    <Card className="busy-card" aria-busy="true">
      <span className="eyebrow">Evaluation running</span>
      <span className="elapsed" role="timer" aria-label="Elapsed time">{sec}s</span>
      <div className="progress progress-indeterminate" role="progressbar" aria-label="Running evaluation" />
      <p className="small muted" role="status">Generating stories, narrating and transcribing them. On CPU this can take several minutes - keep this tab open.</p>
    </Card>
  )
}

export default function Evaluation() {
  const toast = useToast()
  const { languages } = useMeta()
  const { loading, error, data, reload } = useAsync(() => api.evaluations(), [])
  const [selected, setSelected] = useState(0)
  const [tab, setTab] = useState('overview')
  const [metric, setMetric] = useState('rtf')
  const [opts, setOpts] = useState({ samples: 5, language_code: '', skip_tts: false, skip_story: false })
  const [runningSince, setRunningSince] = useState(null)
  const [runError, setRunError] = useState(null)

  const runs = data || []
  const run = runs[Math.min(selected, Math.max(0, runs.length - 1))]
  const m = run?.metrics_json
  const avg = m?.averages || {}
  const samples = m?.samples || []

  const chartData = useMemo(
    () => samples.filter((s) => typeof s[metric] === 'number').map((s, i) => ({ name: `${i + 1}·${s.language_code}`, value: s[metric], prompt: s.prompt })),
    [samples, metric],
  )

  async function start(e) {
    e.preventDefault()
    const n = Math.max(1, Math.min(30, parseInt(opts.samples, 10) || 5))
    setRunError(null)
    setRunningSince(Date.now())
    try {
      const body = { samples: n, skip_tts: opts.skip_tts, skip_story: opts.skip_story }
      if (opts.language_code) body.language_code = opts.language_code
      await api.runEvaluation(body)
      reload()
      setSelected(0)
      setTab('overview')
      toast.success('Evaluation complete. Results are saved under data/evaluations.')
    } catch (err) {
      setRunError(err.message)
      toast.error(err.message)
    } finally {
      setRunningSince(null)
    }
  }

  const sampleCols = [
    { key: 'prompt', label: 'Prompt', render: (r) => <span className="prompt-cell">{r.prompt}</span> },
    { key: 'language_code', label: 'Lang' },
    { key: 'story_time_s', label: 'Story s', numeric: true, render: (r) => num(r.story_time_s) },
    { key: 'tts_time_s', label: 'TTS s', numeric: true, render: (r) => num(r.tts_time_s) },
    { key: 'audio_duration_s', label: 'Audio s', numeric: true, render: (r) => num(r.audio_duration_s, 2) },
    { key: 'rtf', label: 'RTF', numeric: true, render: (r) => num(r.rtf) },
    { key: 'wer', label: 'WER', numeric: true, render: (r) => num(r.wer) },
    { key: 'cer', label: 'CER', numeric: true, render: (r) => num(r.cer) },
    { key: 'prompt_story_similarity', label: 'Similarity', numeric: true, render: (r) => num(r.prompt_story_similarity) },
  ]

  return (
    <>
      <PageHeader
        eyebrow="Evaluation"
        title="Pipeline metrics"
        description="Every number is computed from real StoryVox outputs at evaluation time: intelligibility (WER/CER via transcription), topic similarity, latency and real-time factor. Nothing is pre-filled."
      />

      <Card title="Run an evaluation" as="form" onSubmit={start} noValidate style={{ marginBottom: 28 }}>
        <div className="eval-run">
          <Input label="Samples" type="number" min={1} max={30} value={opts.samples} onChange={(e) => setOpts({ ...opts, samples: e.target.value })} hint="1 to 30; the built-in set has 5 prompts" disabled={!!runningSince} />
          <Select label="Language" hint="Filters the built-in prompts" value={opts.language_code} onChange={(e) => setOpts({ ...opts, language_code: e.target.value })} disabled={!!runningSince}
            options={[{ value: '', label: 'Mixed (built-in set)' }, ...languages.map((l) => ({ value: l.code, label: l.name }))]} />
          <Switch label="Skip narration" checked={opts.skip_tts} onChange={(v) => setOpts({ ...opts, skip_tts: v })} disabled={!!runningSince} />
          <Switch label="Skip story model" checked={opts.skip_story} onChange={(v) => setOpts({ ...opts, skip_story: v })} disabled={!!runningSince} />
          <Button type="submit" variant="primary" icon={Play} loading={!!runningSince}>Run evaluation</Button>
        </div>
        {runError && <div style={{ marginTop: 16 }}><Alert tone="error">{runError}</Alert></div>}
      </Card>

      {runningSince && <div style={{ marginBottom: 28 }}><Running since={runningSince} /></div>}

      {loading && !data ? (
        <SkeletonBlock rows={6} label="Loading evaluations" />
      ) : error ? (
        <ErrorState title="Could not load evaluations" error={error} onRetry={reload} />
      ) : !run ? (
        <EmptyState icon={BarChart3} title="Not run yet">
          No evaluation has been run on this machine. Press Run evaluation to compute real metrics.
        </EmptyState>
      ) : (
        <div className="stack" style={{ '--gap': '24px' }}>
          {runs.length > 1 && (
            <Select label="Evaluation run" value={selected} onChange={(e) => setSelected(Number(e.target.value))}
              options={runs.map((r, i) => ({ value: i, label: `${fmtDate(r.created_at)} · ${r.sample_count} sample${r.sample_count === 1 ? '' : 's'} · ${r.language_code}` }))} />
          )}

          <div className="eval-stats">
            <StatCard label="Samples" value={m.sample_count ?? 0} />
            <StatCard label="WER" value={avg.wer ?? '—'} decimals={3} hint={avg.wer == null ? 'Needs narration + transcription' : 'Lower is clearer'} />
            <StatCard label="CER" value={avg.cer ?? '—'} decimals={3} hint={avg.cer == null ? 'Needs narration + transcription' : 'Lower is clearer'} />
            <StatCard label="Topic similarity" value={avg.prompt_story_similarity ?? '—'} decimals={3} hint="Prompt vs story" />
            <StatCard label="Story latency" value={avg.story_time_s ?? '—'} decimals={2} hint="seconds per story" />
            <StatCard label="TTS latency" value={avg.tts_time_s ?? '—'} decimals={2} hint="seconds per narration" />
            <StatCard label="RTF" value={avg.rtf ?? '—'} decimals={3} hint="Below 1.0 is faster than real time" />
            <StatCard label="ROUGE-L" value={avg.rougeL_prompt_vs_story ?? '—'} decimals={3} hint="Prompt vs story overlap" />
          </div>

          <Tabs label="Evaluation sections" value={tab} onChange={setTab}
            tabs={[{ id: 'overview', label: 'Chart' }, { id: 'samples', label: 'Samples', count: samples.length }, { id: 'method', label: 'Method & provenance' }]} />

          {tab === 'overview' && (
            <Card title="Per-sample results">
              <div style={{ maxWidth: 320, marginBottom: 16 }}>
                <Select label="Metric" value={metric} onChange={(e) => setMetric(e.target.value)} options={CHART_METRICS.map((c) => ({ value: c.key, label: c.label }))} />
              </div>
              {chartData.length ? (
                <Suspense fallback={<Skeleton height={280} />}>
                  <BarBlocks data={chartData} xKey="name" yKey="value" name={CHART_METRICS.find((c) => c.key === metric).label} labelKey="prompt" />
                </Suspense>
              ) : (
                <EmptyState title="Nothing to chart">This run has no values for this metric - for example WER needs narration and transcription to have run.</EmptyState>
              )}
            </Card>
          )}

          {tab === 'samples' && (
            samples.length ? <Table columns={sampleCols} rows={samples} rowKey={(r, i) => i} pageSize={8} caption="Per-sample evaluation results" />
              : <EmptyState title="No sample rows">This run did not record per-sample results.</EmptyState>
          )}

          {tab === 'method' && (
            <div className="grid grid-2">
              <Card title="Provenance">
                <KeyValueList items={[
                  { label: 'Computed', value: fmtDate(m.created_at) },
                  { label: 'Type', value: m.evaluation_type },
                  { label: 'Languages', value: (m.languages || []).join(', ') },
                  { label: 'Story model', value: m.story_model },
                  { label: 'ASR model', value: m.asr_model },
                  { label: 'Similarity', value: samples[0]?.similarity_method },
                ]} />
              </Card>
              <Card title="What the metrics mean">
                <KeyValueList items={Object.entries(m.metric_notes || {}).map(([label, value]) => ({ label, value }))} />
              </Card>
            </div>
          )}
        </div>
      )}
    </>
  )
}
