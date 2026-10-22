import { Info, ShieldCheck } from 'lucide-react'
import { Card, PageHeader, Timeline } from '../components/ui'

const STEPS = [
  { title: 'Input & validation', meta: 'Your entries are validated on the server.', tone: 'lavender' },
  { title: 'Feature engineering', meta: 'Raw values become interpretable features: net investment position, age bands, education tiers, regional categories, employment stability.', tone: 'mint' },
  { title: 'Trained classifier', meta: 'Logistic Regression, Random Forest, Gradient Boosting and XGBoost are compared; the best by ROC-AUC serves predictions.', tone: 'peach' },
  { title: 'SHAP explanations', meta: 'Global importance plus live per-person contributors.', tone: 'sky' },
  { title: 'Forecasting', meta: 'A Holt-Winters projection of the Household Financial Conditions Index with intervals.', tone: 'rose' },
  { title: 'What-if', meta: 'Adjust key variables and compare modelled outcomes side by side.', tone: 'lavender' },
]

export default function About() {
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="About"
        icon={Info}
        title="About FinSight AI"
        lead="An AI-based financial identification and forecasting application for individuals. It analyses age, occupation, education, income signals, location and economic indicators to discover patterns, identify a financial profile, assess risk, forecast trends and explain its reasoning."
      />
      <div className="grid-2 wide-left">
        <Card hover={false} title="How it works">
          <Timeline items={STEPS} />
        </Card>
        <div className="stack">
          <Card hover={false} title="Technology">
            <p>Python · pandas · NumPy · scikit-learn · XGBoost · SHAP · statsmodels · Flask · joblib. The interface is React with Vite, Framer Motion and Recharts. Everything runs locally on an ordinary laptop; no GPU required.</p>
          </Card>
          <Card hover={false} tint="mint" title="Responsible use">
            <div className="stack" style={{ '--gap': '10px' }}>
              <p className="row" style={{ '--gap': '8px', flexWrap: 'nowrap', alignItems: 'flex-start' }}><ShieldCheck size={18} style={{ flex: 'none', marginTop: 3 }} aria-hidden="true" />FinSight AI provides informational estimates based on historical patterns. It does not provide professional financial advice and does not guarantee income, returns, credit or loan outcomes.</p>
              <p>SHAP values describe associations learned by the model, not causal effects. The model reflects biases present in 1990s census data, so treat results as patterns rather than judgements about individuals.</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
