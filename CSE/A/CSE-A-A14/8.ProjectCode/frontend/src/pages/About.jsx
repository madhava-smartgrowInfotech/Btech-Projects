import { BookOpen, BrainCircuit, Database, FlaskConical, Info, Lightbulb, LineChart, Lock, ShieldAlert, Sparkles, Target, UserSearch } from 'lucide-react'
import { PageHeader, Badge, Card, Timeline } from '../components/ui'
import { Callout } from '../components/app'
import { Reveal, Stagger } from '../components/motion'

const QUESTIONS = [
  ['WHO', 'is likely to churn?'],
  ['HOW LIKELY', 'are they to churn?'],
  ['WHY', 'are they likely to churn?'],
  ['WHAT ACTION', 'could be considered to keep them?'],
]

const PIPELINE = [
  { title: 'Customer data', meta: 'CSV upload or the built-in synthetic sample', icon: Database, tone: 'mint' },
  { title: 'Preprocessing and exploration', meta: 'Imputation, one-hot encoding, scaling, churn-by-attribute analysis', icon: Database, tone: 'sky' },
  { title: 'Class imbalance handling', meta: 'Class weights or SMOTE, applied to the training split only', icon: BrainCircuit, tone: 'lavender' },
  { title: 'Multiple ML models and comparison', meta: 'Accuracy, precision, recall, F1-score and ROC-AUC. Best model is not picked on accuracy alone', icon: LineChart, tone: 'peach' },
  { title: 'Churn probability and risk bands', meta: '0–100% mapped to Low, Medium, High and Critical with configurable thresholds', icon: ShieldAlert, tone: 'rose' },
  { title: 'Global and local explanations', meta: 'Built-in importance, permutation importance and SHAP with an automatic fallback', icon: Sparkles, tone: 'mint' },
  { title: 'Rule-based retention engine', meta: 'IF/THEN suggestions, fully local, never guarantees', icon: Lightbulb, tone: 'butter' },
  { title: 'What-if, Customer 360, batch and monitoring', meta: 'Scenario analysis, a single customer view, bulk scoring and a drift check', icon: FlaskConical, tone: 'sky' },
]

export default function About() {
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Help"
        icon={Info}
        title="About this project"
        lead="Explainable AI-Based Customer Churn Prediction and Intelligent Retention System, a B.Tech final-year major project that extends a traditional telecom churn predictor."
      />

      <Reveal>
        <Card title="The problem" subtitle="A basic churn model only says whether a customer may leave. An actionable system answers four questions.">
          <Stagger className="grid-kpi" inView>
            {QUESTIONS.map(([k, v], i) => (
              <Stagger.Item key={k}>
                <div className="card tint-lavender" style={{ boxShadow: 'none' }}>
                  <Target size={20} aria-hidden="true" />
                  <h3 style={{ marginTop: 8 }}>{k}</h3>
                  <p className="small muted">{v}</p>
                  <span className="tiny muted">Question {i + 1}</span>
                </div>
              </Stagger.Item>
            ))}
          </Stagger>
        </Card>
      </Reveal>

      <Reveal>
        <Card title="System architecture" subtitle="From raw customer data to a retention plan">
          <Timeline items={PIPELINE.map((p, i) => ({ id: i, ...p }))} />
        </Card>
      </Reveal>

      <div className="grid-2">
        <Reveal>
          <Card title="Technology stack">
            <div className="chip-list">
              {['Python', 'scikit-learn', 'pandas', 'imbalanced-learn', 'SHAP (optional)', 'joblib', 'FastAPI', 'React', 'Recharts', 'Framer Motion'].map((t) => (
                <span className="chip" key={t}>
                  {t}
                </span>
              ))}
            </div>
            <p className="small muted" style={{ marginTop: 12 }}>
              The original Streamlit app (<span className="code-pill">streamlit run app.py</span>) still works. This interface is a React front end on a thin FastAPI layer over the same Python modules.
            </p>
          </Card>
        </Reveal>
        <Reveal>
          <Card title="Explainable AI approach">
            <div className="stack" style={{ '--gap': '10px' }}>
              <p>
                <Badge tone="sky">Global</Badge> Built-in importance, permutation importance and mean |SHAP| show what generally influences churn predictions.
              </p>
              <p>
                <Badge tone="mint">Local</Badge> SHAP values (or a coefficient-based fallback) show why <em>this</em> customer received their score.
              </p>
            </div>
          </Card>
        </Reveal>
      </div>

      <Reveal>
        <div className="grid-2">
          <Card title="Risk scoring">
            <p>
              Churn probability maps to <strong>Low, Medium, High and Critical</strong> bands via thresholds you control on the Customer risk screen. They are application-defined, not universally valid probability cut-offs.
            </p>
          </Card>
          <Card title="What-if scenario analysis">
            <p>
              Change a customer’s attributes and see how the prediction moves. It is labelled <strong>model-based scenario analysis</strong>: it does not claim the change would cause the customer to stay.
            </p>
          </Card>
        </div>
      </Reveal>

      <Reveal>
        <Card title="Dataset">
          <p>
            Supports the classic Telco schema (customerID, gender, SeniorCitizen, Partner, Dependents, tenure, PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling, PaymentMethod, MonthlyCharges, TotalCharges, Churn) but is not hard-coded to it. Any CSV with a detectable churn column works; the sample dataset is synthetic and generated locally.
          </p>
        </Card>
      </Reveal>

      <Reveal>
        <div className="grid-2">
          <Card title="Base paper" actions={<BookOpen size={20} aria-hidden="true" />}>
            <p>
              <em>“Explaining Customer Churn Through Unified Perturbation-Based XAI Soft Computing,”</em> IEEE Access, 2026. DOI <span className="code-pill">10.1109/ACCESS.2026.3663648</span>.
            </p>
            <p className="small muted" style={{ marginTop: 10 }}>
              This application is an applied extension of the paper’s motivation, pairing churn prediction with individual-level explanation and actionable retention support. It does not claim to reproduce every algorithm or experiment from the paper.
            </p>
          </Card>
          <Card title="Security and privacy" actions={<Lock size={20} aria-hidden="true" />}>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              <li>No customer data is sent to any external API.</li>
              <li>No external AI or LLM service is used anywhere.</li>
              <li>Prediction, explanation and recommendation logic all run locally.</li>
            </ul>
          </Card>
        </div>
      </Reveal>

      <Reveal>
        <Card title="Future enhancements" actions={<UserSearch size={20} aria-hidden="true" />}>
          <div className="chip-list">
            {['Deep-learning churn models for comparison', 'Automated periodic retraining', 'Live CRM integration', 'Cohort-based campaign tracking', 'Multi-language recommendation text'].map((t) => (
              <span className="chip" key={t}>
                {t}
              </span>
            ))}
          </div>
        </Card>
      </Reveal>
      <Callout tone="info">Suggestions are always phrased as options to consider, never guarantees of a retention outcome.</Callout>
    </div>
  )
}
