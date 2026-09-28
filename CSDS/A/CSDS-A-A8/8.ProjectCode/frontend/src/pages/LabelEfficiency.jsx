import { useEffect, useState } from 'react'
import api, { errorText } from '../api.js'
import { BarChart, ErrorBox, PageTitle, Spinner, Stat } from '../components/Ui.jsx'

export const METHODS = [
  { key: 'jepa', label: 'ViT + JEPA pre-training (BioSight)' },
  { key: 'unet', label: 'U-Net, supervised' },
  { key: 'mae', label: 'ViT + MAE reconstruction pre-training' },
  { key: 'scratch', label: 'ViT from scratch' },
]

export default function LabelEfficiency() {
  const [data, setData] = useState(null)
  const [metric, setMetric] = useState('dice')
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/metrics/label-efficiency').then((r) => setData(r.data)).catch((e) => setError(errorText(e)))
  }, [])

  if (error) return <ErrorBox error={error} />
  if (!data) return <Spinner text="Loading results..." />
  const ft = data.finetune
  const methods = METHODS.filter((m) => ft[`${m.key}_10`] || ft[`${m.key}_100`])
  const groups = [10, 100].map((p) => ({
    label: `${p}% of masks`,
    bars: methods.map((m) => ({ name: m.label, value: ft[`${m.key}_${p}`]?.[metric] ?? null })),
  }))
  const j10 = ft.jepa_10?.dice
  const u100 = ft.unet_100?.dice
  const u10 = ft.unet_10?.dice

  return (
    <div className="space-y-5">
      <PageTitle title="Label efficiency" subtitle={`Brain-MRI tumour segmentation on ${data.data?.test_slices} held-out slices from unseen patients. Models are trained with 10% or 100% of the ${data.data?.train_slices} training masks.`} />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="JEPA @ 10% masks" value={j10} hint="test Dice" />
        <Stat label="U-Net @ 100% masks" value={u100} hint="fully supervised" />
        <Stat label="JEPA 10% vs U-Net 100%" value={j10 && u100 ? `${Math.round((100 * j10) / u100)}%` : '-'} hint="of the supervised Dice" />
        <Stat label="Gain over U-Net @ 10%" value={j10 && u10 ? `${j10 - u10 >= 0 ? '+' : ''}${(j10 - u10).toFixed(3)}` : '-'} hint="Dice points" />
      </div>
      <div className="card">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Test {metric === 'dice' ? 'Dice' : 'IoU'} by label budget</h2>
          <div className="flex rounded-lg border border-slate-200 p-0.5 text-sm">
            {['dice', 'iou'].map((m) => (
              <button key={m} onClick={() => setMetric(m)} className={`rounded-md px-3 py-1 ${metric === m ? 'bg-teal-600 text-white' : 'text-slate-600'}`}>{m === 'dice' ? 'Dice' : 'IoU'}</button>
            ))}
          </div>
        </div>
        <BarChart groups={groups} legend={methods.map((m) => m.label)} />
      </div>
      <div className="card overflow-x-auto">
        <h2 className="mb-3 font-semibold text-slate-900">All runs</h2>
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr><th className="py-2">Method</th><th>Masks</th><th>Labelled slices</th><th>Dice</th><th>IoU</th><th>Mean Dice (tumour slices)</th><th>Train time</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {[10, 100].flatMap((p) => methods.map((m) => {
              const r = ft[`${m.key}_${p}`]
              if (!r) return null
              return (
                <tr key={`${m.key}_${p}`} className={m.key === 'jepa' ? 'font-medium' : ''}>
                  <td className="py-2">{m.label}</td><td>{p}%</td><td>{r.labelled_slices}</td><td>{r.dice}</td><td>{r.iou}</td>
                  <td>{r.mean_dice_tumour_slices}</td><td>{Math.round(r.seconds / 60)} min</td>
                </tr>
              )
            }))}
          </tbody>
        </table>
        <p className="mt-3 text-xs text-slate-500">Dice / IoU are pooled over all test pixels (threshold 0.5). Pre-training (JEPA and MAE) used the training slices only, without any masks.</p>
      </div>
      <div className="card">
        <h2 className="mb-3 font-semibold text-slate-900">Self-supervised pre-training loss</h2>
        <img src="/api/metrics/plot/mri_pretrain_loss.png" alt="Pre-training loss" className="max-w-xl" onError={(e) => { e.currentTarget.style.display = 'none' }} />
      </div>
    </div>
  )
}
