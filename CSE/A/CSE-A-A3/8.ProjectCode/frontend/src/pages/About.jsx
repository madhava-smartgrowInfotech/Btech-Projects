import { Link } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import { Button, Card, CardHeader, KeyValueList, PageHeader } from '../components/ui'

export default function About() {
  return (
    <div className="container">
      <PageHeader crumbs={[{ label: 'Insights' }, { label: 'About' }]} title="About this project" description="Intelligent Health Assistant - multi-disease prediction using machine learning." />
      <div className="stack">
        <div className="grid grid-2">
          <Card>
            <CardHeader title="What it does" />
            <div className="card-body prose">
              <p>
                Predicts the risk of <strong>diabetes, heart disease, liver disease and kidney disease</strong> from patient health parameters. Each disease is modelled with four
                algorithms - Logistic Regression, Decision Tree, Random Forest and SVM - and the best performer by F1-score is selected automatically for live predictions.
              </p>
              <p>Every prediction shows the risk class, the model's confidence, and the model and test accuracy that produced it.</p>
            </div>
          </Card>
          <Card>
            <CardHeader title="Tech stack" />
            <div className="card-body">
              <KeyValueList
                items={[
                  ['Models', 'scikit-learn (LR, DT, RF, SVM)'],
                  ['Data', 'pandas, numpy, joblib'],
                  ['Original UI', 'Flask + HTML/CSS (app.py)'],
                  ['API', 'FastAPI over the same trained models'],
                  ['Frontend', 'React, Vite, Recharts, three.js'],
                ]}
              />
            </div>
          </Card>
        </div>

        <Card pad spotlight={false} role="note">
          <div className="row" style={{ gap: 12, alignItems: 'flex-start' }}>
            <ShieldAlert size={22} aria-hidden="true" style={{ color: 'var(--warn)', flexShrink: 0, marginTop: 2 }} />
            <div className="prose">
              <h2 className="section-title" style={{ marginBottom: 8 }}>
                Medical disclaimer
              </h2>
              <p>
                This tool provides a machine-learning based risk estimate for educational and demonstration purposes only. It is not a substitute for professional medical diagnosis.
                Please consult a qualified healthcare provider for any medical concerns.
              </p>
              <p>The training data is synthetically generated, so results do not reflect real clinical populations.</p>
            </div>
          </div>
        </Card>

        <div className="row">
          <Button as={Link} to="/app/predict/diabetes" variant="primary">
            Make a prediction
          </Button>
          <Button as={Link} to="/app/models">
            See model scores
          </Button>
        </div>
      </div>
    </div>
  )
}
