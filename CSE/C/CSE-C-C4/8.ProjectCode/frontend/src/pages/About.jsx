import { useMemo } from 'react'
import { BrainCircuit, Database, Info, LineChart, Network, RefreshCw, Scale, ShieldAlert, Sigma, Waves } from 'lucide-react'
import { Badge, Button, Card, ErrorState, KeyValueList, PageHeader, PageSkeleton, Table, Timeline } from '../components/ui'
import { ModeBadge } from '../components/app/parts'
import { api } from '../lib/api'
import { useAsync, useRefresh } from '../lib/hooks'
import { companyOf } from '../lib/market'
import { fmtInt } from '../lib/format'

const PIPELINE = [
  { id: 'base', title: 'Classical baselines', icon: Sigma, tone: 'sky', meta: 'ARIMA(5,1,0), SARIMAX, Prophet, Random Forest (lag 20) and SVR on an 80/20 chronological split.' },
  { id: 'lstm', title: 'Core LSTM', icon: Waves, tone: 'lavender', meta: 'One LSTM(64) layer with BatchNorm, Dropout 0.2 and a Dense output over a 20-day window.' },
  { id: 'attn', title: 'Attention tier', icon: BrainCircuit, tone: 'mint', meta: 'LSTM with return sequences, 4-head MultiHeadAttention, residual connection, LayerNorm and pooling.' },
  { id: 'sent', title: 'Sentiment tier', icon: LineChart, tone: 'peach', meta: 'FinBERT-tone scores of financial headlines are aligned to trading dates and added as an input channel.' },
  { id: 'fed', title: 'Federated hybrid', icon: Network, tone: 'rose', meta: 'Each ticker trains locally and the weights are averaged with FedAvg (2 rounds of 3 local epochs).' },
]

export default function About() {
  const state = useAsync(async (signal) => {
    const [health, metrics] = await Promise.all([api.health({ signal }), api.metrics({ signal })])
    return { health, metrics }
  }, [])
  const refresh = useRefresh(state, 'Details refreshed')
  const { data, error, loading } = state

  const rows = useMemo(
    () =>
      data
        ? Object.entries(data.metrics)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([ticker, m]) => ({ ticker, company: companyOf(ticker), mode: m.mode, n_rows: m.n_rows, n_headlines: m.sentiment?.n_headlines, source: m.sentiment?.source }))
        : [],
    [data],
  )

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Method and data"
        icon={Info}
        title="How QuantPulse works"
        lead="The modelling stages, where each ticker's data comes from, and what the forecasts are and are not."
        actions={
          <Button variant="secondary" icon={RefreshCw} loading={loading && !!data} onClick={refresh}>
            Refresh
          </Button>
        }
      />

      {loading && !data && <PageSkeleton kpis={0} blocks={2} />}
      {error && <ErrorState title="Could not load the details" error={error} onRetry={state.reload} />}

      {data && (
        <>
          <div className="grid-2 wide-left">
            <Card title="Modelling pipeline" subtitle="Each stage is scored on the same held-out test set.">
              <Timeline items={PIPELINE} />
            </Card>
            <div className="stack" style={{ '--gap': '20px' }}>
              <Card title="This installation" subtitle="Read live from the API.">
                <KeyValueList
                  items={[
                    ['Models trained', data.health.trained ? 'Yes' : 'No'],
                    ['Tickers', fmtInt(data.health.tickers.length)],
                    ['News source', data.health.news_source === 'newsapi' ? 'NewsAPI (live)' : 'Built-in fallback'],
                    ['Sentiment scorer', Object.values(data.metrics)[0]?.sentiment?.scorer || '–'],
                    ['Window', '20 trading days'],
                    ['Horizons', '5 and 30 days'],
                  ]}
                />
              </Card>
              <Card tint="peach" hover={false}>
                <div className="row" style={{ flexWrap: 'nowrap', alignItems: 'flex-start' }}>
                  <ShieldAlert size={22} aria-hidden="true" style={{ flex: 'none', marginTop: 2 }} />
                  <div>
                    <h3>Research and education only</h3>
                    <p className="small" style={{ marginTop: 6 }}>
                      Forecasts are statistical estimates with wide uncertainty, not financial advice. A model that fits history well can still be wrong
                      tomorrow.
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          <Card
            title="Data behind each ticker"
            subtitle="Where each price series came from and how many headlines were scored."
            actions={<Badge tone="lavender" icon={Database}>{rows.length} tickers</Badge>}
          >
            <Table
              caption="Data source and size per ticker"
              rows={rows}
              rowKey={(r) => r.ticker}
              pageSize={10}
              searchKeys={['ticker', 'company', 'mode']}
              searchPlaceholder="Search ticker or company"
              initialSort={{ key: 'ticker', dir: 'asc' }}
              cardTitle={(r) => `${r.ticker} · ${r.company}`}
              columns={[
                { key: 'ticker', label: 'Ticker', render: (r) => <b>{r.ticker}</b> },
                { key: 'company', label: 'Company' },
                { key: 'mode', label: 'Price data', render: (r) => <ModeBadge mode={r.mode} /> },
                { key: 'n_rows', label: 'Price rows', numeric: true, render: (r) => fmtInt(r.n_rows) },
                { key: 'n_headlines', label: 'Headlines', numeric: true, render: (r) => fmtInt(r.n_headlines) },
                { key: 'source', label: 'News source', render: (r) => (r.source === 'newsapi' ? 'NewsAPI' : 'Built-in fallback') },
              ]}
            />
          </Card>
          <div className="note" role="note">
            <Scale size={18} aria-hidden="true" />
            <span>
              Price mode <b>live</b> means the series was pulled from Yahoo Finance, <b>csv</b> means the bundled snapshot was used, and <b>synthetic</b> means a
              clearly labelled stand-in series. The fallback news source uses synthetic headlines with the same schema, so the sentiment tier is only as informative as its headlines.
            </span>
          </div>
        </>
      )}
    </div>
  )
}
