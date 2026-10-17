import { Activity, Cpu, Database, FileSpreadsheet, ShieldAlert, ShieldCheck } from 'lucide-react'
import { api } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtInt, fmtPct, fmtPoints, fmtUSD } from '../lib/format'
import { MODE_CODE, MODE_LABEL } from '../lib/labels'
import { BarCompare } from '../components/charts'
import { Badge, Button, Card, KeyValueList, PageHeader, StatCard, Table } from '../components/ui'
import { SlideUp, Stagger } from '../components/motion'
import Loadable from '../components/app/Loadable'

const load = () => Promise.all([api.health(), api.datasetInfo(), api.datasetStats(), api.comparison()])

const COLUMNS = [
  { key: 'Amount', label: 'Amount', numeric: true, render: (r) => fmtUSD(r.Amount), sortValue: (r) => r.Amount },
  { key: 'Merchant_Category', label: 'Merchant' },
  { key: 'Transaction_Type', label: 'Channel', render: (r) => <Badge tone="neutral">{r.Transaction_Type}</Badge> },
  { key: 'Card_Present', label: 'Card present', render: (r) => (r.Card_Present ? 'Yes' : 'No') },
  { key: 'Country_Match', label: 'Country match', render: (r) => (r.Country_Match ? 'Yes' : 'No') },
  {
    key: 'Class',
    label: 'Label',
    render: (r) => (r.Class === 1 ? <Badge tone="rose" icon={ShieldAlert}>Fraud</Badge> : <Badge tone="mint" icon={ShieldCheck}>Legitimate</Badge>),
  },
]

export default function Dashboard() {
  const state = useApi(load)
  const [health, info, stats, comparison] = state.data || []

  let best = null
  if (comparison?.length) best = [...comparison].sort((a, b) => b['F1-Score'] - a['F1-Score'])[0]

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Overview"
        icon={Activity}
        title="Fraud screening dashboard"
        lead="A live look at the transaction dataset and the three trained models behind every verdict."
        actions={
          <>
            <Button to="/app/verify" icon={ShieldCheck}>Verify a transaction</Button>
            <Button to="/app/bulk" variant="secondary" icon={FileSpreadsheet}>Upload a CSV</Button>
          </>
        }
      />
      <Loadable state={state} title="The dashboard could not load">
        {state.data && (
          <>
            <Stagger className="grid-kpi">
              <Stagger.Item>
                <StatCard label="Transactions" value={info.rows} format={fmtInt} icon={Database} tone="lavender" foot={`${info.columns.length} columns per row`} />
              </Stagger.Item>
              <Stagger.Item>
                <StatCard
                  label="Fraud-labelled"
                  value={info.fraud_count}
                  format={fmtInt}
                  icon={ShieldAlert}
                  tone="rose"
                  foot={`${fmtPct(info.fraud_count / info.rows)} of the dataset`}
                />
              </Stagger.Item>
              <Stagger.Item>
                <StatCard
                  label="Best F1 score"
                  display={best ? fmtPoints(best['F1-Score']) : '–'}
                  icon={Activity}
                  tone="mint"
                  foot={best ? `${MODE_LABEL[best.mode]} · epoch ${best.best_epoch}` : 'No model trained yet'}
                />
              </Stagger.Item>
              <Stagger.Item>
                <StatCard label="Models loaded" display={`${health.models_trained.length} of 3`} icon={Cpu} tone="sky" foot={health.models_trained.map((m) => MODE_CODE[m]).join(' · ') || 'None'} />
              </Stagger.Item>
            </Stagger>

            <SlideUp>
              <div className="grid-2">
                <Card title="Fraud rate by merchant category" subtitle="Share of each category's transactions labelled fraud">
                  <BarCompare
                    horizontal
                    yWidth={100}
                    height={320}
                    name="Fraud rate"
                    label="Bar chart of fraud rate by merchant category"
                    valueFormat={(v) => fmtPct(v, 0)}
                    data={stats.by_merchant.map((m, i) => ({ name: m.name, value: m.rate, highlight: i === 0 }))}
                  />
                </Card>
                <Card title="Model F1 at best epoch" subtitle="Higher is better; each model is scored on its strongest epoch">
                  {comparison.length ? (
                    <BarCompare
                      height={320}
                      name="F1 score"
                      label="Bar chart of F1 score per model"
                      valueFormat={(v) => `${v}%`}
                      data={comparison.map((c) => ({ name: `${MODE_LABEL[c.mode]} (${c.Method})`, value: c['F1-Score'], highlight: c.mode === best?.mode }))}
                    />
                  ) : (
                    <p className="muted">No trained model yet. Train one in the Model lab.</p>
                  )}
                </Card>
              </div>
            </SlideUp>

            <SlideUp>
              <div className="grid-2 wide-left">
                <Card title="Sample transactions" subtitle="The first rows of the dataset with their ground-truth label">
                  <Table columns={COLUMNS} rows={info.head} pageSize={0} caption="Sample transactions" rowKey={(_, i) => i} cardTitle={(r) => fmtUSD(r.Amount)} />
                </Card>
                <Card title="What fraud looks like here" subtitle="Computed from the full dataset">
                  <KeyValueList
                    items={[
                      ['Average fraud amount', fmtUSD(stats.amount.fraud_mean)],
                      ['Average legitimate amount', fmtUSD(stats.amount.legit_mean)],
                      ['Fraud rate, card not present', fmtPct(stats.card_present.not_present.rate)],
                      ['Fraud rate, card present', fmtPct(stats.card_present.present.rate)],
                      ['Fraud rate, country mismatch', fmtPct(stats.country_match.mismatch.rate)],
                      ['Fraud rate, country match', fmtPct(stats.country_match.match.rate)],
                    ]}
                  />
                </Card>
              </div>
            </SlideUp>
          </>
        )}
      </Loadable>
    </div>
  )
}
