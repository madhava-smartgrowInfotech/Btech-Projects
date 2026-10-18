import { Alert, Card, KeyValueList, PageHeader, Timeline } from '../components/ui'
import { useDocumentTitle, useHealth } from '../lib/hooks'

const PIPELINE = [
  'Image upload via web interface',
  'Preprocessing: resize (224×224), CLAHE contrast enhancement, normalization',
  'Data augmentation during training (rotation, zoom, shift, flip)',
  'CNN-based feature extraction and 3-class classification',
  'Grad-CAM heatmap generation for explainability',
  'Result storage and history tracking (SQLite)',
]

export default function About() {
  useDocumentTitle('About')
  const health = useHealth()
  return (
    <>
      <PageHeader eyebrow="Project" title="About this project" description="Pneumonia Detection Using Deep Learning." />

      <div className="stack" style={{ '--gap': '24px' }}>
        <Card title="Abstract">
          <p style={{ maxWidth: '78ch' }}>
            Pneumonia remains one of the leading causes of illness and death worldwide, especially among children and elderly patients. Manual diagnosis from chest
            X-ray images depends on radiologist availability and can be time-consuming. This system applies image preprocessing, CNN-based deep learning, and
            classification techniques to classify chest X-ray images into Normal, Bacterial Pneumonia, or Viral Pneumonia categories, and generates heatmap-based visual
            explanations to highlight affected lung regions for clinical decision support.
          </p>
        </Card>

        <div className="grid grid-2">
          <Card title="Proposed system pipeline">
            <Timeline items={PIPELINE.map((title) => ({ title }))} />
          </Card>

          <div className="stack">
            <Card title="Technology stack">
              <div className="grid grid-2" style={{ '--gap': '16px' }}>
                <div>
                  <strong>Front end</strong>
                  <ul>
                    <li>React + Vite</li>
                    <li>Framer Motion, GSAP, Recharts</li>
                    <li>Neo Brutal Grid design kit</li>
                  </ul>
                </div>
                <div>
                  <strong>Back end</strong>
                  <ul>
                    <li>Python, FastAPI (API), Flask (original UI)</li>
                    <li>OpenCV</li>
                    <li>TensorFlow / Keras</li>
                    <li>SQLite</li>
                  </ul>
                </div>
              </div>
            </Card>

            <Card title="Live system status">
              {health ? (
                <KeyValueList
                  items={[
                    { label: 'API', value: health.status },
                    { label: 'Model', value: !health.model_ready ? 'Loading…' : health.demo_mode ? 'Demo (untrained)' : 'Trained' },
                    { label: 'Classes', value: health.classes.join(', ') },
                    { label: 'Upload', value: `${health.allowed_types.join(', ').toUpperCase()} · up to ${health.max_upload_mb} MB` },
                  ]}
                />
              ) : (
                <p className="muted">The API is not responding. Start it with run.bat.</p>
              )}
            </Card>
          </div>
        </div>

        <Alert tone="info">
          <strong>Disclaimer:</strong> This is an academic / research prototype for computer-aided screening support. It is not a certified medical device and must not
          be used as the sole basis for clinical diagnosis or treatment decisions.
        </Alert>
      </div>
    </>
  )
}
