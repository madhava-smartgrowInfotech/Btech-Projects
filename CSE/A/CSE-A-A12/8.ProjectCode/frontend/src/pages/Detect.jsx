import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ScanLine } from 'lucide-react'
import { Alert, Button, Card, FileDrop, PageHeader, ProgressBar, Stepper, useToast } from '../components/ui'
import { api } from '../lib/api'
import { useDocumentTitle, useHealth } from '../lib/hooks'

const ALLOWED = ['png', 'jpg', 'jpeg']
const PIPELINE = [
  'Image resizing and CLAHE contrast enhancement',
  'Normalization for the CNN input',
  'Deep learning classification (Normal / Bacterial / Viral)',
  'Grad-CAM heatmap of the affected lung regions',
  'Result saved to history for review',
]

export default function Detect() {
  useDocumentTitle('New scan')
  const nav = useNavigate()
  const toast = useToast()
  const health = useHealth()
  const maxMb = health?.max_upload_mb || 8
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [phase, setPhase] = useState('idle') // idle | uploading | analysing
  const [progress, setProgress] = useState(0)

  const pick = (f) => {
    setError('')
    if (!f) return setFile(null)
    const ext = f.name.includes('.') ? f.name.split('.').pop().toLowerCase() : ''
    if (!ALLOWED.includes(ext)) {
      setFile(null)
      return setError('Unsupported file type. Please upload a JPG or PNG image.')
    }
    if (f.size > maxMb * 1024 * 1024) {
      setFile(null)
      return setError(`File is too large (${(f.size / 1048576).toFixed(1)} MB). The limit is ${maxMb} MB.`)
    }
    setFile(f)
  }

  const analyse = async () => {
    if (!file) return setError('Please choose an X-ray image to upload.')
    setError('')
    setPhase('uploading')
    setProgress(0)
    try {
      const rec = await api.predict(file, (p) => {
        setProgress(p)
        if (p >= 1) setPhase('analysing')
      })
      toast.success(`Analysis complete: ${rec.prediction}.`)
      nav(`/app/result/${rec.id}`)
    } catch (e) {
      setPhase('idle')
      setError(e.status === 0 ? 'The API server is not reachable. Start it with run.bat, then try again.' : e.message)
    }
  }

  const busy = phase !== 'idle'
  return (
    <>
      <PageHeader
        eyebrow="New scan"
        title="Analyze an X-ray"
        description="Upload a chest X-ray to screen for Normal, Bacterial Pneumonia or Viral Pneumonia patterns."
      />

      {health?.demo_mode && (
        <div style={{ marginBottom: 24 }}>
          <Alert tone="warning">
            <strong>Demo mode.</strong> No trained weights were found at <code>saved_models/pneumonia_model.h5</code>, so predictions come from an untrained network. The
            full pipeline runs end to end, but the output is not diagnostically meaningful. Train with <code>python model/train.py --data_dir dataset</code>.
          </Alert>
        </div>
      )}

      <div className="grid grid-2" style={{ alignItems: 'start' }}>
        <Card title="1 · Choose the image">
          <div className="stack">
            {error && (
              <Alert tone="error">
                {error}
                <br />
                <span className="small">Pick a JPG or PNG under {maxMb} MB and try again.</span>
              </Alert>
            )}
            <FileDrop
              label="Drag and drop a chest X-ray here"
              hint={`JPG or PNG · up to ${maxMb} MB · or click to browse`}
              accept=".png,.jpg,.jpeg,image/png,image/jpeg"
              file={file}
              onFile={pick}
            />
            {busy && (
              <div className="stack" style={{ '--gap': '10px' }} aria-live="polite">
                <Stepper steps={['Upload', 'Analyse', 'Result']} current={phase === 'uploading' ? 0 : 1} label="Scan progress" />
                {phase === 'uploading' ? (
                  <ProgressBar value={progress} label="Upload progress" />
                ) : (
                  <p className="small">Preprocessing, classifying and building the Grad-CAM heatmap. The first scan after start-up can take a few seconds.</p>
                )}
              </div>
            )}
            <Button variant="primary" size="lg" icon={ScanLine} loading={busy} disabled={!file} onClick={analyse} block>
              {phase === 'analysing' ? 'Analyzing…' : phase === 'uploading' ? 'Uploading…' : 'Analyze X-ray'}
            </Button>
          </div>
        </Card>

        <Card title="How it works">
          <ol className="stack" style={{ margin: 0, paddingLeft: 22, '--gap': '10px' }}>
            {PIPELINE.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ol>
        </Card>
      </div>
    </>
  )
}
