import { useMemo, useState } from 'react'
import { CalendarClock, Info, LineChart, RefreshCw, Target, TrendingUp, Wallet } from 'lucide-react'
import { Button, Card, EmptyState, ErrorState, PageHeader, PageSkeleton, Segmented, StatCard, Table } from '../components/ui'
import { ForecastChart, ChartLegend } from '../components/charts'
import { ModeBadge, TickerTabs, TrendBadge, useTicker } from '../components/app/parts'
import { api } from '../lib/api'
import { useAsync, useRefresh } from '../lib/hooks'
import { buildSeries, companyOf } from '../lib/market'
import { dateLabel, fmtNum, fmtSigned, fmtUSD } from '../lib/format'

const HORIZONS = [
  { value: 'short', label: '5-day' },
  { value: 'long', label: '30-day' },
]
const RANGES = [
  { value: '60', label: '60 days' },
  { value: '120', label: '120 days' },
  { value: '250', label: '250 days' },
]

export default function Forecast() {
  const list = useAsync((signal) => api.tickers({ signal }), [])
  const names = useMemo(() => list.data?.tickers.map((t) => t.ticker) || [], [list.data])
  const [ticker, setTicker, params, setParams] = useTicker(names)
  const horizon = params.get('h') === 'long' ? 'long' : 'short'
  const [range, setRange] = useState('120')
  const setHorizon = (h) =>
    setParams((p) => {
      const n = new URLSearchParams(p)
      n.set('h', h)
      return n
    }, { replace: true })

  const view = useAsync(
    async (signal) => {
      if (!names.length) return null
      // Always fetch a year so the forecast cut-off date is inside the window; the range control only trims what is drawn.
      const [fc, hist] = await Promise.all([api.forecast(ticker, horizon, { signal }), api.history(ticker, 250, { signal })])
      return { fc, hist }
    },
    [ticker, horizon, names.length],
  )
  const refresh = useRefresh(view, `${ticker} forecast refreshed`)

  const model = useMemo(() => {
    if (!view.data) return null
    const { fc, hist } = view.data
    if (!hist.history.length) return { empty: true }
    const s = buildSeries(hist.history, fc.forecast, fc.last_close, Number(range))
    return { ...s, end: s.rows[s.rows.length - 1] }
  }, [view.data, range])

  const hLabel = horizon === 'short' ? '5-day' : '30-day'

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Forecast"
        icon={TrendingUp}
        title={`${ticker} ${hLabel} outlook`}
        lead="Actual closes, the model's dashed forecast and its shaded confidence band, on one chart."
        actions={
          <Button variant="secondary" icon={RefreshCw} loading={view.loading && !!view.data} onClick={refresh}>
            Refresh
          </Button>
        }
      />

      {list.error && <ErrorState title="Could not load the ticker list" error={list.error} onRetry={list.reload} />}
      {list.loading && !list.data && <PageSkeleton kpis={4} blocks={1} />}

      {names.length > 0 && (
        <>
          <div className="toolbar">
            <TickerTabs tickers={names} value={ticker} onChange={setTicker} />
            <Segmented name="horizon" label="Horizon" value={horizon} onChange={setHorizon} options={HORIZONS} />
            <Segmented name="range" label="History shown" value={range} onChange={setRange} options={RANGES} />
          </div>

          {view.loading && !view.data && <PageSkeleton kpis={4} blocks={1} />}
          {view.error && <ErrorState title={`Could not load the ${ticker} forecast`} error={view.error} onRetry={view.reload} />}

          {view.data && model?.empty && (
            <EmptyState icon={LineChart} title="No price history" message={`The API returned no price rows for ${ticker}.`} action={<Button onClick={view.reload} icon={RefreshCw}>Reload</Button>} />
          )}

          {view.data && model && !model.empty && (
            <div className="stack" style={{ '--gap': '22px', opacity: view.loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={view.loading}>
              <div className="grid-kpi">
                <StatCard
                  label="Close at forecast"
                  display={fmtUSD(view.data.fc.last_close)}
                  icon={Wallet}
                  tone="lavender"
                  foot={model.anchored ? `${dateLabel(model.cutoff, true)} · latest ${fmtUSD(model.latest.close)}` : `latest ${fmtUSD(model.latest.close)}`}
                />
                <StatCard
                  label={`Day ${model.end.day} forecast`}
                  display={fmtUSD(model.end.predicted_close)}
                  icon={Target}
                  tone="mint"
                  delta={{ value: model.end.change, text: fmtSigned(model.end.change), good: 'up' }}
                  foot={dateLabel(model.end.date, true)}
                />
                <StatCard label="Confidence band" display={`${fmtUSD(model.end.lower, 0)} – ${fmtUSD(model.end.upper, 0)}`} icon={CalendarClock} tone="sky" foot={`at day ${model.end.day}`} />
                <StatCard label="Trend" display={<TrendBadge trend={view.data.fc.trend} />} icon={TrendingUp} tone={view.data.fc.trend === 'up' ? 'mint' : 'rose'} foot={`${companyOf(ticker)} · 5-day outlook`} />
              </div>

              {model.stale && (
                <div className="note warn" role="note">
                  <Info size={18} aria-hidden="true" />
                  <span>
                    {model.anchored ? (
                      <>
                        The models were trained on prices up to <b>{dateLabel(model.cutoff, true)}</b> and forecast from there. Actual closes since then are
                        drawn as the solid line past the dotted marker, so you can see how the forecast held up. Retrain with <code>python -m backend.train</code>{' '}
                        to forecast from {dateLabel(model.latest.date, true)}.
                      </>
                    ) : (
                      <>
                        The forecast starts from a close of {fmtUSD(view.data.fc.last_close)}, which is not in the last year of live prices (latest{' '}
                        {fmtUSD(model.latest.close)}). The models were trained on older data, so retrain with <code>python -m backend.train</code>.
                      </>
                    )}
                  </span>
                </div>
              )}

              <Card
                title={`${ticker} price history and ${hLabel} forecast`}
                subtitle="Solid line is the actual close, dashed is the forecast, the shaded area is the confidence band."
                actions={<ModeBadge mode={view.data.hist.mode} />}
              >
                <div className="legend-row">
                  <ChartLegend
                    items={[
                      { label: 'Actual close', color: 'var(--text)' },
                      { label: 'Forecast', color: 'var(--lavender)' },
                      { label: 'Confidence band', color: 'var(--sky)' },
                    ]}
                  />
                </div>
                <ForecastChart
                  data={model.data}
                  splitAt={model.anchored ? model.cutoff : undefined}
                  valueFormat={(v) => fmtUSD(v)}
                  xFormat={(v, long) => dateLabel(v, long)}
                  label={`${ticker} closing price history with a ${hLabel} forecast and confidence band`}
                />
              </Card>

              <Card title={`${hLabel} forecast table`} subtitle="Predicted close and band for each trading day ahead, against the last close.">
                <Table
                  caption={`${ticker} ${hLabel} forecast`}
                  rows={model.rows}
                  rowKey={(r) => r.day}
                  pageSize={10}
                  cardTitle={(r) => `Day +${r.day} · ${dateLabel(r.date, true)}`}
                  columns={[
                    { key: 'day', label: 'Day', numeric: true, render: (r) => `+${r.day}` },
                    { key: 'date', label: 'Date', render: (r) => dateLabel(r.date, true) },
                    { key: 'predicted_close', label: 'Predicted close', numeric: true, render: (r) => fmtUSD(r.predicted_close) },
                    { key: 'lower', label: 'Lower', numeric: true, render: (r) => fmtUSD(r.lower) },
                    { key: 'upper', label: 'Upper', numeric: true, render: (r) => fmtUSD(r.upper) },
                    { key: 'width', label: 'Band width', numeric: true, sortValue: (r) => r.upper - r.lower, render: (r) => fmtNum(r.upper - r.lower) },
                    { key: 'actual', label: 'Actual close', numeric: true, sortValue: (r) => r.actual ?? -1, render: (r) => (r.actual == null ? 'not yet' : fmtUSD(r.actual)) },
                    { key: 'miss', label: 'Forecast miss', numeric: true, sortValue: (r) => r.miss ?? 0, render: (r) => (r.miss == null ? '–' : fmtSigned(r.miss)) },
                    { key: 'change', label: 'vs close at forecast', numeric: true, render: (r) => <span className={`chg ${r.change > 0 ? 'up' : r.change < 0 ? 'down' : ''}`}>{fmtSigned(r.change)}</span> },
                  ]}
                />
              </Card>
              <p className="disclaimer">Forecasts are statistical estimates for research and education, not financial advice.</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
