import { useEffect, useState } from 'react'
import api, { errorText } from '../api'
import { ErrorBox, Spinner, Stat } from '../components/ui.jsx'

const pct = (v) => (v == null ? '-' : `${(v * 100).toFixed(1)}%`)
const ms = (v) => (v == null ? '-' : `${v.toFixed ? v.toFixed(1) : v} ms`)

function Confusion({ block }) {
  const [hover, setHover] = useState(null)
  const { labels, confusion } = block
  const n = labels.length
  return (
    <div className="min-w-0">
      <div className="text-xs text-slate-500 h-5 mb-1">
        {hover ? <>true <b>{labels[hover[0]]}</b> → predicted <b>{labels[hover[1]]}</b>: {confusion[hover[0]][hover[1]]}</> : 'Rows: true sign, columns: predicted sign. Hover a cell.'}
      </div>
      <div className="overflow-x-auto">
        <div className="grid gap-px bg-slate-100 w-max" style={{ gridTemplateColumns: `90px repeat(${n}, 12px)` }} onMouseLeave={() => setHover(null)}>
          {confusion.map((row, i) => {
            const total = row.reduce((a, b) => a + b, 0) || 1
            return [
              <div key={`l${i}`} className="text-[9px] leading-3 text-right pr-1 bg-white truncate">{labels[i].replaceAll('_', ' ')}</div>,
              ...row.map((v, j) => {
                const a = v / total
                const bg = v === 0 ? '#fff' : i === j ? `rgba(79,70,229,${0.25 + 0.75 * a})` : `rgba(225,29,72,${0.25 + 0.75 * a})`
                return <div key={`${i}-${j}`} className="w-3 h-3" style={{ background: bg }} onMouseEnter={() => setHover([i, j])} />
              }),
            ]
          })}
        </div>
      </div>
    </div>
  )
}

function PerClass({ rows }) {
  const sorted = [...rows].sort((a, b) => a.f1 - b.f1)
  return (
    <div className="max-h-72 overflow-y-auto">
      <table className="w-full text-sm">
        <thead className="text-xs text-slate-500 sticky top-0 bg-white"><tr><th className="text-left py-1">Sign</th><th>Precision</th><th>Recall</th><th>F1</th><th>Test</th></tr></thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.label} className="border-t border-slate-100 text-center">
              <td className="text-left py-1">{r.label.replaceAll('_', ' ')}</td><td>{pct(r.precision)}</td><td>{pct(r.recall)}</td>
              <td className={r.f1 < 0.6 ? 'text-rose-600 font-medium' : ''}>{pct(r.f1)}</td><td>{r.support}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Performance() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('words')
  const load = () => { setError(''); api.get('/metrics').then((r) => setData(r.data)).catch((e) => setError(errorText(e))) }
  useEffect(load, [])

  if (error) return <ErrorBox error={error} onRetry={load} />
  if (!data) return <Spinner label="Loading evaluation..." />
  const ev = data.evaluation
  if (!ev) return <div className="card p-6 text-sm text-slate-600">No evaluation yet. Run <code>python -m ml.eval</code> to produce the numbers.</div>
  const lat = ev.latency
  const block = ev[tab]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-semibold text-lg">Model performance</h2>
        <p className="text-sm text-slate-500">Held-out test data, measured on this computer's CPU · generated {new Date(ev.generated_at).toLocaleString()}</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Word accuracy" value={pct(ev.words.accuracy)} hint={`top-3 ${pct(ev.words.top3_accuracy)} · ${ev.words.n_test} test signs`} />
        <Stat label="Fingerspelling accuracy" value={pct(ev.letters.accuracy)} hint={`${ev.letters.n_test} test images · 35 classes`} />
        <Stat label="Continuous signing" value={pct(ev.continuous?.sign_accuracy)} hint={`${ev.continuous?.n_sequences} sequences · WER ${pct(ev.continuous?.word_error_rate)}`} />
        <Stat label="Frame latency" value={ms(lat.frame_total_ms.mean)} hint={`p95 ${ms(lat.frame_total_ms.p95)} · ~${lat.max_fps} FPS possible`} />
      </div>

      <div className="card p-5">
        <div className="flex gap-1 mb-4">
          {[['words', 'Words'], ['letters', 'Fingerspelling']].map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${tab === k ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100'}`}>{label}</button>
          ))}
          <div className="ml-auto text-sm text-slate-500 self-center">accuracy {pct(block.accuracy)} · macro F1 {pct(block.macro_f1)}</div>
        </div>
        <div className="grid xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] gap-6">
          <Confusion block={block} />
          <PerClass rows={block.per_class} />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-5 min-w-0">
          <h3 className="font-semibold mb-3">Latency (CPU)</h3>
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-500"><tr><th className="text-left">Stage</th><th>Mean</th><th>p50</th><th>p95</th></tr></thead>
            <tbody>
              {[['Landmarks (MediaPipe)', lat.landmarks_ms], ['Word model (ONNX)', lat.word_model_ms], ['Letter model (ONNX)', lat.letter_model_ms], ['Whole frame', lat.frame_total_ms], ['Sentence (rules)', lat.sentence_rules_ms], ['Speech-to-text per utterance', lat.speech_to_text_ms], ['Text-to-speech per sentence', lat.text_to_speech_ms]]
                .filter(([, v]) => v).map(([label, v]) => (
                  <tr key={label} className="border-t border-slate-100 text-center"><td className="text-left py-1">{label}</td><td>{ms(v.mean)}</td><td>{ms(v.p50)}</td><td>{ms(v.p95)}</td></tr>
                ))}
            </tbody>
          </table>
          {data.live?.frames > 0 && <p className="text-xs text-slate-500 mt-3">Live since server start: {data.live.frames} frames, average {ms(data.live.avg_frame_ms)}{data.live.p95_frame_ms && <>, p95 {ms(data.live.p95_frame_ms)}</>}.</p>}
        </div>
        <div className="card p-5 space-y-3 text-sm">
          <h3 className="font-semibold">Reliability</h3>
          {ev.words_live_pipeline && <p><b>{pct(ev.words_live_pipeline.accuracy)}</b> accuracy on {ev.words_live_pipeline.n_test} test clips re-extracted with SignBridge's own live landmark pipeline ({ev.words_live_pipeline.n_classes} words), versus {pct(ev.words_live_pipeline.same_clips_reference_accuracy)} on the same takes from the reference landmarks.</p>}
          {ev.robustness && <p>Under camera noise (rotation, scale, jitter, dropped hand frames) word accuracy is <b>{pct(ev.robustness.word_accuracy_perturbed)}</b>; mirrored (left-handed) signing gives <b>{pct(ev.robustness.word_accuracy_mirrored)}</b>.</p>}
          {ev.speech && <p>Speech-to-text word error rate on {ev.speech.n_phrases} synthesised phrases: <b>{pct(ev.speech.word_error_rate)}</b> (real-time factor {ev.speech.real_time_factor}).</p>}
          {ev.sentence && <p>Rule-based sentence formation matches the reference wording on <b>{ev.sentence.exact_match}/{ev.sentence.n}</b> gloss sequences.</p>}
          {ev.continuous && <p>Continuous signing: {ev.continuous.n_sequences} sequences of {ev.continuous.signs_per_sequence} signs streamed frame-by-frame through the live segmenter; {pct(ev.continuous.sequence_exact)} fully correct.</p>}
        </div>
      </div>
    </div>
  )
}
