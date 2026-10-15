import { useCallback, useEffect, useState } from 'react'
import { AudioLines, Gauge, HeartPulse, MessageSquareText, Mic, Tags } from 'lucide-react'
import api, { errorText } from '../api'
import { label, pct } from '../lib/format'
import { Alert, Card, EmptyState, ErrorState, KeyValueList, PageHeader, SkeletonBlock, StatCard, Table, Tabs } from '../components/ui'
import { HBarBlocks } from '../components/ui/Charts'

const f3 = (v) => (v == null ? '—' : Number(v).toFixed(3))

function MetricTable({ rows, caption }) {
  const data = rows.filter((r) => r.m).map((r) => ({ id: r.name, name: r.name, n: r.m.n ?? r.m.test_size, accuracy: r.m.accuracy, f1: r.m.macro_f1 }))
  if (!data.length) return null
  return (
    <Table
      caption={caption}
      rows={data}
      pageSize={20}
      columns={[
        { key: 'name', label: 'Test set', sortable: false },
        { key: 'n', label: 'n', numeric: true, sortable: false },
        { key: 'accuracy', label: 'Accuracy', numeric: true, sortable: false, render: (r) => <strong>{pct(r.accuracy)}</strong> },
        { key: 'f1', label: 'Macro-F1', numeric: true, sortable: false, render: (r) => <strong>{f3(r.f1)}</strong> },
      ]}
    />
  )
}

