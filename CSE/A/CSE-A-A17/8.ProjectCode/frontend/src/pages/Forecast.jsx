import { useMemo, useState } from 'react'
import { Sparkles, TrendingUp } from 'lucide-react'
import { Button, Card, ErrorState, PageHeader, SearchField, Select, Skeleton, StatCard, Tabs } from '../components/ui'
import { ActionError, ChartCard, ForecastBlocks, Gate, RecordTable, useAction } from '../components/app/common'
import { useApi } from '../lib/useApi'
import { api } from '../lib/api'
import { fmtNum, fmtInt } from '../lib/format'
import { usePipeline } from '../lib/pipeline'

const HORIZONS = [
  { id: '7', label: '7 days' },
  { id: '14', label: '14 days' },
  { id: '30', label: '30 days' },
]
const MAX_OPTIONS = 300

export default function Forecast() {
  const { state } = usePipeline()
  const ready = Boolean(state?.xgboost_trained)
  const { data, error, loading, reload } = useApi('/api/forecast/articles', { enabled: ready })
  const { run, loading: running, error: runError } = useAction()
  const [query, setQuery] = useState('')
  const [article, setArticle] = useState('')
  const [horizon, setHorizon] = useState('7')
  const [result, setResult] = useState(null)

  const filtered = useMemo(() => {
    if (!data) return []
    const q = query.trim().toLowerCase()
    const list = q ? data.articles.filter((a) => String(a.id).includes(q) || a.label.toLowerCase().includes(q)) : data.articles
    return list
  }, [data, query])
  const shown = filtered.slice(0, MAX_OPTIONS)
  const selected = article || String(shown[0]?.id ?? '')

  const generate = async (e) => {
    e.preventDefault()
    if (!selected) return
    const out = await run(() => api('/api/forecast', { method: 'POST', body: { article_id: Number(selected), horizon: Number(horizon) } }), {
      success: 'Forecast generated.',
    })
    if (out) setResult(out)
  }

  const rows = useMemo(() => {
    if (!result) return []
    const hist = result.history.map((h) => ({ date: h.t_dat, history: h.demand, forecast: null }))
    const last = hist[hist.length - 1]
    // Join the dashed line to the solid one at the last real observation.
    if (last) last.forecast = last.history
    return [...hist, ...result.forecast.map((f) => ({ date: f.t_dat, history: null, forecast: Number(f.predicted_demand.toFixed(3)) }))]
  }, [result])

  const trend = result ? result.forecast[result.forecast.length - 1].predicted_demand - result.forecast[0].predicted_demand : 0

  return (
    <>
      <PageHeader
        eyebrow="08 · Demand forecast"
        title="Forecast"
        description="Pick a product and a horizon. Lag and rolling features roll forward on the model’s own predictions."
      />
      <Gate ok={ready} loading={!state} title="Train the XGBoost model first" to="/app/training" cta="Go to Model training">
        <div className="page-stack">
          {error ? (
            <ErrorState title="Could not load the product list" error={error} onRetry={reload} />
          ) : loading || !data ? (
            <Skeleton height={200} />
          ) : (
            <form onSubmit={generate} noValidate>
              <Card title="Forecast settings">
                <div className="grid grid-2">
                  <div className="stack">
                    <SearchField value={query} onChange={setQuery} label="Filter products" placeholder="Filter by article id or product type…" />
                    <Select
                      label={`Article (${fmtInt(filtered.length)} match${filtered.length === 1 ? '' : 'es'})`}
                      value={selected}
                      onChange={(e) => setArticle(e.target.value)}
                      hint={filtered.length > MAX_OPTIONS ? `Showing the first ${MAX_OPTIONS}. Filter to narrow the list.` : undefined}
                      options={shown.map((a) => ({ value: String(a.id), label: `${a.id}${a.label ? ` · ${a.label}` : ''} · ${fmtInt(a.units)} units` }))}
                    />
                    {!filtered.length && <span className="field-error">No product matches that filter.</span>}
                  </div>
                  <div>
                    <span className="field-label" id="hz">
                      Forecast horizon
                    </span>
                    <Tabs tabs={HORIZONS} value={horizon} onChange={setHorizon} label="Forecast horizon" />
                  </div>
                </div>
                <div className="stack" style={{ marginTop: 16 }}>
                  <ActionError error={runError} />
                  <div className="row">
                    <Button type="submit" variant="primary" size="lg" icon={TrendingUp} loading={running} disabled={!selected}>
                      Generate forecast
                    </Button>
                  </div>
                </div>
              </Card>
            </form>
          )}

          {running && !result && <Skeleton height={320} />}
          {result && (
            <section className="page-stack" aria-label={`Forecast for article ${result.article_id}`}>
              <div className="metric-grid">
                <StatCard label="Article" value={String(result.article_id)} hint={`${fmtInt(result.history_days)} days of history`} />
                <StatCard label={`Units, next ${result.horizon} days`} value={fmtNum(result.total, 1)} hint="Sum of predicted demand" />
                <StatCard label="Average per day" value={fmtNum(result.total / result.horizon, 2)} />
                <StatCard
                  label="Trend"
                  value={trend > 0 ? 'Up' : trend < 0 ? 'Down' : 'Flat'}
                  hint={`${fmtNum(result.forecast[0].predicted_demand, 2)} → ${fmtNum(result.forecast[result.forecast.length - 1].predicted_demand, 2)} per day`}
                />
              </div>
              <ChartCard
                title="History and forecast"
                height={320}
                summary={`Last 60 days of demand for article ${result.article_id} followed by a ${result.horizon} day forecast totalling ${fmtNum(result.total, 1)} units.`}
              >
                <ForecastBlocks rows={rows} />
              </ChartCard>
              <Card title="Forecast table">
                <RecordTable
                  columns={['t_dat', 'predicted_demand']}
                  rows={result.forecast}
                  pageSize={10}
                  caption="Predicted demand per day"
                  format={{ predicted_demand: (v) => v.toFixed(3) }}
                />
              </Card>
              {state?.gemini_configured && (
                <div className="row">
                  <Button to="/app/insights" icon={Sparkles}>
                    Summarize this forecast with AI
                  </Button>
                </div>
              )}
            </section>
          )}
        </div>
      </Gate>
    </>
  )
}
