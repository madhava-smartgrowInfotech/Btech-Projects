import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ScanLine, UserPlus } from 'lucide-react'
import api from '../api.js'
import { PageHeader } from '../components/ui/Layout.jsx'
import { Alert, Button, Card, EmptyState, ErrorState, Field, FileDrop, SkeletonBlock } from '../components/ui/index.js'
// Field is used for the patient picker below
import { useToast } from '../components/ui/Toast.jsx'
import PatientForm from '../components/PatientForm.jsx'
import { failure } from '../lib/product.js'

const ACCEPT = '.png,.jpg,.jpeg,.dcm,.dicom'

// Explains what to do next for each way an upload can fail (the API's own message is shown above it).
function uploadHint(status) {
  if (status === 422) return 'Upload a grayscale chest X-ray or chest CT slice. Colour photos and non-chest images are rejected on purpose.'
  if (status === 413) return 'Choose a file smaller than 25 MB and try again.'
  if (status === 404) return 'The patient could not be found. Pick the patient again from the list.'
  return 'The analysis service did not finish. Check the API window that run.bat opened, then try again. Your file has not been saved.'
}

export default function NewScan() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const toast = useToast()
  const nameRef = useRef(null)
  const [patients, setPatients] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [patientId, setPatientId] = useState(params.get('patient') || '')
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    setLoadError(null)
    setPatients(null)
    api
      .get('/patients')
      .then((r) => setPatients(r.data))
      .catch(async (e) => setLoadError(await failure(e)))
  }
  useEffect(load, [])

  const pick = (f) => {
    setFile(f)
    setError(null)
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!patientId || !file) return
    setBusy(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append('patient_id', patientId)
      fd.append('file', file)
      const { data } = await api.post('/scans', fd)
      toast.success(`Scan #${data.id} analysed.`)
      nav(`/scans/${data.id}`)
    } catch (err) {
      const f = await failure(err)
      setError({ ...f, hint: uploadHint(f.status) })
    } finally {
      setBusy(false)
    }
  }

  const addPatient = (p) => {
    setPatients((list) => [p, ...(list || [])])
    setPatientId(String(p.id))
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Screening"
        title="New scan"
        description="A chest X-ray or chest CT slice (PNG, JPG or DICOM, up to 25 MB). The file is checked, segmented and classified in one step."
      />

      <div className="split">
        <Card as="form" onSubmit={submit} title="1 · Patient and scan">
          <div className="page" style={{ gap: 20 }}>
            {loadError && <ErrorState title="Patients could not be loaded" error={loadError.message} hint="Check that the API is running, then retry." onRetry={load} />}
            {!loadError && !patients && <SkeletonBlock rows={2} label="Loading patients" />}
            {!loadError && patients && patients.length === 0 && (
              <EmptyState
                icon={UserPlus}
                title="No patients yet"
                action={
                  <Button variant="primary" icon={UserPlus} onClick={() => nameRef.current?.focus()}>
                    Register a patient
                  </Button>
                }
              >
                A scan belongs to a patient. Register one first, using the form beside this one.
              </EmptyState>
            )}
            {!loadError && patients && patients.length > 0 && (
              <Field label="Patient" htmlFor="scan-patient" hint="Scans are saved to this patient's record.">
                <div className="select-wrap">
                  <select id="scan-patient" className="select" value={patientId} onChange={(e) => setPatientId(e.target.value)} required>
                    <option value="">Select a patient…</option>
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.code} · {p.name} ({p.age}, {p.sex})
                      </option>
                    ))}
                  </select>
                </div>
              </Field>
            )}

            <div className="field">
              <span className="field-label">Scan file</span>
              <FileDrop label="Drop a chest scan here" hint="PNG, JPG or DICOM (.dcm) · or click to browse" accept={ACCEPT} file={file} onFile={pick} />
            </div>

            {error && (
              <Alert tone="error" action={null}>
                <span>
                  <strong style={{ display: 'block' }}>The scan was not analysed.</strong>
                  {error.message} {error.hint}
                </span>
              </Alert>
            )}
            {busy && (
              <Alert tone="info">Analysing: modality check, preprocessing, lung mask, classification and Grad-CAM. On a CPU this can take a minute.</Alert>
            )}

            <Button type="submit" variant="primary" size="lg" icon={ScanLine} loading={busy} block disabled={!patientId || !file}>
              {busy ? 'Analysing…' : 'Analyse scan'}
            </Button>
          </div>
        </Card>

        <Card title="2 · Register a patient">
          <PatientForm nameRef={nameRef} idPrefix="scan-patient-new" onCreated={addPatient} />
          <p className="tiny muted" style={{ marginTop: 14 }}>Names and phone numbers are stored encrypted.</p>
        </Card>
      </div>
    </div>
  )
}
