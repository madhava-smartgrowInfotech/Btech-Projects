import { useEffect, useMemo, useState } from 'react'
import { ImagePlus, Play } from 'lucide-react'
import api, { errorText } from '../api.js'
import { ErrorBox, PageTitle, ReportCard, Spinner, Stat } from '../components/Ui.jsx'

export default function Mri() {
  const [models, setModels] = useState([])
  const [samples, setSamples] = useState([])
  const [model, setModel] = useState('jepa_10')
  const [spacing, setSpacing] = useState(1.0)
  const [file, setFile] = useState(null)
  const [sample, setSample] = useState(null)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    Promise.all([api.get('/mri/models'), api.get('/mri/samples')])
      .then(([m, s]) => { setModels(m.data); setSamples(s.data) })
      .catch((e) => setError(errorText(e)))
  }, [])

  const preview = useMemo(() => (file ? URL.createObjectURL(file) : sample ? `/api/mri/samples/${sample}` : null), [file, sample])
  const pageItems = samples.slice(page * 12, page * 12 + 12)

  const run = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      let data
      if (file) {
        const fd = new FormData()
        fd.append('file', file)
        fd.append('model', model)
        fd.append('pixel_spacing_mm', spacing)
        data = (await api.post('/mri/segment', fd)).data
      } else {
        data = (await api.post('/mri/segment-sample', { name: sample, model, pixel_spacing_mm: Number(spacing) })).data
      }
      setResult(data)
    } catch (e) {
      setError(errorText(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageTitle title="MRI analysis" subtitle="Upload a brain-MRI slice (FLAIR / 3-channel PNG, JPG or TIF) or pick a sample slice to get the tumour mask, its area and a structured report." />
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="card space-y-4 lg:col-span-1">
          <div>
            <label className="label">Segmentation model</label>
            <select className="input" value={model} onChange={(e) => setModel(e.target.value)}>
              {models.map((m) => <option key={m.key} value={m.key} disabled={!m.available}>{m.label}{m.available ? '' : ' (not trained)'}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Pixel spacing (mm per pixel)</label>
            <input className="input" type="number" step="0.01" min="0.05" max="5" value={spacing} onChange={(e) => setSpacing(e.target.value)} />
          </div>
          <div>
            <label className="label">Upload a slice</label>
            <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-300 p-4 text-sm text-slate-500 hover:border-teal-400">
              <ImagePlus size={18} /> {file ? file.name : 'Choose image'}
              <input type="file" accept=".png,.jpg,.jpeg,.tif,.tiff" className="hidden"
                onChange={(e) => { setFile(e.target.files[0] || null); setSample(null); setResult(null) }} />
            </label>
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between">
              <span className="label mb-0">Or pick a sample slice ({samples.length})</span>
              <div className="flex gap-1 text-xs">
                <button className="rounded px-2 py-0.5 hover:bg-slate-100 disabled:opacity-40" disabled={page === 0} onClick={() => setPage(page - 1)}>Prev</button>
                <button className="rounded px-2 py-0.5 hover:bg-slate-100 disabled:opacity-40" disabled={(page + 1) * 12 >= samples.length} onClick={() => setPage(page + 1)}>Next</button>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {pageItems.map((s) => (
                <button key={s.file} onClick={() => { setSample(s.file); setFile(null); setResult(null) }}
                  className={`relative overflow-hidden rounded border-2 ${sample === s.file ? 'border-teal-500' : 'border-transparent'}`}
                  title={`${s.file} - ${s.tumour_pixels ? 'tumour in ground truth' : 'no tumour in ground truth'}`}>
                  <img src={`/api/mri/samples/${s.file}`} alt={s.file} className="aspect-square w-full object-cover" loading="lazy" />
                  {s.tumour_pixels > 0 && <span className="absolute right-0.5 top-0.5 h-2 w-2 rounded-full bg-red-500" />}
                </button>
              ))}
            </div>
            <p className="mt-1 text-xs text-slate-400">Sample data: held-out LGG slices; red dot = tumour in the expert mask.</p>
          </div>
          <button className="btn w-full" onClick={run} disabled={loading || (!file && !sample)}>
            {loading ? <Spinner text="Segmenting and writing report..." /> : <><Play size={16} /> Analyse slice</>}
          </button>
          <ErrorBox error={error} />
        </div>

        <div className="space-y-5 lg:col-span-2">
          <div className="card">
            <div className="grid gap-4 sm:grid-cols-2">
              <Figure title="Input slice" src={preview} />
              <Figure title="Tumour mask overlay" src={result?.overlay_png} placeholder={loading ? 'Running model...' : 'Run the analysis to see the mask'} />
            </div>
            {result && (
              <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
                <Stat label="Tumour detected" value={result.tumour_detected ? 'Yes' : 'No'} />
                <Stat label="Area" value={`${result.area_mm2} mm²`} hint={`${result.area_pixels} px`} />
                <Stat label="Share of brain" value={`${result.percent_of_brain}%`} />
                <Stat label="Mean confidence" value={result.mean_confidence} hint={result.location} />
                {result.max_extent_mm && <Stat label="Max extent" value={`${result.max_extent_mm} mm`} />}
                {result.ground_truth && <Stat label="Dice vs expert mask" value={result.ground_truth.dice} hint={`IoU ${result.ground_truth.iou}`} />}
                <Stat label="Model test Dice" value={result.model_test_dice} hint={result.model_label} />
              </div>
            )}
          </div>
          {result && <ReportCard report={result.report} />}
        </div>
      </div>
    </div>
  )
}

function Figure({ title, src, placeholder = 'No image selected' }) {
  return (
    <div>
      <div className="label">{title}</div>
      <div className="flex aspect-square items-center justify-center overflow-hidden rounded-lg bg-slate-900">
        {src ? <img src={src} alt={title} className="h-full w-full object-contain" /> : <span className="px-4 text-center text-sm text-slate-400">{placeholder}</span>}
      </div>
    </div>
  )
}
