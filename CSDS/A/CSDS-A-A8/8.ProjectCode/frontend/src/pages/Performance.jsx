import { useEffect, useState } from 'react'
import api, { errorText } from '../api.js'
import { BarChart, ErrorBox, PageTitle, Spinner, Stat } from '../components/Ui.jsx'
import { METHODS } from './LabelEfficiency.jsx'

const DNA_METHODS = [
  { key: 'jepa', label: 'k-mer JEPA pre-training (BioSight)' },
  { key: 'mlm', label: 'Masked-token reconstruction pre-training' },
  { key: 'scratch', label: 'From scratch' },
]

function Table({ head, rows }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500"><tr>{head.map((h) => <th key={h} className="py-2 pr-3">{h}</th>)}</tr></thead>
        <tbody className="divide-y divide-slate-100">{rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j} className="py-2 pr-3">{c ?? '-'}</td>)}</tr>)}</tbody>
      </table>
    </div>
  )
}

export default function Performance() {
  const [m, setM] = useState(null)
  const [hist, setHist] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.get('/metrics/all'), api.get('/history')])
      .then(([a, h]) => { setM(a.data); setHist(h.data) })
      .catch((e) => setError(errorText(e)))
  }, [])

  if (error) return <ErrorBox error={error} />
  if (!m) return <Spinner text="Loading metrics..." />
  const mri = m.mri || {}
  const dna = m.dna || {}
  const ev = m.eval || {}
  const rep = dna.repeat || {}
  const cm = rep.jepa_100?.confusion

  return (
    <div className="space-y-5">
      <PageTitle title="Model performance" subtitle="Held-out evaluation of every model in BioSight against supervised and reconstruction-based baselines." />

      <div className="card">
        <h2 className="mb-3 font-semibold text-slate-900">Brain-MRI segmentation (test slices from unseen patients)</h2>
        <Table head={['Method', 'Masks', 'Dice', 'IoU', 'Mean Dice (tumour slices)']}
          rows={[10, 100].flatMap((p) => METHODS.filter((x) => mri.finetune?.[`${x.key}_${p}`]).map((x) => {
            const r = mri.finetune[`${x.key}_${p}`]
            return [x.label, `${p}%`, r.dice, r.iou, r.mean_dice_tumour_slices]
          }))} />
        {mri.pretrain && (
          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            {Object.entries(mri.pretrain).map(([k, v]) => (
              <Stat key={k} label={`${k.toUpperCase()} pre-training`} value={`${v.epochs} epochs`} hint={`final loss ${v.history.at(-1).loss.toFixed(4)} · ${Math.round(v.seconds / 60)} min`} />
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="mb-1 font-semibold text-slate-900">DNA encoder - STR repeat-type classification</h2>
        <p className="mb-3 text-xs text-slate-500">5 classes (none, di-, tri-, tetra-, penta-nucleotide repeats); {dna.pretrain_sequences} unlabelled sequences for pre-training.</p>
        <BarChart format={(v) => v.toFixed(3)} legend={DNA_METHODS.map((x) => x.label)}
          groups={[10, 100].map((p) => ({ label: `${p}% of labels`, bars: DNA_METHODS.map((x) => ({ name: x.label, value: rep[`${x.key}_${p}`]?.accuracy ?? null })) }))} />
        <div className="mt-4">
          <Table head={['Method', 'Labels', 'Accuracy', 'Macro F1', 'Labelled sequences']}
            rows={[10, 100].flatMap((p) => DNA_METHODS.filter((x) => rep[`${x.key}_${p}`]).map((x) => {
              const r = rep[`${x.key}_${p}`]
              return [x.label, `${p}%`, r.accuracy, r.macro_f1, r.labelled_sequences]
            })).concat(rep.jepa_probe_100 ? [['JEPA encoder frozen (linear probe)', '100%', rep.jepa_probe_100.accuracy, rep.jepa_probe_100.macro_f1, rep.jepa_probe_100.labelled_sequences]] : [])} />
        </div>
        {cm && (
          <div className="mt-4 overflow-x-auto">
            <div className="label">Confusion matrix - JEPA, 100% labels (rows = true)</div>
            <table className="text-xs">
              <thead><tr><th />{rep.jepa_100.labels.map((l) => <th key={l} className="px-2 py-1 font-medium text-slate-500">{l.slice(0, 5)}</th>)}</tr></thead>
              <tbody>{cm.map((row, i) => (
                <tr key={i}><td className="pr-2 font-medium text-slate-600">{rep.jepa_100.labels[i]}</td>
                  {row.map((v, j) => <td key={j} className={`px-2 py-1 text-center ${i === j ? 'bg-teal-100 font-semibold' : ''}`}>{v}</td>)}</tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="mb-1 font-semibold text-slate-900">DNA encoder - organism class (Kaggle dataset)</h2>
        <p className="mb-3 text-xs text-slate-500">All methods score close to chance on held-out data: the class labels in this dataset are not predictable from the sequence.</p>
        <Table head={['Method', 'Accuracy', 'Macro F1', 'Chance']}
          rows={DNA_METHODS.filter((x) => dna.organism?.[`${x.key}_100`]).map((x) => {
            const r = dna.organism[`${x.key}_100`]
            return [x.label, r.accuracy, r.macro_f1, r.chance_accuracy]
          })} />
      </div>

      {ev.str && (
        <div className="card">
          <h2 className="mb-3 font-semibold text-slate-900">STR matching (simulated casework queries)</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Rank-1 identification" value={`${(ev.str.rank1_accuracy * 100).toFixed(1)}%`} hint={`${ev.str.true_source_queries} queries with drop-out + errors`} />
            <Stat label="Median log10 LR (true source)" value={ev.str.median_log10_lr_true_source} />
            <Stat label="Non-contributors with LR > 1" value={`${(ev.str.non_contributor_lr_gt1_rate * 100).toFixed(2)}%`} hint={`${ev.str.non_contributor_queries} queries x database`} />
            <Stat label="Max log10 LR non-contributor" value={ev.str.max_log10_lr_non_contributor} />
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="mb-3 font-semibold text-slate-900">Your recent analyses</h2>
        {hist.length === 0 ? <p className="text-sm text-slate-500">No analyses yet.</p> : (
          <Table head={['When', 'Type', 'Title']} rows={hist.slice(0, 15).map((h) => [new Date(h.created_at).toLocaleString(), h.kind.toUpperCase(), h.title])} />
        )}
      </div>
    </div>
  )
}
