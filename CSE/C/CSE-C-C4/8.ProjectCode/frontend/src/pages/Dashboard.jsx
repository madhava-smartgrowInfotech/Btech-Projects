import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, LineChart, RefreshCw, Sigma, TrendingUp, Trophy } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, PageSkeleton, Sparkline, StatCard, Table } from '../components/ui'
import { Stagger } from '../components/motion'
import { ModeBadge, TrendBadge } from '../components/app/parts'
import { api } from '../lib/api'
import { useAsync, useRefresh } from '../lib/hooks'
import { allModels, bestBy, companyOf, forecastMove, modelLabel } from '../lib/market'
import { fmtNum, fmtSigned, fmtUSD } from '../lib/format'

export default function Dashboard() {
  const state = useAsync(async (signal) => {
    const [tickers, metrics] = await Promise.all([api.tickers({ signal }), api.metrics({ signal })])
    return { tickers: tickers.tickers, metrics }
  }, [])
  const refresh = useRefresh(state, 'Dashboard refreshed')
  const { data, error, loading } = state

  const rows = useMemo(() => {
    if (!data) return []
    return data.tickers.map((t) => {
      const m = data.metrics[t.ticker]
      const best = bestBy(allModels(m), 'mae')
      return {
        ticker: t.ticker,
        company: companyOf(t.ticker),
        last_close: t.last_close,
        trend: t.trend,
        mode: t.mode,
        move5: forecastMove(m, 'forecast_short'),
        move30: forecastMove(m, 'forecast_long'),
        best,
        spark: m?.forecast_short ? [t.last_close, ...m.forecast_short.map((f) => f.predicted_close)] : [],
      }
    })
  }, [data])

  const summary = useMemo(() => {
    if (!rows.length) return null
    const wins = {}
    rows.forEach((r) => r.best && (wins[r.best.key] = (wins[r.best.key] || 0) + 1))
    const top = Object.entries(wins).sort((a, b) => b[1] - a[1])[0]
    const moves = rows.map((r) => r.move5).filter((v) => v != null)
    return {
      up: rows.filter((r) => r.trend === 'up').length,
      top: top ? { key: top[0], wins: top[1] } : null,
      avgMove: moves.length ? moves.reduce((a, b) => a + b, 0) / moves.length : null,
    }
  }, [rows])

  const actions = (
    <Button variant="secondary" icon={RefreshCw} loading={loading && !!data} onClick={refresh}>
      Refresh
    </Button>
  )

  return (
    <div className="stack" style={{ '--gap': '26px' }}>
      <PageHeader
        eyebrow="Market pulse"
        icon={LineChart}
        title="Your forecast universe"
        lead="Every ticker QuantPulse has trained models for, with the close the models forecast from, its trend and the 5- and 30-day outlook."
        actions={actions}
      />

      {loading && !data && <PageSkeleton kpis={4} blocks={2} />}
      {error && <ErrorState title="Could not load the dashboard" error={error} onRetry={state.reload} />}

      {data && rows.length === 0 && (
        <EmptyState
          icon={LineChart}
          title="No tickers yet"
          message="The API is running but no ticker has trained models. Train the pipeline, then reload."
          action={<Button onClick={state.reload} icon={RefreshCw}>Reload</Button>}
        />
      )}

      {data && summary && (
        <>
          <div className="grid-kpi">
            <StatCard label="Tickers covered" value={rows.length} icon={Sigma} tone="lavender" foot="models trained for each" />
            <StatCard label="Trending up" display={`${summary.up} of ${rows.length}`} icon={TrendingUp} tone="mint" foot="5-day directional outlook" />
            <StatCard
              label="Most accurate model"
              display={summary.top ? modelLabel(summary.top.key) : '–'}
              icon={Trophy}
              tone="peach"
              foot={summary.top ? `lowest test MAE on ${summary.top.wins} of ${rows.length} tickers` : undefined}
            />
            <StatCard
              label="Average 5-day move"
              display={fmtSigned(summary.avgMove)}
              icon={LineChart}
              tone="sky"
              foot="forecast vs last close, all tickers"
            />
          </div>

          <section aria-labelledby="universe-h" className="stack" style={{ '--gap': '14px' }}>
            <h2 id="universe-h">Tickers</h2>
            <Stagger className="ticker-grid">
              {rows.map((r) => (
                <Stagger.Item key={r.ticker}>
                  <Link to={`/app/forecast?t=${r.ticker}`} className="ticker-link" aria-label={`${r.ticker}, ${r.company}: open forecast`}>
                    <Card className="ticker-card">
                      <div className="row between" style={{ flexWrap: 'nowrap' }}>
                        <div>
                          <div className="sym">{r.ticker}</div>
                          <div className="co">{r.company}</div>
                        </div>
                        <TrendBadge trend={r.trend} />
                      </div>
                      <div className="px">{fmtUSD(r.last_close)}</div>
                      <div className="small muted">
                        5-day outlook{' '}
                        <span className={`chg ${r.move5 > 0 ? 'up' : r.move5 < 0 ? 'down' : ''}`}>{fmtSigned(r.move5)}</span>
                      </div>
                      <Sparkline data={r.spark} color={r.trend === 'up' ? 'var(--mint)' : 'var(--rose)'} className="spark" />
                      <div className="row between small muted" style={{ flexWrap: 'nowrap' }}>
                        <ModeBadge mode={r.mode} />
                        <span className="row" style={{ '--gap': '4px', flexWrap: 'nowrap' }}>
                          Forecast <ArrowRight size={14} aria-hidden="true" />
                        </span>
                      </div>
                    </Card>
                  </Link>
                </Stagger.Item>
              ))}
            </Stagger>
          </section>

          <Card title="Universe at a glance" subtitle="Sort any column, or search by symbol or company.">
            <Table
              caption="All tickers with price, outlook and best model"
              rows={rows}
              rowKey={(r) => r.ticker}
              pageSize={10}
              searchKeys={['ticker', 'company']}
              searchPlaceholder="Search ticker or company"
              initialSort={{ key: 'ticker', dir: 'asc' }}
              cardTitle={(r) => `${r.ticker} · ${r.company}`}
              columns={[
                { key: 'ticker', label: 'Ticker', render: (r) => <Link to={`/app/forecast?t=${r.ticker}`}><b>{r.ticker}</b></Link> },
                { key: 'company', label: 'Company' },
                { key: 'last_close', label: 'Close at forecast', numeric: true, render: (r) => fmtUSD(r.last_close) },
                { key: 'trend', label: 'Trend', render: (r) => <TrendBadge trend={r.trend} /> },
                { key: 'move5', label: '5-day', numeric: true, render: (r) => fmtSigned(r.move5) },
                { key: 'move30', label: '30-day', numeric: true, render: (r) => fmtSigned(r.move30) },
                { key: 'best', label: 'Best model', sortValue: (r) => r.best?.label || '', render: (r) => (r.best ? <Badge tone="lavender">{r.best.label}</Badge> : '–') },
                { key: 'mae', label: 'Best MAE', numeric: true, sortValue: (r) => r.best?.mae ?? 0, render: (r) => fmtNum(r.best?.mae) },
              ]}
            />
          </Card>
          <p className="disclaimer">QuantPulse is a research and education tool. Forecasts are statistical estimates, not financial advice.</p>
        </>
      )}
    </div>
  )
}
