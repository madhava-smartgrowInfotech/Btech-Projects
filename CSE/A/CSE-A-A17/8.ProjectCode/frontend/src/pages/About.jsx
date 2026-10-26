import { Check } from 'lucide-react'
import { Card, KeyValueList, PageHeader } from '../components/ui'
import { Container } from '../components/ui'

const TECHNIQUES = [
  'XGBoost regression for demand forecasting',
  'Chronological (time-aware) train/test splitting',
  'Lag and rolling-window features computed per product, leakage-free',
  'Domain adaptation via logistic-regression-based instance weighting',
  'Safe MAPE calculation (zero-demand-aware)',
]

const CHECKLIST = [
  'Daily demand aggregation only summarizes same-day transactions.',
  'Lag and rolling features use a shift before any rolling window.',
  'The train/test split is chronological, never random.',
  'Hyperparameter tuning uses TimeSeriesSplit.',
  'Target-domain test data is never used to train the source model.',
  'The domain-defining column is excluded from the model features so the domain classifier cannot trivially read the answer.',
]

export default function About() {
  return (
    <Container style={{ padding: '40px 16px 80px' }}>
      <PageHeader
        eyebrow="About project"
        title="Fashion demand forecasting"
        description="Fashion Demand Forecasting Using Machine Learning and Domain Adaptation. A final-year B.Tech project, batch CSE-A-A17."
      />
      <div className="page-stack">
        <Card title="Goal">
          <p style={{ maxWidth: '70ch' }}>
            Forecast fashion product demand using historical sales data, while demonstrating how a model trained on one domain, for example a sales
            channel, can be adapted to perform better on a different, related domain with a shifted data distribution.
          </p>
        </Card>
        <div className="two-col">
          <Card title="Techniques used">
            <ul className="stack" style={{ '--gap': '10px', paddingLeft: 20, margin: 0 }}>
              {TECHNIQUES.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </Card>
          <Card title="Data">
            <KeyValueList
              items={[
                { label: 'Dataset', value: 'H&M Personalized Fashion Recommendations (or any similar structure)' },
                { label: 'transactions', value: 't_dat, customer_id, article_id, price, sales_channel_id' },
                { label: 'articles', value: 'article_id, prod_name, product type, group, colour, department, section, garment group' },
                { label: 'customers', value: 'customer_id, age, club_member_status (optional)' },
              ]}
            />
          </Card>
        </div>
        <Card title="No-data-leakage checklist">
          <ul className="stack" style={{ '--gap': '10px', listStyle: 'none', padding: 0, margin: 0 }}>
            {CHECKLIST.map((c) => (
              <li key={c} className="row" style={{ '--gap': '10px', alignItems: 'flex-start', flexWrap: 'nowrap' }}>
                <span className="nav-done" aria-hidden="true" style={{ marginTop: 2 }}>
                  <Check size={12} strokeWidth={4} />
                </span>
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </Card>
        <p className="small muted" style={{ maxWidth: '70ch' }}>
          Built for academic demonstration. Model outputs, especially percentage improvements, reflect the actual experiment run on the uploaded data. No
          results are hard-coded or assumed.
        </p>
      </div>
    </Container>
  )
}
