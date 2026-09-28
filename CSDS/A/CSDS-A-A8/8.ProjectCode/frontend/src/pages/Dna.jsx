import { useEffect, useState } from 'react'
import { Play } from 'lucide-react'
import api, { errorText } from '../api.js'
import { ErrorBox, PageTitle, ReportCard, Spinner, Stat } from '../components/Ui.jsx'

function Probs({ probs, best }) {
  return (
    <div className="space-y-1.5">
      {Object.entries(probs).map(([k, v]) => (
        <div key={k} className="flex items-center gap-2 text-sm">
          <span className={`w-36 shrink-0 ${k === best ? 'font-semibold text-slate-900' : 'text-slate-600'}`}>{k}</span>
          <div className="h-2.5 flex-1 rounded bg-slate-100"><div className={`h-2.5 rounded ${k === best ? 'bg-teal-600' : 'bg-slate-300'}`} style={{ width: `${v * 100}%` }} /></div>
          <span className="w-12 text-right text-xs text-slate-500">{(v * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  )
}

export default function Dna() {
  const [samples, setSamples] = useState([])
  const [seq, setSeq] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [res, setRes] = useState(null)

  useEffect(() => {
    api.get('/dna/samples').then((r) => setSamples(r.data)).catch((e) => setError(errorText(e)))
  }, [])

  const run = async () => {
    setLoading(true)
    setError('')
    setRes(null)
    try {
      setRes((await api.post('/dna/classify', { sequence: seq })).data)
    } catch (e) {
      setError(errorText(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageTitle title="DNA analysis" subtitle="Paste a DNA sequence (raw bases or FASTA). The k-mer JEPA encoder classifies its STR repeat type and organism class; an exact scan lists tandem repeats." />
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="card space-y-4">
          <div>
            <label className="label">Sequence</label>
            <textarea className="input h-48 font-mono text-xs" value={seq} onChange={(e) => setSeq(e.target.value)} placeholder=">read_1&#10;ACGTTGCA..." />
          </div>
          <div>
            <label className="label">Sample sequences</label>
            <div className="flex flex-wrap gap-1.5">
              {samples.map((s) => (
                <button key={s.name} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700 hover:bg-teal-50" onClick={() => { setSeq(s.sequence); setRes(null) }}>{s.name}</button>
              ))}
            </div>
          </div>
          <button className="btn w-full" disabled={loading || !seq.trim()} onClick={run}>
            {loading ? <Spinner text="Classifying and writing report..." /> : <><Play size={16} /> Classify sequence</>}
          </button>
          <ErrorBox error={error} />
        </div>
        <div className="space-y-5 lg:col-span-2">
          {!res && !loading && <div className="card text-sm text-slate-500">Results appear here.</div>}
          {res && (
            <>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Stat label="Length" value={`${res.sequence.length} bp`} hint={res.sequence.id} />
                <Stat label="GC content" value={`${res.sequence.gc_percent}%`} />
                <Stat label="Windows analysed" value={res.sequence.windows_analysed} hint="99 bp, 96 4-mer tokens each" />
                <Stat label="Exact repeats found" value={res.repeat_scan.length} />
              </div>
              <div className="grid gap-5 md:grid-cols-2">
                <div className="card">
                  <h2 className="font-semibold text-slate-900">STR repeat type</h2>
                  <p className="mb-3 text-xs text-slate-500">Strongest window #{res.repeat_type.strongest_window} · model held-out accuracy {res.repeat_type.model_test_accuracy}</p>
                  <div className="mb-3 text-2xl font-semibold text-teal-700">{res.repeat_type.prediction}</div>
                  <Probs probs={res.repeat_type.probabilities} best={res.repeat_type.prediction} />
                </div>
                <div className="card">
                  <h2 className="font-semibold text-slate-900">Organism class</h2>
                  <p className="mb-3 text-xs text-slate-500">Model held-out accuracy {res.organism_class.model_test_accuracy} (chance {res.organism_class.chance_accuracy})</p>
                  <div className="mb-3 text-2xl font-semibold text-slate-700">{res.organism_class.prediction}</div>
                  <Probs probs={res.organism_class.probabilities} best={res.organism_class.prediction} />
                  <p className="mt-3 rounded bg-amber-50 p-2 text-xs text-amber-800">{res.organism_class.note}</p>
                </div>
              </div>
              {res.repeat_scan.length > 0 && (
                <div className="card overflow-x-auto">
                  <h2 className="mb-2 font-semibold text-slate-900">Tandem repeats (exact scan)</h2>
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs uppercase text-slate-500"><tr><th className="py-1">Motif</th><th>Period</th><th>Position</th><th>Copies</th></tr></thead>
                    <tbody className="divide-y divide-slate-100">
                      {res.repeat_scan.map((r, i) => <tr key={i}><td className="py-1 font-mono">{r.motif}</td><td>{r.period}</td><td>{r.start}-{r.end}</td><td>{r.copies}</td></tr>)}
                    </tbody>
                  </table>
                </div>
              )}
              <ReportCard report={res.report} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
