import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Check, Download, PencilLine } from 'lucide-react'
import {
  Alert, Badge, Breadcrumbs, Button, Card, EmptyState, ErrorState, KeyValueList, Modal, PageHeader, Select, SkeletonBlock, Textarea, Timeline, useToast,
} from '../components/ui'
import { PriorityBlock, ShapBars, FindingChips, LabChips } from '../components/athena/bits'
import { api } from '../lib/api'
import { fmtDateTime, fmtPct, PRIORITY_NAME } from '../lib/format'
import { UserX } from 'lucide-react'

const VITAL_ROWS = [
  ['age', 'Age', ''], ['heart_rate', 'Heart rate', ' bpm'], ['sbp', 'Systolic BP', ' mmHg'], ['dbp', 'Diastolic BP', ' mmHg'],
  ['spo2', 'SpO2', ' %'], ['temp_c', 'Temperature', ' °C'], ['resp_rate', 'Respiratory rate', ' /min'], ['arrival_mode', 'Arrival mode', ''],
]

export default function PatientResult() {
  const { id } = useParams()
  const toast = useToast()
  const [state, setState] = useState({ loading: true, data: null, error: null })
  const [open, setOpen] = useState(false)
  const [newP, setNewP] = useState('1')
  const [reason, setReason] = useState('')
  const [formErr, setFormErr] = useState('')
  const [saving, setSaving] = useState(false)
  const [pdfBusy, setPdfBusy] = useState(false)

  const load = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }))
    api
      .patient(id)
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => setState({ loading: false, data: null, error }))
  }, [id])
  useEffect(load, [load])

  const p = state.data

  const openModal = () => {
    setNewP(String(p.priority))
    setReason('')
    setFormErr('')
    setOpen(true)
  }

  const save = async (e) => {
    e?.preventDefault()
    const pr = Number(newP)
    if (pr !== p.priority && !reason.trim()) {
      setFormErr('Give a reason when you change the priority.')
      return
    }
    setSaving(true)
    setFormErr('')
    try {
      const updated = await api.override(p.id, pr, reason)
      setState({ loading: false, data: updated, error: null })
      setOpen(false)
      toast.success(pr === p.priority ? 'Priority accepted and logged.' : `Priority changed to ${pr}. The queue has been reordered.`)
    } catch (err) {
      setFormErr(err.message)
    } finally {
      setSaving(false)
    }
  }

  const pdf = async () => {
    setPdfBusy(true)
    try {
      await api.downloadSummary(p.id)
      toast.success('Triage summary downloaded.')
    } catch (err) {
      toast.error(`Could not build the summary: ${err.message}`)
    } finally {
      setPdfBusy(false)
    }
  }

  const crumbs = <Breadcrumbs items={[{ label: 'Triage queue', to: '/app/queue' }, { label: p ? p.name : `Patient ${id}` }]} />

  if (state.loading && !p)
    return (
      <>
        <PageHeader title="Loading result" crumbs={crumbs} />
        <SkeletonBlock rows={6} label="Loading the triage result" />
      </>
    )
  if (state.error)
    return state.error.status === 404 ? (
      <EmptyState icon={UserX} title="Patient not found" action={<Button variant="primary" to="/app/queue" icon={ArrowLeft}>Back to the queue</Button>}>
        This record does not exist or was removed.
      </EmptyState>
    ) : (
      <ErrorState title="Could not load this patient" error={state.error} onRetry={load} />
    )

  const rep = p.report || {}
  const changed = p.priority !== p.model_priority
  const probs = Object.entries(p.probabilities)

  return (
    <>
      <PageHeader
        crumbs={crumbs}
        eyebrow={`Recorded ${fmtDateTime(p.created_at)}${p.source === 'sample' ? ' · sample case' : ''}`}
        title={p.name}
        actions={
          <>
            <Button icon={Download} loading={pdfBusy} onClick={pdf}>Summary PDF</Button>
            <Button variant="primary" icon={PencilLine} onClick={openModal}>Accept or change</Button>
          </>
        }
      />

      <div className="stack" style={{ '--gap': '24px' }}>
        <Card tone={p.priority <= 2 ? 'coral' : undefined} className="result-hero">
          <PriorityBlock p={p.priority} size="lg" />
          <div className="stack" style={{ '--gap': '10px', minWidth: 0 }}>
            <div className="row">
              <h2 className="display-md">{PRIORITY_NAME[p.priority]}</h2>
              <Badge tone={p.risk_level === 'High' ? 'blocked' : p.risk_level === 'Moderate' ? 'upcoming' : 'pass'}>{p.risk_level} risk</Badge>
              {p.reviewed && <Badge tone="info"><Check size={12} strokeWidth={3} aria-hidden="true" /> Reviewed</Badge>}
            </div>
            <div>
              <div className="row-between small mono" style={{ marginBottom: 6 }}>
                <span>Model suggestion: priority {p.model_priority}</span>
                <strong>{fmtPct(p.confidence)} calibrated confidence</strong>
              </div>
              <div className="conf-bar" role="meter" aria-valuenow={Math.round(p.confidence * 100)} aria-valuemin={0} aria-valuemax={100} aria-label="Calibrated confidence">
                <i style={{ width: `${p.confidence * 100}%` }} />
              </div>
            </div>
            {changed && <Alert tone="warning">A clinician changed this from the model's priority {p.model_priority} to {p.priority}.</Alert>}
            <p className="small">
              Top drivers: <strong>{p.headline.join(', ') || '—'}</strong>
            </p>
          </div>
        </Card>

        <div className="fused-grid">
          <Card title="Fused patient record · from the report">
            <div className="stack">
              <div><h3 className="display-sm" style={{ marginBottom: 8 }}>Symptoms</h3><FindingChips items={rep.symptoms} /></div>
              <div><h3 className="display-sm" style={{ marginBottom: 8 }}>Findings</h3><FindingChips items={rep.findings} /></div>
              <div><h3 className="display-sm" style={{ marginBottom: 8 }}>History</h3><FindingChips items={rep.history} /></div>
              <div><h3 className="display-sm" style={{ marginBottom: 8 }}>Lab values</h3><LabChips labs={rep.labs} /></div>
              {!p.report && <Alert tone="info">No report was uploaded for this patient. Only vitals fed the model.</Alert>}
            </div>
          </Card>
          <Card title="Fused patient record · vitals">
            <KeyValueList items={VITAL_ROWS.map(([k, label, unit]) => ({ label, value: `${p.vitals[k]}${unit}` }))} />
            <p className="tiny muted" style={{ marginTop: 12 }}>
              {Object.values(p.fused).filter(Boolean).length} non-zero inputs reached the model · processing {p.total_seconds}s
              {p.ocr_seconds ? ` (report reading ${p.ocr_seconds}s)` : ''}.
            </p>
          </Card>
        </div>

        <Card title="Why this priority">
          <p className="small muted" style={{ marginBottom: 14 }}>
            SHAP attribution for the model's choice of priority {p.model_priority}, strongest influence first.
          </p>
          <ShapBars items={p.shap} />
        </Card>

        <div className="fused-grid">
          <Card title="Model probabilities">
            <div className="stack" style={{ '--gap': '10px' }}>
              {probs.map(([k, v]) => (
                <div key={k} className="row" style={{ flexWrap: 'nowrap' }}>
                  <PriorityBlock p={Number(k)} />
                  <div className="conf-bar" style={{ flex: 1 }} role="meter" aria-valuenow={Math.round(v * 100)} aria-valuemin={0} aria-valuemax={100} aria-label={`Priority ${k} probability`}>
                    <i style={{ width: `${v * 100}%` }} />
                  </div>
                  <span className="mono small" style={{ width: 44, textAlign: 'right' }}>{fmtPct(v)}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card title="Clinician decisions">
            {p.overrides.length === 0 ? (
              <EmptyState title="No decision yet" action={<Button variant="primary" icon={PencilLine} onClick={openModal}>Accept or change</Button>}>
                Accept the model's priority or change it with a reason. Both are stored with the case.
              </EmptyState>
            ) : (
              <Timeline
                items={[...p.overrides].reverse().map((o) => ({
                  key: o.id,
                  tone: o.action === 'accept' ? 'ok' : undefined,
                  title: o.action === 'accept' ? `Accepted priority ${o.new_priority}` : `Changed ${o.old_priority} to ${o.new_priority}`,
                  meta: `${o.user_name} · ${fmtDateTime(o.created_at)}`,
                  body: o.reason || undefined,
                }))}
              />
            )}
          </Card>
        </div>
        <Link to="/app/queue" className="small mono" style={{ alignSelf: 'flex-start' }}>← Back to the queue</Link>
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Accept or change priority"
        footer={
          <>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="primary" icon={Check} loading={saving} onClick={save}>
              {Number(newP) === p.priority ? 'Accept priority' : 'Save change'}
            </Button>
          </>
        }
      >
        <form className="stack" onSubmit={save} noValidate>
          <Select
            label="Priority"
            value={newP}
            onChange={(e) => setNewP(e.target.value)}
            options={[1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: `${n} · ${PRIORITY_NAME[n]}${n === p.priority ? ' (current)' : ''}` }))}
          />
          <Textarea
            label="Reason"
            rows={3}
            hint={Number(newP) === p.priority ? 'Optional when you accept.' : 'Required when you change the priority.'}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            error={formErr || undefined}
          />
          <button type="submit" hidden />
        </form>
      </Modal>
    </>
  )
}
