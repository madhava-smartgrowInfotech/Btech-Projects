import { useEffect, useState } from 'react'
import api, { describeError } from '../../api'
import { FileDrop, Select } from '../ui/controls'
import { EmptyState, ErrorState, Skeleton } from '../ui/feedback'
import { Tabs, TabPanel } from '../ui/nav'

// Sample images are public on the API, so <img> can load them directly.
const sampleUrl = (s) => `/api/samples/file/${s.kind}/${encodeURIComponent(s.name)}`
const KIND_LABEL = { visdrone: 'VisDrone drone images', sipi: 'USC-SIPI test images' }

// Loaded once per page visit; the list is small and does not change while the app runs.
let samplesPromise = null
function loadSamples() {
  if (!samplesPromise) {
    samplesPromise = api.get('/samples').then((r) => r.data).catch((e) => {
      samplesPromise = null
      throw e
    })
  }
  return samplesPromise
}

/**
 * Chooses the input image. `value` is one of:
 *   { kind, name }  a bundled sample
 *   { file }        an uploaded file
 *   { jobId }       a saved studio job (only when `jobs` is given)
 * `jobs` = [{ id, name, width, height }]
 */
export default function SourcePicker({ value, onChange, jobs, id = 'source' }) {
  const [tab, setTab] = useState(value?.file ? 'upload' : value?.jobId ? 'job' : 'sample')
  const [samples, setSamples] = useState(null)
  const [error, setError] = useState(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let live = true
    setError(null)
    loadSamples()
      .then((s) => live && setSamples(s))
      .catch((e) => live && setError(describeError(e, 'Could not load sample images')))
    return () => { live = false }
  }, [retry])

  const tabs = [
    { id: 'sample', label: 'Sample' },
    { id: 'upload', label: 'Upload' },
    ...(jobs ? [{ id: 'job', label: 'Saved job', count: jobs.length }] : []),
  ]

  const picked = value?.file ? `upload · ${value.file.name}`
    : value?.jobId ? `saved job #${value.jobId}`
      : value?.name ? `sample · ${value.name}` : 'nothing selected'

  return (
    <div className="space-y-3">
      <Tabs id={id} tabs={tabs} value={tab} onChange={setTab} label="Image source" />

      <TabPanel tabsId={id} value="sample">
        {tab === 'sample' && (
          error ? <ErrorState error={error} compact onRetry={() => setRetry((n) => n + 1)} />
            : !samples ? <div className="grid grid-cols-4 gap-2"><Skeleton className="aspect-square" /><Skeleton className="aspect-square" /><Skeleton className="aspect-square" /><Skeleton className="aspect-square" /></div>
              : (
                <div className="max-h-80 space-y-4 overflow-y-auto pr-1">
                  {Object.keys(KIND_LABEL).map((kind) => {
                    const items = samples.filter((s) => s.kind === kind)
                    if (!items.length) return null
                    return (
                      <div key={kind}>
                        <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.14em] text-dim">{KIND_LABEL[kind]} · {items.length}</div>
                        <ul className="grid grid-cols-4 gap-2 sm:grid-cols-5">
                          {items.map((s) => {
                            const on = value?.kind === s.kind && value?.name === s.name
                            return (
                              <li key={`${s.kind}/${s.name}`}>
                                <button type="button" aria-pressed={on} aria-label={`Use ${s.name}`} onClick={() => onChange({ kind: s.kind, name: s.name })}
                                  className={`aspect-square w-full overflow-hidden rounded-[4px] border bg-panel-2 transition-colors ${on ? 'border-ok ring-2 ring-ok/40' : 'border-line hover:border-ok/50'}`}>
                                  <img src={sampleUrl(s)} alt="" loading="lazy" className="h-full w-full object-cover" />
                                </button>
                              </li>
                            )
                          })}
                        </ul>
                      </div>
                    )
                  })}
                  {samples.length === 0 && <EmptyState title="No sample images" body="Run scripts/download_data.py, or upload your own image." />}
                </div>
              )
        )}
      </TabPanel>

      <TabPanel tabsId={id} value="upload">
        {tab === 'upload' && (
          <FileDrop label="Drop a PNG, JPEG, TIFF or BMP here" accept="image/*" multiple={false}
            onFiles={(files) => onChange(files[0] ? { file: files[0] } : {})} />
        )}
      </TabPanel>

      {jobs && (
        <TabPanel tabsId={id} value="job">
          {tab === 'job' && (
            jobs.length === 0
              ? <EmptyState title="No saved jobs yet" body="Encrypt an image in the studio first. It is then saved here." />
              : (
                <Select label="Encrypted image" value={value?.jobId ?? ''}
                  onChange={(e) => onChange({ jobId: Number(e.target.value) })}
                  options={[['', 'choose a job…'], ...jobs.map((j) => [String(j.id), `#${j.id} · ${j.name} · ${j.width}×${j.height}`])]} />
              )
          )}
        </TabPanel>
      )}

      <p className="font-mono text-[11px] text-dim" aria-live="polite">selected: {picked}</p>
    </div>
  )
}
