import { Download, FileJson, ShieldCheck, Swords } from 'lucide-react'
import { useEffect, useState } from 'react'
import api, { describeError, download, sourceForm } from '../api'
import KeyField, { keyReady } from '../components/product/KeyField'
import ReportView from '../components/product/ReportView'
import SourcePicker from '../components/product/SourcePicker'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Badge, Card } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { num, pct, when } from '../format'

export default function Lab() {
  const toast = useToast()

  // the image and key for the next analysis
  const [src, setSrc] = useState({})
  const [key, setKey] = useState('')
  const [jobs, setJobs] = useState(null)

  // the report on screen. `run` remembers the image and key it was made with (needed for attack tests).
  const [report, setReport] = useState(null)
  const [run, setRun] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [attackBusy, setAttackBusy] = useState(false)
  const [attackError, setAttackError] = useState(null)

  // saved reports
  const [saved, setSaved] = useState(null)
  const [savedError, setSavedError] = useState(null)
  const [openingId, setOpeningId] = useState(null)

  const ready = !!(src.file || src.kind || src.jobId) && keyReady(key)

  function loadSaved() {
    return api.get('/lab/reports')
      .then((r) => { setSaved(r.data); setSavedError(null) })
      .catch((e) => setSavedError(describeError(e, 'Could not load saved reports')))
  }
  useEffect(() => {
    loadSaved()
    api.get('/studio/jobs').then((r) => setJobs(r.data)).catch(() => setJobs([]))
  }, [])

  async function analyze(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setAttackError(null)
    try {
      const r = await api.post('/lab/analyze', sourceForm(src, key))
      setReport(r.data)
      setRun({ src, key })
      toast({ tone: 'ok', title: 'Analysis saved', body: `report #${r.data.id}` })
      loadSaved()
    } catch (err) {
      setError(describeError(err, 'Analysis failed'))
    } finally {
      setBusy(false)
    }
  }

  async function attacks() {
    const fd = sourceForm(run.src, run.key)
    fd.append('report_id', report.id)
    setAttackBusy(true)
    setAttackError(null)
    try {
      const r = await api.post('/attacks/run', fd)
      setReport((rep) => ({ ...rep, attacks: r.data.results }))
      toast({ tone: 'ok', title: 'Attack tests finished', body: `${r.data.results.length} cases attached to report #${report.id}` })
      loadSaved()
    } catch (err) {
      setAttackError(describeError(err, 'Attack tests failed'))
    } finally {
      setAttackBusy(false)
    }
  }

  async function open(id) {
    setOpeningId(id)
    try {
      const r = await api.get(`/lab/reports/${id}`)
      setReport(r.data)
      setRun(null)
      setAttackError(null)
    } catch (err) {
      toast({ tone: 'alert', title: 'Could not open report', body: describeError(err).message })
    } finally {
      setOpeningId(null)
    }
  }

  async function exportReport(id, fmt) {
    try {
      await download(`/lab/reports/${id}/export?fmt=${fmt}`, `skycipher_report_${id}.${fmt}`)
      toast({ tone: 'ok', title: `Report exported as ${fmt.toUpperCase()}`, body: `report #${id}` })
    } catch (err) {
      toast({ tone: 'alert', title: 'Export failed', body: describeError(err).message })
    }
  }

  return (
    <>
      <PageHeader eyebrow="analysis · attacks"
        title="Security lab"
        subtitle="Statistical tests on the cipher image, a one-pixel differential test, key sensitivity and channel-damage tests. Every run is saved as a report you can export." />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
        <div className="space-y-5">
          <Card title="1 · Image">
            <SourcePicker value={src} onChange={setSrc} jobs={jobs || []} id="lab-source" />
          </Card>
          <Card title="2 · Key">
            <KeyField id="lab-key" value={key} onChange={setKey} />
            <p className="mt-2 text-xs text-muted">The key is needed for the attack tests, so the analysis always uses one you can see.</p>
          </Card>
          <form onSubmit={analyze} className="space-y-3">
            <Button type="submit" size="lg" icon={ShieldCheck} loading={busy} disabled={!ready} className="w-full">Run security analysis</Button>
            {!ready && <p className="text-center font-mono text-[11px] text-dim">choose an image and a key to enable the analysis</p>}
            {error && <ErrorState error={error} />}
          </form>
        </div>

        <div className="min-w-0 space-y-5">
          {busy && (
            <Card title="Analysing">
              <div className="space-y-3"><Skeleton className="h-20 w-full" /><Skeleton className="h-64 w-full" /><Skeleton className="h-40 w-full" /></div>
            </Card>
          )}

          {!busy && !report && (
            <Card>
              <EmptyState icon={ShieldCheck} title="No report on screen"
                body="Choose an image and a key, then run the analysis. Or open a saved report below." />
            </Card>
          )}

          {report && !busy && (
            <>
              <Card title="Actions" eyebrow={`report #${report.id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <Button icon={Swords} loading={attackBusy} disabled={!run || attackBusy} onClick={attacks}>
                    {report.attacks ? 'Run attack tests again' : 'Run attack tests'}
                  </Button>
                  <Button variant="secondary" icon={Download} onClick={() => exportReport(report.id, 'html')}>Export HTML</Button>
                  <Button variant="secondary" icon={FileJson} onClick={() => exportReport(report.id, 'json')}>Export JSON</Button>
                  {!run && <Badge>opened report: run an analysis to attack with a key</Badge>}
                </div>
                <p className="mt-3 text-xs text-muted">
                  Attack tests add salt-and-pepper noise, Gaussian noise and cropping to the cipher image, decrypt it and measure what survives.
                </p>
                {attackError && <div className="mt-3"><ErrorState error={attackError} compact /></div>}
              </Card>
              <ReportView report={report} />
            </>
          )}

          <Card title="Saved reports" bodyClass="p-0">
            <div className="px-4 pb-4 pt-3">
              {savedError && <ErrorState error={savedError} compact onRetry={loadSaved} />}
              <Table
                loading={!saved && !savedError}
                rowKey={(r) => r.id}
                rows={saved}
                empty={<EmptyState title="No saved reports" body="Run an analysis: it is saved here automatically." />}
                columns={[
                  { key: 'id', label: '#', render: (r) => <span className="font-mono">{r.id}</span> },
                  { key: 'image', label: 'Image', className: 'max-w-[160px] truncate', render: (r) => r.image_name },
                  { key: 'created', label: 'Created', render: (r) => when(r.created_at) },
                  { key: 'entropy', label: 'Entropy', align: 'right', render: (r) => num(r.entropy, 4) },
                  { key: 'npcr', label: 'NPCR', align: 'right', render: (r) => pct(r.npcr) },
                  { key: 'attacks', label: 'Attacks', render: (r) => (r.has_attacks ? <Badge tone="ok">yes</Badge> : <Badge>no</Badge>) },
                  { key: 'actions', label: '', align: 'right', render: (r) => (
                    <span className="inline-flex flex-wrap justify-end gap-1.5">
                      <Button size="sm" variant="ghost" loading={openingId === r.id} onClick={() => open(r.id)}>Open</Button>
                      <Button size="sm" variant="ghost" icon={Download} onClick={() => exportReport(r.id, 'html')}>HTML</Button>
                      <Button size="sm" variant="ghost" icon={FileJson} onClick={() => exportReport(r.id, 'json')}>JSON</Button>
                    </span>
                  ) },
                ]}
              />
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
