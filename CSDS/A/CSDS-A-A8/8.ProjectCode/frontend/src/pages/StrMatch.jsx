import { useEffect, useState } from 'react'
import { Search, Shuffle } from 'lucide-react'
import api, { errorText } from '../api.js'
import { ErrorBox, PageTitle, ReportCard, Spinner, Stat } from '../components/Ui.jsx'

export default function StrMatch() {
  const [meta, setMeta] = useState(null)
  const [profile, setProfile] = useState({})
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [res, setRes] = useState(null)
  const [open, setOpen] = useState(null)

  useEffect(() => {
    api.get('/str/loci').then((r) => setMeta(r.data)).catch((e) => setError(errorText(e)))
  }, [])

  const loadSample = async () => {
    setError('')
    try {
      const { data } = await api.get('/str/sample-query')
      setProfile(data.profile)
      setNote(data.note)
      setRes(null)
    } catch (e) {
      setError(errorText(e))
    }
  }

  const run = async () => {
    setLoading(true)
    setError('')
    setRes(null)
    try {
      setRes((await api.post('/str/match', { profile })).data)
      setOpen(0)
    } catch (e) {
      setError(errorText(e))
    } finally {
      setLoading(false)
    }
  }

  if (!meta) return error ? <ErrorBox error={error} /> : <Spinner text="Loading loci..." />

  return (
    <div>
      <PageTitle title="STR profile matching" subtitle={`Rank a query profile against ${meta.database_size} synthetic reference profiles (sample data) with likelihood ratios. Allele frequencies: ${meta.frequency_source}.`} />
      <div className="grid gap-5 lg:grid-cols-5">
        <div className="card space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <span className="label mb-0">Query genotype (alleles separated by a slash)</span>
            <button className="btn-outline px-2.5 py-1 text-xs" onClick={loadSample}><Shuffle size={14} /> Sample query</button>
          </div>
          {note && <p className="rounded bg-slate-50 p-2 text-xs text-slate-600">{note}</p>}
          <div className="grid grid-cols-2 gap-2">
            {meta.loci.map((l) => (
              <div key={l}>
                <label className="text-xs font-medium text-slate-600">{l}</label>
                <input className="input py-1.5" placeholder="e.g. 12/14" value={profile[l] || ''} onChange={(e) => setProfile({ ...profile, [l]: e.target.value })} />
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button className="btn flex-1" onClick={run} disabled={loading}>{loading ? <Spinner text="Searching and writing report..." /> : <><Search size={16} /> Search database</>}</button>
            <button className="btn-outline" onClick={() => { setProfile({}); setNote(''); setRes(null) }}>Clear</button>
          </div>
          <ErrorBox error={error} />
        </div>
        <div className="space-y-5 lg:col-span-3">
          {!res && !loading && <div className="card text-sm text-slate-500">Enter at least 3 loci or load a sample query, then search.</div>}
          {res && (
            <>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Stat label="Loci in query" value={res.query_loci} />
                <Stat label="Random match prob." value={res.random_match_probability.toExponential(2)} hint={`theta = ${res.theta}`} />
                <Stat label="Top log10 LR" value={res.matches[0].log10_lr} hint={res.matches[0].id} />
                <Stat label="Refs with LR > 1" value={res.candidates_with_positive_support} hint={`of ${res.database_size}`} />
              </div>
              <div className="card overflow-x-auto">
                <h2 className="mb-2 font-semibold text-slate-900">Ranked candidates</h2>
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">#</th><th>Reference</th><th>LR</th><th>log10 LR</th><th>Loci matched</th><th>Verbal scale</th></tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {res.matches.map((m, i) => (
                      <tr key={m.id} className={`cursor-pointer hover:bg-slate-50 ${open === i ? 'bg-teal-50' : ''}`} onClick={() => setOpen(open === i ? null : i)}>
                        <td className="py-2">{i + 1}</td><td className="font-medium">{m.id}</td><td>{m.lr_display}</td><td>{m.log10_lr}</td>
                        <td>{m.loci_matched}/{m.loci_compared}</td><td className="text-xs">{m.verbal}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {open !== null && (
                  <div className="mt-4">
                    <div className="label">Per-locus comparison - {res.matches[open].id}</div>
                    <div className="grid gap-1.5 sm:grid-cols-2">
                      {res.matches[open].loci.map((l) => (
                        <div key={l.locus} className={`flex justify-between rounded px-2 py-1 text-xs ${l.shared_alleles === 2 ? 'bg-emerald-50' : 'bg-rose-50'}`}>
                          <span className="font-medium">{l.locus}</span><span>{l.query} vs {l.reference}</span><span>LR {l.lr}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <ReportCard report={res.report} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
