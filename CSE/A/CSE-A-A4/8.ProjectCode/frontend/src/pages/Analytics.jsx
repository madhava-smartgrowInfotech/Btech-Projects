import { useState } from 'react'
import { BarChart3, Clock, CreditCard, MapPin, Wallet } from 'lucide-react'
import { api } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtInt, fmtPct, fmtUSD } from '../lib/format'
import { AreaTrend, BarCompare, ChartLegend, GroupedBars } from '../components/charts'
import { Card, KeyValueList, PageHeader, StatCard, Tabs } from '../components/ui'
import { SlideUp } from '../components/motion'
import Loadable from '../components/app/Loadable'
import { PASTEL } from '../lib/palette'

const TABS = [
  { id: 'where', label: 'Where', icon: MapPin },
  { id: 'when', label: 'When', icon: Clock },
  { id: 'amount', label: 'How much', icon: Wallet },
  { id: 'card', label: 'Card signals', icon: CreditCard },
]

const pctAxis = (v) => fmtPct(v, 0)
const hourLabel = (h) => `${String(h).padStart(2, '0')}:00`

function RateBars({ title, subtitle, rows, label }) {
  return (
    <Card title={title} subtitle={subtitle}>
      <BarCompare
        horizontal
        yWidth={104}
        height={Math.max(220, rows.length * 46)}
        name="Fraud rate"
        label={label}
        valueFormat={pctAxis}
        data={rows.map((m, i) => ({ name: m.name, value: m.rate, highlight: i === 0 }))}
      />
    </Card>
  )
}

export default function Analytics() {
  const state = useApi(api.datasetStats)
  const [tab, setTab] = useState('where')
  const s = state.data

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Insights"
        icon={BarChart3}
        title="Fraud analytics"
        lead="Where, when and how much: patterns in the full transaction dataset, not a sample."
      />
      <Loadable state={state} kpis={3} title="Analytics could not load">
        {s && (
          <>
            <div className="grid-kpi">
              <StatCard label="Transactions analysed" value={s.rows} format={fmtInt} tone="lavender" foot={`${fmtInt(s.fraud)} fraud · ${fmtInt(s.legit)} legitimate`} />
              <StatCard label="Typical fraud amount" display={fmtUSD(s.amount.fraud_median)} tone="rose" foot={`Median; legitimate is ${fmtUSD(s.amount.legit_median)}`} />
              <StatCard label="Riskiest category" display={s.by_merchant[0].name} tone="peach" foot={`${fmtPct(s.by_merchant[0].rate)} of its transactions are fraud`} />
            </div>
            <Tabs tabs={TABS} value={tab} onChange={setTab} label="Analytics views" name="analytics" />
            <SlideUp key={tab}>
              {tab === 'where' && (
                <div className="grid-2">
                  <RateBars title="Fraud rate by merchant category" subtitle="Highest first" rows={s.by_merchant} label="Fraud rate by merchant category" />
                  <RateBars title="Fraud rate by channel" subtitle="How the card was used" rows={s.by_channel} label="Fraud rate by channel" />
                </div>
              )}
              {tab === 'when' && (
                <Card title="Fraud rate by hour of day" subtitle="Hour taken from each transaction's timestamp (seconds modulo one day)">
                  <AreaTrend
                    data={s.by_hour.map((h) => ({ x: h.hour, y: h.rate }))}
                    name="Fraud rate"
                    label="Area chart of fraud rate by hour of day"
                    xFormat={hourLabel}
                    yFormat={pctAxis}
                    valueFormat={(v) => fmtPct(v)}
                  />
                  <p className="small muted" style={{ marginTop: 10 }}>A flat line means the hour of day carries little signal in this dataset.</p>
                </Card>
              )}
              {tab === 'amount' && (
                <div className="grid-2 wide-left">
                  <Card title="Amount distribution" subtitle="Transactions per amount band, split by label">
                    <GroupedBars
                      data={s.amount_buckets.map((b) => ({ x: b.name, legit: b.legit, fraud: b.fraud }))}
                      series={[
                        { key: 'legit', name: 'Legitimate', color: PASTEL[2] },
                        { key: 'fraud', name: 'Fraud', color: PASTEL[4] },
                      ]}
                      label="Grouped bars of transaction counts by amount band"
                      valueFormat={fmtInt}
                    />
                    <ChartLegend items={[{ label: 'Legitimate', color: PASTEL[2] }, { label: 'Fraud', color: PASTEL[4] }]} />
                  </Card>
                  <Card title="Amount summary">
                    <KeyValueList
                      items={[
                        ['Fraud, mean', fmtUSD(s.amount.fraud_mean)],
                        ['Fraud, median', fmtUSD(s.amount.fraud_median)],
                        ['Legitimate, mean', fmtUSD(s.amount.legit_mean)],
                        ['Legitimate, median', fmtUSD(s.amount.legit_median)],
                        ['Largest transaction', fmtUSD(s.amount.max)],
                      ]}
                    />
                  </Card>
                </div>
              )}
              {tab === 'card' && (
                <div className="grid-2">
                  <Card title="Card present" subtitle="Fraud rate when the physical card was or was not used">
                    <BarCompare
                      height={240}
                      name="Fraud rate"
                      label="Fraud rate by card presence"
                      valueFormat={pctAxis}
                      data={[
                        { name: 'Card present', value: s.card_present.present.rate },
                        { name: 'Card not present', value: s.card_present.not_present.rate, highlight: true },
                      ]}
                    />
                    <p className="small muted">{fmtInt(s.card_present.not_present.total)} transactions had no card present.</p>
                  </Card>
                  <Card title="Country match" subtitle="Fraud rate when the purchase country matches the card's">
                    <BarCompare
                      height={240}
                      name="Fraud rate"
                      label="Fraud rate by country match"
                      valueFormat={pctAxis}
                      data={[
                        { name: 'Country matches', value: s.country_match.match.rate },
                        { name: 'Country mismatch', value: s.country_match.mismatch.rate, highlight: true },
                      ]}
                    />
                    <p className="small muted">{fmtInt(s.country_match.mismatch.total)} transactions came from a different country.</p>
                  </Card>
                </div>
              )}
            </SlideUp>
          </>
        )}
      </Loadable>
    </div>
  )
}