export default function Performance() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('intent')

  const load = useCallback(async () => {
    setError('')
    try {
      const r = await api.get('/metrics')
      setData(r.data)
    } catch (err) {
      setError(errorText(err))
    }
  }, [])
  useEffect(() => {
    load()
  }, [load])

  const header = (
    <PageHeader
      eyebrow="Held-out data · sample calls · real recordings"
      title="Model performance"
      description="Numbers produced by ml/train.py and ml/eval.py. Nothing here is hand-typed."
    />
  )
  if (error) {
    return (
      <>
        {header}
        <ErrorState title="Could not load model metrics" error={error} onRetry={load} />
      </>
    )
  }
  if (!data) {
    return (
      <>
        {header}
        <SkeletonBlock rows={6} label="Loading metrics" />
      </>
    )
  }

  const tr = data.training
  const ev = data.evaluation
  if (!tr && !ev) {
    return (
      <>
        {header}
        <EmptyState icon={Gauge} title="No metrics yet">
          Run <code>ml/train.py</code> and <code>ml/eval.py</code> (setup.bat does this) and reload this page.
        </EmptyState>
      </>
    )
  }

  const tabs = [
    { id: 'intent', label: 'Intent', icon: Tags },
    { id: 'sentiment', label: 'Sentiment', icon: MessageSquareText },
    { id: 'voice', label: 'Voice emotion', icon: HeartPulse },
    { id: 'asr', label: 'Transcription', icon: Mic },
    { id: 'calls', label: 'Sample calls', icon: AudioLines },
  ]
  const f1Rows = (obj, take) =>
    Object.entries(obj || {})
      .sort((a, b) => a[1] - b[1])
      .slice(0, take)
      .map(([k, v]) => ({ label: k, count: v }))

  return (
    <>
      {header}
      <div className="stack" style={{ '--gap': '24px' }}>
        {ev && (
          <div className="grid grid-4">
            <StatCard label="Intent accuracy (Bitext test)" value={pct(ev.intent.bitext_holdout.accuracy)} hint={`macro-F1 ${ev.intent.bitext_holdout.macro_f1}`} icon={Tags} />
            <StatCard label="Intent on sample calls" value={pct(ev.intent.sample_calls_end_to_end.accuracy)} hint={`end to end, n=${ev.intent.sample_calls_end_to_end.n}`} icon={AudioLines} />
            <StatCard label="WER (real recordings)" value={pct(ev.transcription.wer_call_center_recordings)} hint={`sample calls ${pct(ev.transcription.wer_sample_calls)}`} icon={Mic} />
            <StatCard label="Speaker attribution" value={pct(ev.transcription.speaker_attribution_accuracy_sample_calls)} hint="stereo sample calls" icon={Gauge} />
          </div>
        )}
        {!tr && <Alert tone="warning">No training metrics yet — run ml/train.py.</Alert>}
        {!ev && <Alert tone="warning">End-to-end evaluation not run yet — run ml/eval.py.</Alert>}

        <div>
          <Tabs tabs={tabs} value={tab} onChange={setTab} label="Model families" />

          {tab === 'intent' &&
            (tr ? (
              <div className="grid grid-2">
                <Card title="Intent classifier">
                  <p className="small muted" style={{ marginBottom: 12 }}>
                    {tr.intent.model} — {tr.intent.dataset}
                  </p>
                  <MetricTable
                    caption="Intent classifier results"
                    rows={[
                      { name: 'Bitext held-out utterances', m: tr.intent },
                      { name: 'Sample calls (full pipeline)', m: ev?.intent.sample_calls_end_to_end },
                    ]}
                  />
                </Card>
                <Card title="Lowest per-intent F1">
                  <HBarBlocks rows={f1Rows(tr.intent.per_class_f1, 8)} name="F1" format={(v) => v.toFixed(3)} domainMax={1} ariaLabel="Lowest per-intent F1 scores" />
                </Card>
              </div>
            ) : (
              <EmptyState icon={Tags} title="No intent metrics">Run ml/train.py.</EmptyState>
            ))}

          {tab === 'sentiment' &&
            (tr ? (
              <div className="grid grid-2">
                <Card title="Sentiment">
                  <p className="small muted" style={{ marginBottom: 12 }}>
                    {tr.sentiment.model} — {tr.sentiment.dataset}
                  </p>
                  <MetricTable
                    caption="Sentiment results"
                    rows={[
                      { name: 'Airline messages held-out', m: tr.sentiment },
                      { name: 'Sample call script lines', m: ev?.sentiment.sample_call_script_lines },
                      { name: 'Sample call customer turns (after ASR)', m: ev?.sentiment.sample_call_customer_turns_end_to_end },
                      { name: 'Real call transcripts (reference text)', m: ev?.sentiment.call_center_reference_transcripts },
                      { name: 'Real call transcripts (after ASR)', m: ev?.sentiment.call_center_asr_transcripts },
                    ]}
                  />
                </Card>
                <Card title="Per-class F1 (airline test)">
                  <HBarBlocks rows={f1Rows(tr.sentiment.per_class_f1, 10)} name="F1" format={(v) => v.toFixed(3)} domainMax={1} color="#7cc6ff" ariaLabel="Per-class sentiment F1" />
                </Card>
              </div>
            ) : (
              <EmptyState icon={MessageSquareText} title="No sentiment metrics">Run ml/train.py.</EmptyState>
            ))}

          {tab === 'voice' &&
            (ev ? (
              <Card title="Voice emotion">
                <p className="small muted" style={{ marginBottom: 12 }}>
                  {ev.voice_emotion.model} (pretrained) — neutral / happy / sad / angry
                </p>
                <MetricTable
                  caption="Voice emotion results"
                  rows={[
                    { name: 'RAVDESS sample', m: ev.voice_emotion.ravdess },
                    { name: 'CREMA-D sample', m: ev.voice_emotion.cremad },
                  ]}
                />
              </Card>
            ) : (
              <EmptyState icon={HeartPulse} title="No voice-emotion metrics">Run ml/eval.py.</EmptyState>
            ))}

          {tab === 'asr' &&
            (ev ? (
              <Card title="Transcription">
                <p className="small muted" style={{ marginBottom: 12 }}>
                  {ev.transcription.model}
                </p>
                <KeyValueList
                  items={[
                    { label: 'WER — real call recordings', value: pct(ev.transcription.wer_call_center_recordings) },
                    { label: 'WER — sample calls', value: pct(ev.transcription.wer_sample_calls) },
                    { label: 'Speaker attribution (stereo)', value: pct(ev.transcription.speaker_attribution_accuracy_sample_calls) },
                  ]}
                />
              </Card>
            ) : (
              <EmptyState icon={Mic} title="No transcription metrics">Run ml/eval.py.</EmptyState>
            ))}

          {tab === 'calls' &&
            (ev ? (
              <Card title="Sample calls — end-to-end results">
                <Table
                  caption="Sample calls, end to end"
                  rows={ev.sample_calls.map((c) => ({ ...c, id: c.call }))}
                  pageSize={10}
                  columns={[
                    { key: 'call', label: 'Call', render: (c) => <span style={{ textTransform: 'capitalize' }}>{label(c.call)}</span> },
                    { key: 'intent_true', label: 'True intent', render: (c) => label(c.intent_true) },
                    {
                      key: 'intent_pred',
                      label: 'Predicted',
                      render: (c) => (
                        <strong className={c.intent_true === c.intent_pred ? 'pos' : 'neg'}>
                          {label(c.intent_pred)} {c.intent_true === c.intent_pred ? '✓' : '✗'}
                        </strong>
                      ),
                    },
                    { key: 'score', label: 'Score', numeric: true },
                    { key: 'wer', label: 'WER', numeric: true, render: (c) => pct(c.wer) },
                    { key: 'customer_emotions', label: 'Customer emotions', sortable: false, render: (c) => c.customer_emotions.join(' → ') },
                  ]}
                />
                {ev.notes && <p className="small muted metric-note" style={{ marginTop: 16 }}>{ev.notes}</p>}
              </Card>
            ) : (
              <EmptyState icon={AudioLines} title="No end-to-end results">Run ml/eval.py.</EmptyState>
            ))}
        </div>
      </div>
    </>
  )
}
