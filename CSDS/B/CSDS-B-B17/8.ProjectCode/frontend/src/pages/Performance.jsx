import { useEffect, useState } from 'react'
import api, { errorText, label } from '../api.js'
import { HBars } from '../components/charts.jsx'
import { Empty, ErrorBox, Spinner, Stat } from '../components/ui.jsx'

const pct = (v) => (v == null ? '-' : `${(v * 100).toFixed(1)}%`)

function Row({ name, m, extra }) {
  if (!m) return null
  return (
    <tr className="border-t border-slate-100">
      <td className="py-2 pr-3">{name}</td>
      <td className="pr-3">{m.n ?? m.test_size}</td>
      <td className="pr-3 font-medium">{pct(m.accuracy)}</td>
      <td className="font-medium">{m.macro_f1 != null ? m.macro_f1.toFixed(3) : '-'}</td>
      {extra !== undefined && <td>{extra}</td>}
    </tr>
  )
}

function Table({ children }) {
  return (
    <table className="w-full text-sm">
      <thead className="text-left text-xs uppercase text-slate-500">
        <tr>
          <th className="py-1">Test set</th>
          <th>n</th>
          <th>Accuracy</th>
          <th>Macro-F1</th>
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  )
}

export default function Performance() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const load = () =>
    api
      .get('/metrics')
      .then((r) => setData(r.data))
      .catch((err) => setError(errorText(err)))
  useEffect(() => {
    load()
  }, [])

  if (error) return <ErrorBox error={error} onRetry={load} />
  if (!data) return <Spinner />
  const tr = data.training
  const ev = data.evaluation
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Model performance</h1>
        <p className="text-sm text-slate-500">Numbers produced by ml/train.py and ml/eval.py on held-out data, the sample calls and real call recordings.</p>
      </div>
      {!tr && <Empty>No training metrics yet - run ml/train.py</Empty>}
      {ev && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Stat label="Intent accuracy (Bitext test)" value={pct(ev.intent.bitext_holdout.accuracy)} sub={`macro-F1 ${ev.intent.bitext_holdout.macro_f1}`} />
          <Stat label="Intent on sample calls" value={pct(ev.intent.sample_calls_end_to_end.accuracy)} sub={`end to end, n=${ev.intent.sample_calls_end_to_end.n}`} />
          <Stat label="WER (real recordings)" value={pct(ev.transcription.wer_call_center_recordings)} sub={`sample calls ${pct(ev.transcription.wer_sample_calls)}`} />
          <Stat label="Speaker attribution" value={pct(ev.transcription.speaker_attribution_accuracy_sample_calls)} sub="stereo sample calls" />
        </div>
      )}
      <div className="grid gap-5 lg:grid-cols-2">
        {tr && (
          <div className="card">
            <h2 className="h2">Intent classifier</h2>
            <p className="mb-2 text-xs text-slate-500">{tr.intent.model} - {tr.intent.dataset}</p>
            <Table>
              <Row name="Bitext held-out utterances" m={tr.intent} />
              {ev && <Row name="Sample calls (full pipeline)" m={ev.intent.sample_calls_end_to_end} />}
            </Table>
            <h3 className="mb-2 mt-4 text-xs font-semibold uppercase text-slate-500">Lowest per-intent F1 (Bitext test)</h3>
            <HBars
              rows={Object.entries(tr.intent.per_class_f1)
                .sort((a, b) => a[1] - b[1])
                .slice(0, 8)
                .map(([k, v]) => ({ label: k, count: v }))}
              format={(v) => v.toFixed(3)}
            />
          </div>
        )}
        {tr && (
          <div className="card">
            <h2 className="h2">Sentiment</h2>
            <p className="mb-2 text-xs text-slate-500">{tr.sentiment.model} - {tr.sentiment.dataset}</p>
            <Table>
              <Row name="Airline messages held-out" m={tr.sentiment} />
              {ev && (
                <>
                  <Row name="Sample call script lines" m={ev.sentiment.sample_call_script_lines} />
                  <Row name="Sample call customer turns (after ASR)" m={ev.sentiment.sample_call_customer_turns_end_to_end} />
                  <Row name="Real call transcripts (reference text)" m={ev.sentiment.call_center_reference_transcripts} />
                  <Row name="Real call transcripts (after ASR)" m={ev.sentiment.call_center_asr_transcripts} />
                </>
              )}
            </Table>
            <h3 className="mb-2 mt-4 text-xs font-semibold uppercase text-slate-500">Per-class F1 (airline test)</h3>
            <HBars rows={Object.entries(tr.sentiment.per_class_f1).map(([k, v]) => ({ label: k, count: v }))} format={(v) => v.toFixed(3)} color="#0d9488" />
          </div>
        )}
        {ev && (
          <div className="card">
            <h2 className="h2">Voice emotion</h2>
            <p className="mb-2 text-xs text-slate-500">{ev.voice_emotion.model} (pretrained) - neutral / happy / sad / angry</p>
            <Table>
              <Row name="RAVDESS sample" m={ev.voice_emotion.ravdess} />
              <Row name="CREMA-D sample" m={ev.voice_emotion.cremad} />
            </Table>
          </div>
        )}
        {ev && (
          <div className="card">
            <h2 className="h2">Transcription</h2>
            <p className="mb-2 text-xs text-slate-500">{ev.transcription.model}</p>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt className="text-slate-500">WER - 20 real call recordings</dt>
              <dd className="font-medium">{pct(ev.transcription.wer_call_center_recordings)}</dd>
              <dt className="text-slate-500">WER - 10 sample calls</dt>
              <dd className="font-medium">{pct(ev.transcription.wer_sample_calls)}</dd>
              <dt className="text-slate-500">Speaker attribution (stereo)</dt>
              <dd className="font-medium">{pct(ev.transcription.speaker_attribution_accuracy_sample_calls)}</dd>
            </dl>
          </div>
        )}
      </div>
      {ev && (
        <div className="card overflow-x-auto">
          <h2 className="h2">Sample calls - end-to-end results</h2>
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="py-1">Call</th>
                <th>True intent</th>
                <th>Predicted</th>
                <th>Score</th>
                <th>WER</th>
                <th>Customer emotions</th>
              </tr>
            </thead>
            <tbody>
              {ev.sample_calls.map((c) => (
                <tr key={c.call} className="border-t border-slate-100">
                  <td className="py-2">{label(c.call)}</td>
                  <td>{c.intent_true}</td>
                  <td className={c.intent_true === c.intent_pred ? 'text-green-700' : 'text-red-700'}>{c.intent_pred}</td>
                  <td>{c.score}</td>
                  <td>{pct(c.wer)}</td>
                  <td className="text-xs text-slate-600">{c.customer_emotions.join(' → ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-slate-500">{ev.notes}</p>
        </div>
      )}
      {!ev && tr && <Empty>End-to-end evaluation not run yet - run ml/eval.py</Empty>}
    </div>
  )
}
