import { Card, CardHeader, PageHeader, Timeline } from '../components/ui'
import { Disclaimer } from '../components/lab'
import { Stagger } from '../components/motion'

const STACK = [
  ['FastAPI + React', 'this interface and the thin API behind it (the original Streamlit app still runs)'],
  ['SQLite + SQLAlchemy', 'report, result and insight storage'],
  ['PyMuPDF', 'PDF text-layer extraction'],
  ['OpenCV + Tesseract OCR', 'scanned documents and photos of reports'],
  ['scikit-learn', 'fuzzy normalisation of test names (TF-IDF character n-grams)'],
  ['spaCy', 'optional patient-name extraction'],
  ['Recharts', 'trend and comparison charts'],
]

const LIMITS = [
  'OCR accuracy depends on scan or photo quality.',
  'Only lab report layouts with recognisable name / value / range rows are supported.',
  'This is not a diagnostic tool and does not replace professional medical advice.',
]

const PIPELINE = [
  { title: 'Upload', body: 'PDF, JPG, JPEG or PNG, up to 15 MB.' },
  { title: 'Text extraction', body: 'PDF text layer when present, otherwise OpenCV clean-up and Tesseract OCR.' },
  { title: 'Test-value extraction', body: 'Test name, value, unit and reference range are parsed from each row.' },
  { title: 'Classification', body: 'Each value is compared with its reference range: Low, Normal or High.' },
  { title: 'Insights', body: 'Abnormal results get a plain-language, non-diagnostic explanation.' },
]

export default function About() {
  return (
    <div className="container">
      <PageHeader title="About" description="An educational tool that extracts, organises and explains laboratory test results from uploaded reports." />
      <Stagger className="stack">
        <Card>
          <CardHeader title="AI-powered medical lab report analysis & health insights" subtitle="LabLens · Batch A8 · CSE" />
          <div className="card-body">
            <p className="muted" style={{ marginTop: 0 }}>
              Upload a laboratory report and LabLens turns complex medical information into structured results, trends across reports and explanations in everyday language. It never diagnoses a condition.
            </p>
            <Timeline items={PIPELINE.map((p) => ({ key: p.title, title: p.title, body: p.body }))} />
          </div>
        </Card>
        <div className="grid grid-2">
          <Card>
            <CardHeader title="Technology stack" />
            <div className="card-body">
              <ul className="about-list">
                {STACK.map(([k, v]) => (
                  <li key={k}>
                    <strong style={{ color: 'var(--text)' }}>{k}</strong> - {v}
                  </li>
                ))}
              </ul>
            </div>
          </Card>
          <Card>
            <CardHeader title="Limitations" />
            <div className="card-body">
              <ul className="about-list">
                {LIMITS.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </div>
          </Card>
        </div>
        <Disclaimer />
      </Stagger>
    </div>
  )
}
